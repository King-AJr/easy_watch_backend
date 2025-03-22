import requests
import os
import re
from pytubefix import YouTube
from googleapiclient.discovery import build
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor


load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def youtube_search(query: str) -> list[dict]:
    """
    Search youtube for videos based on a query and returns a list of dictionaries 
    with 10 video information so the user can select which to transcribe
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


def get_transcript_from_url(youtube_url: str) -> dict:
    """
    Fetch transcript for a YouTube video using the video URL and return its transcript along with metadata.
    """
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", youtube_url)
    if not match:
        return {}
    
    video_id = match.group(1)
    transcript_api_key = os.getenv("YOUTUBE_TRANSCRIPT_IO_API_TOKEN")
    youtube_api_key = os.getenv("YOUTUBE_API_KEY")
    
    headers = {
        "Authorization": f"Basic {transcript_api_key}",
        "Content-Type": "application/json"
    }
    payload = {"ids": [video_id]}
    
    transcript_url = "https://www.youtube-transcript.io/api/transcripts"
    details_url = (
        f"https://www.googleapis.com/youtube/v3/videos?"
        f"id={video_id}&key={youtube_api_key}&part=snippet,contentDetails,statistics"
    )
    
    # Run both API calls concurrently using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_transcript = executor.submit(requests.post, transcript_url, headers=headers, json=payload)
        future_details = executor.submit(requests.get, details_url)
        
        transcript_response = future_transcript.result()
        details_response = future_details.result()
    
    # Process video details
    data = details_response.json()
    if data['items']:
        video = data['items'][0]
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        statistics = video.get('statistics', {})
        
        title = snippet.get('title', '')
        description = snippet.get('description', '')
        # You can extract additional metadata if needed:
        published_at = snippet.get('publishedAt', '')
        duration = content_details.get('duration', '')
        view_count = statistics.get('viewCount', 'N/A')
    else:
        title = description = published_at = duration = view_count = ""
    
    # Process transcript data
    transcript_data = transcript_response.json()
    # Assumes transcript_data is a list with at least one item containing a 'tracks' key.
    transcript_segments = transcript_data[0]["tracks"][0]['transcript']
    transcript_text = " ".join(segment["text"] for segment in transcript_segments)
    
    return {
        "transcript": transcript_text,
        "title": title,
        "description": description,
        "published_at": published_at,
        "duration": duration,
        "view_count": view_count
    }
