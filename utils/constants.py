

from datetime import date


today = date.today().strftime("%B %d, %Y")


TRANSCRIPT_PROMPT = """You are a helpful assistant that gives a really detailed summary of YouTube videos. 
BE AS DETAILED AS POSSIBLE!!!!
Your user should be able to understand everything about the video from your summary without having to watch it. 
Provide the video resources at the end of your summary, incase the user wants to check out the video
"""

SYSTEM_PROMPT = """You are a helpful assistant that can search for youtube videos,
get transcripts, and answer questions.

If the user is asking for the summary of a video, movie or tutorial you can search youtube for videos
and  return ONLY a JSON object whose keys are 'message' and 'videos'.
Return as many videos as possible
The videos should be a dictionary with the video details such as video_id, title, description, channel,views, url, and thumbnail
if any of the videos seem to be the users query in your json message give a brief description of the video but STILL return the videos so the user can choose

If the input is a youtube URL get the transcript for the video and return it as text

If the user is asking a question answer using information from past conversations;
Today's date is {today}."""


FUNCTION_CALL_CONFIG = {
    "tools": [
        {
            "function_declarations": [
                {
                    "name": "youtube_search",
                    "description": "Search YouTube for videos based on a query and returns a dictionary with 10 video titles and URLs for selection.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to search for. This could be the title or description of the video."
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "get_transcript_from_url",
                    "description": "Fetch transcript for a YouTube video using its URL and returns the transcript as a string.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "youtube_url": {
                                "type": "string",
                                "description": "The URL of the YouTube video."
                            }
                        },
                        "required": ["youtube_url"]
                    }
                }
            ]
        }
    ]
}
