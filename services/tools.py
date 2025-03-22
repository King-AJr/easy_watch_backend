import requests
import os
import re
from pytubefix import YouTube
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

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


def get_transcript_from_url(youtube_url: str) -> any:
    """
    Fetch transcript for a youtube video using the youtube url and returns the transcript as a string
    """

    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", youtube_url)

    api_key= os.getenv("YOUTUBE_TRANSCRIPT_IO_API_TOKEN")
    if match:
        video_id = match.group(1)
            
        headers = {
            "Authorization": f"Basic {api_key}",
            "Content-Type": "application/json"
        }
            
        payload = {"ids": [video_id]}

        yt = YouTube(youtube_url)
            
        response = requests.post("https://www.youtube-transcript.io/api/transcripts", headers=headers, json=payload)

        data = response.json()

        transcript_segments = data[0]["tracks"][0]['transcript']

        transcript = " ".join(segment["text"] for segment in transcript_segments)
            
        return {
            "transcript": transcript,
            "title": yt.title,
            "description": yt.description,
            "video_metadata": yt.metadata
        }
    

