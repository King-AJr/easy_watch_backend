import os
import json
import subprocess
import yt_dlp
from groq import Groq
from typing import Optional, Dict
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from youtube_transcript_api.proxies import WebshareProxyConfig
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')

ytt_api = YouTubeTranscriptApi(
    proxy_config=WebshareProxyConfig(
        proxy_username=os.environ.get('PROXY_USERNAME'),
        proxy_password=os.environ.get('PROXY_PASSWORD'),
    )
)

def search_video(query: str) -> Optional[Dict]:
    """
    Search for a YouTube video and return its metadata
    """
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

        request = youtube.search().list(
            part="snippet",
            maxResults=10,
            q=query,
            type="video"
        )
        response = request.execute()

        if not response['items']:
            return None

        results = []
        
        for video in response['items']:
            video_id = video['id']['videoId']
            
            video_request = youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            video_response = video_request.execute()
            
            if video_response['items']:
                video_details = video_response['items'][0]
                
                results.append({
                    'video_id': video_id,
                    'title': video_details['snippet']['title'],
                    'description': video_details['snippet']['description'],
                    'channel': video_details['snippet']['channelTitle'],
                    'views': video_details['statistics'].get('viewCount', '0'),
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'thumbnail': video_details['snippet']['thumbnails']['high']['url']
                })
        
        return results
    except Exception as e:
        raise Exception(f"Error searching YouTube video: {str(e)}")
    

def download_audio_to_memory(video_id):
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = ['yt-dlp', '-f', 'bestaudio/best', '-o', '-', youtube_url]
    audio_bytes = subprocess.check_output(cmd)
    return audio_bytes

def transcribe_audio_groq_memory(video_id, prompt="""
        You are a skilled video content analyzer. Create a comprehensive summary of the video
        based on its transcript. Include:
        1. Main topics and key points
        2. Important details and insights
        3. Key takeaways
        Format the summary in a clear, easy-to-read structure.
        """,
        language="en",
        model="whisper-large-v3-turbo", temperature=0.0):

    audio_bytes = download_audio_to_memory(video_id)
    
    transcription = client.audio.transcriptions.create(
        file=("audio.mp3", audio_bytes),
        model=model,
        prompt=prompt,
        language=language,
        response_format="json",
        temperature=temperature
    )
    return transcription.text

def get_video_transcript(video_id: str):
    """
    Get the transcript of a YouTube video
    """
    try:
        transcript_list = ytt_api.get_transcript(video_id)
        transcript_text = ' '.join([entry['text'] for entry in transcript_list])
        return transcript_text

    except NoTranscriptFound:
        transcription_text = transcribe_audio_groq_memory(video_id, language="en")
        return transcription_text
    except Exception as e:
        raise Exception(f"Error getting video transcript: {str(e)}")
    

def select_video(results: list[Dict], selection_index: int = None) -> Optional[Dict]:
        """
        Allow the user to select a video from the search results
        """
        if not results:
            return None
        
        if selection_index is not None:
            if 0 <= selection_index < len(results):
                return results[selection_index]
            else:
                raise ValueError(f"Selection index {selection_index} is out of range (0-{len(results)-1})")
        
        print("Found the following videos:")
        for i, video in enumerate(results):
            print(f"{i+1}. {video['title']} by {video['channel']} ({video['views']} views)")
            print(f"   {video['url']}")
            print(f"   {video['description'][:100]}{'...' if len(video['description']) > 100 else ''}")
            print()
        
        while True:
            try:
                choice = int(input(f"Select a video (1-{len(results)}): "))
                if 1 <= choice <= len(results):
                    return results[choice-1]
                else:
                    print(f"Please enter a number between 1 and {len(results)}")
            except ValueError:
                print("Please enter a valid number")
            except KeyboardInterrupt:
                return None
            
tools =[
    {
        "type": "function",
        "function": {
            "name": "search_video",
            "description": "Use it to search up movies, videos and clips",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Query to be searched up on YouTube",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_video_transcript",
            "description": "Retrieves video_id, transcribes and summarizes information about the video",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_id": {
                        "type": "string",
                        "description": "Video to be summarized",
                    }
                },
                "required": ["video_id"],
            },
        },
    }
]

messages = [
    {

        "role": "system",
        "content": """
        You are a skilled video content analyzer. Create a comprehensive summary of the video
        based on its transcript. Include:
        1. Main topics and key points
        2. Important details and insights
        3. Key takeaways
        Format the summary in a clear, easy-to-read structure.
        """
    },
    {
        "role": "user",
        "content":"{query}"
    }
]

response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Using Llama 3.3 70B versatile model,
            messages=messages,
            tools=tools,
            tool_choice='auto',
            temperature=0.7,
            max_tokens=1000
        )

response_message = response.choices[0].message
tool_calls = response_message.tool_calls
print(f"Initial Response: \n{response.choices[0].message}\n\n")

if tool_calls:
    available_funtions = {
        "search_video": search_video,
        "get_video_transcript":get_video_transcript
    }
    messages.append(response_message)

    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_funtions.get(function_name, None)
        funtion_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(**funtion_args)
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role":"tool",
                "name": function_name,
                "content": str(function_response)
            }
        )

        second_response = client.chat.completions.create(
            model="llama-3.3-versatile",
            messages=messages
        )
        response = second_response

print(f"Final Response: {response.choices[0].message.content}\n\n")