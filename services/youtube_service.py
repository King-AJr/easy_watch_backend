from google import genai
import os
from dotenv import load_dotenv
from utils.constants import TRANSCRIPT_PROMPT, SYSTEM_PROMPT,  FUNCTION_CALL_CONFIG
from services.firestore_service import FirestoreService
from services.tools import get_transcript_from_url, youtube_search


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


class YoutubeService:
    def __init__(self, session_id: str, user_id: str, tag: str):
        self.session_id = session_id
        self.user_id = user_id
        self.tag = tag
        self.firestore = FirestoreService(session_id=self.session_id, tag=self.tag)


    async def get_youtube_summary (self, query: str):

        await self.firestore.store_conversation(self.user_id, query)
        recent_conversations = await self.firestore.get_user_conversations(limit=10)
   
        conversation_context = []
        for conv in recent_conversations:
            conversation_context.extend([
                {"role": "user", "content": conv['message']},
                {"role": "assistant", "content": conv['response']}
            ])

        first_response = client.models.generate_content(
            model="gemini-1.5-pro",
            config=FUNCTION_CALL_CONFIG,
            contents=f"{SYSTEM_PROMPT}\n\n Past Conversations: {conversation_context}\n\n User Query: {query}" 
        )

        part = first_response.candidates[0].content.parts[0]

        function = part.function_call


        if function is not None:
            available_functions = {
                "youtube_search": youtube_search,
                "get_transcript_from_url": get_transcript_from_url,
            }

            function_to_call = available_functions.get(function.name, None)
            function_response = function_to_call(**function.args)

            if function.name == "get_transcript_from_url":
                second_response = client.models.generate_content(
                    model="gemini-1.5-pro",
                    config=FUNCTION_CALL_CONFIG,
                    contents=f"{TRANSCRIPT_PROMPT}\n\n Past Conversations: {conversation_context}\n\n video_info: {function_response}" 
                )

                await self.firestore.store_conversation(self.user_id, query, second_response.text)

                return second_response.text
            else:
                return function_response
                
        else:

            return part.text