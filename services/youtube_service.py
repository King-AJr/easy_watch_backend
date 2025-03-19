from groq import Groq
import json
from dotenv import load_dotenv
from services.firestore_service import FirestoreService
from tools import get_transcript_from_url, tools, youtube_search
from datetime import date

load_dotenv()

client = Groq()


class YoutubeService:
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id

    def get_youtube_summary(self, query: str):

        date_now = date.today()
        today = date_now.strftime("%B %d, %Y")
        messages = [
            {
                "role": "system",
                "content": f"""
                            You are a smart assistant. You can search YouTube, fetch video transcripts, and summarize videos for users. 
                            You also answer general questions using transcript data when relevant.
                            - If given a YouTube URL, fetch the transcript and provide a summary.
                            - If given a video title, call a function to search YouTube and return video options.
                            - When the user selects a URL, fetch and summarize its transcript.
                            Today's date: {today}
                            """
            },
            {
                "role": "user",
                "content": f"{query}"
            }
        ]

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        print(f"Initial Response: \n{response.choices[0].message}\n\n")

        if tool_calls:
            available_functions = {
                "youtube_search": youtube_search,
                "get_transcript_from_url": get_transcript_from_url,
            }
            messages.append(response_message)

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name, None)
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": str(function_response),
                    }
                )

            second_response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=messages
            )
            response = second_response

            FirestoreService(self.session_id, self.user_id).save_chat_message(response.choices[0].message.content)

            return response.choices[0].message.content

    # get input from user

    # if input a youtube url, then get the video id

    # get the video id from the youtube url

    # pass video id to youtube transcript api package

    # get the transcript from the youtube video

    # pass transcript to llm to get the summary of the video

    # pass summary to firestore service to save to firestore

    # return the summary of the transcript

    # if input is not a url
    # check if input is question based on the context of the user
    # if question, then pass question to llm to get the answer
    # pass answer to firestore service to save to firestore
    # return the answer

    # if not question, then pass input to youtube_search to get the youtube url

    # pass youtube url to youtube transcript api package

    # get the transcript from the youtube video

    # pass transcript to llm to get the summary of the video

    # return the summary of the transcript

    # pass summary to firestore service to save to firestore
