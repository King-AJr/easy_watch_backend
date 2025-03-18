from youtube_transcript_api import YouTubeTranscriptApi
from serpapi import GoogleSearch
import os
import re

def youtube_search(query: str) -> dict:
    """
    Search youtube for videos based on a query and returns a dictionary 
    with 10 video title and video url so the user can select which to transcribe
    """
    params = {
        "engine": "youtube",
        "q": query,
        "api_key": os.getenv('SERPAPI_API_KEY')
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    video_results = results["video_results"]
    return [{"title": video["title"], "link": video["link"]} 
          for video in video_results[:10]]


def get_transcript_from_url(youtube_url: str) -> str:
    """
    Fetch transcript for a youtube video using the youtube url and returns the transcript as a string
    """
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", youtube_url)
    if match:
        video_id = match.group(1)
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([entry["text"] for entry in transcript_list])
        return transcript
    else:
        raise ValueError("Invalid YouTube URL")
    

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