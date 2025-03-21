from groq import Groq
import json
from dotenv import load_dotenv
import httpx
from services.firestore_service import FirestoreService
from services.tools import get_transcript_from_url, tools, youtube_search
from datetime import date
import tiktoken
from langchain.text_splitter import CharacterTextSplitter

load_dotenv()

# Explicitly set the encoding for the model
encoding = tiktoken.get_encoding("cl100k_base")

# Update your token counting function
def count_tokens(text: str) -> int:
    return len(encoding.encode(text))

client = Groq()

class YoutubeService:
    def __init__(self, session_id: str, user_id: str, tag: str):
        self.session_id = session_id
        self.user_id = user_id
        self.tag = tag
        self.firestore = FirestoreService(session_id=self.session_id, tag=self.tag)

    def multi_step_summary(self, transcript: str) -> str:
        # Define a text splitter that splits based on token count using the explicit encoding
        text_splitter = CharacterTextSplitter(
            separator=" ",
            chunk_size=7000,     
            chunk_overlap=100,
            length_function=lambda text: len(encoding.encode(text))
        )
        chunks = text_splitter.split_text(transcript)
        summaries = []
        # Summarize each chunk individually
        for chunk in chunks:
            chunk_response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {"role": "system", "content": "You are a summarization assistant. Summarize the following text concisely:"},
                    {"role": "user", "content": chunk}
                ],
            )
    
            summary_text = chunk_response.choices[0].message.content
            summaries.append(summary_text)
        # Combine individual summaries
        combined_summary = "\n".join(summaries)
        
        return combined_summary

    async def get_youtube_summary (self, query: str):
        today = date.today().strftime("%B %d, %Y")
        chat = await self.firestore.store_conversation(self.user_id, query)
        recent_conversations = await self.firestore.get_user_conversations(limit=10)
        # print(recent_conversations)
        conversation_context = []
        for conv in recent_conversations:
            conversation_context.extend([
                {"role": "user", "content": conv['message']},
                {"role": "assistant", "content": conv['response']}
            ])


        messages = conversation_context + [
            {
                "role": "system",
                "content": (
                    """You are a helpful assistant that can search for youtube videos,
                    If the user is asking for a movie or tutorial search youtube for it
                    get the transcript of the video, and using that, give a summary of
                    the video telling the user all that the video is about. 
                    Don't forget to include the video url in your response
                    You can also
                    respond to normal questions. If you are returning a list of videos,
                    return a JSON with your message and a dictionary with each video detail.
                    If you get a youtube link, just get the transcript. The user can also ask 
                    a question and you can use the transcript to answer the question. 
                    
                    if you are returning videos for a user to select from always return ONLY JSON with keys message and videos DO NOT ADD ANY EXTRA TEXT JUST THE JSON
                    videos should be a list with a each video as a dictionary
                    if you are returning a summary return the summary in string format
                    Your message is being display directly to the user so do NOT add technical details like the format of the response in your message
                    if any of the videos seem to be the users query in your json message give a brief description of the video but STILL return the videos so the user can choose"""
                    f"Today's date is {today}."""
                )
            },
            {"role": "user", "content": f"{query}"}
        ]

        # Initial call to process the query and determine tool calls
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=4096
        )

        response_message = response.choices[0].message
        # print(f"Initial Response:\n{response_message}\n\n")
        tool_calls = response_message.tool_calls

        if tool_calls is not None:
            messages.append(response_message)
            called = False
            print(called)
            transcrip = ""
            available_functions = {
                "youtube_search": youtube_search,
                "get_transcript_from_url": get_transcript_from_url,
            }
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name, None)
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                print(function_name)
                if function_name == "get_transcript_from_url":
                    # print("transcribing")
                    called = True
                    transcrip = function_response
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(function_response),
                })

            # Extract transcript from tool responses
            print(tool_calls[0].function.name)

            transcript = ""
            for msg in messages:
                if tool_calls[0].function.name == "get_transcript_from_url":
                    transcript = transcrip
                    break

            # If transcript exists and exceeds a token threshold, use multi-step summarization
            if transcript and count_tokens(transcript) > 6000:
                # print("Transcript is long; applying multi-step summarization...")
                transcript = self.multi_step_summary(transcript)
                # return final_summary

            # Otherwise, continue with normal workflow
            if called == True:
                print('about  creating new message')
                new_messages = [
                    {
                        "role": "system",
                        "content": (
                            """You are a summarization assistant. You have received a transcript summary from a video. 
                            Refer to every input as "the video" not "the text", Use The phrase "The video" instead of 
                            "the text".

                            Using the transcript provide a summary with each paragraph flowing into the next.
                            """
                        )
                    },
                    {"role": "user", "content": transcript},
                    {"role": "user", "content": query}
                ]
                second_response = client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=new_messages
                )
            else:
                second_response = client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=messages
                )

            response = second_response

            if called == True:
                # print('saving response')
                await self.firestore.store_conversation(self.user_id, query,response.choices[0].message.content)

            return response.choices[0].message.content
        else:
            response = response_message.content
            # print('save response')
            await self.firestore.store_conversation(self.user_id, query,response)

            return response
