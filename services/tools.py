from youtube_transcript_api import YouTubeTranscriptApi
import youtube_transcript_api
import os
import re
from googleapiclient.discovery import build
import tiktoken

def youtube_search(query: str) -> list[dict]:
    """
    Search youtube for videos based on a query and returns a list of dictionaries 
    with 10 video information so the user can select which to transcribe
    """
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
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
        
        # Process all videos in the response
        for video in response['items']:
            video_id = video['id']['videoId']
            
            # Get additional video details
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


def get_transcript_from_url(youtube_url: str) -> str:
    """
    Fetch transcript for a youtube video using the youtube url and returns the transcript as a string
    """
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", youtube_url)
    try:
        if match:
            video_id = match.group(1)
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = " ".join([entry["text"] for entry in transcript_list])
            return transcript
        else:
            raise ValueError("Invalid YouTube URL")
    except youtube_transcript_api._errors.TranscriptsDisabled:
        return "Could not retrieve transcript for this video"
    except youtube_transcript_api._errors.VideoUnavailable:
        return "Video is no longer available on youtube"

    

def count_tokens(text: str, model: str) -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
    

tools = [
    {
        "type": "function",
        "function": {
            "name": "youtube_search",
            "description": """Search youtube for videos based on a query and returns a dictionary 
                                with 10 video title and video url so the user can select which to transcribe""",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The query to search for could be the title of the video or the description of the video"
                    }
                },
                "required": ["query"]
            }
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transcript_from_url",
            "description": "Fetch transcript for a youtube video using the youtube url and returns the transcript as a string",
            "parameters": {
                "type": "object",
                "properties": {
                    "youtube_url": {
                        "type": "string",
                        "description": "The url of the youtube video"
                    }
                },
                "required": ["youtube_url"]
            }
        },
    }
]