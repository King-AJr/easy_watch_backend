from langchain_google_firestore import FirestoreChatMessageHistory
from dotenv import load_dotenv
import os
from typing import Dict, List, Optional
from google.cloud import firestore
from datetime import datetime

load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
COLLECTION_NAME = "chat_history"
client = firestore.Client(project=PROJECT_ID)

class FirestoreService:
    def __init__(self, session_id: str = "general", tag: str = "general"):
        """
        Initialize the FirestoreService with a session ID and tag.
        
        The session_id is used for storing messages in the chat history,
        and later combined with the user_id to record session details.
        """
        self.project_id = PROJECT_ID
        self.collection_name = COLLECTION_NAME
        self.session_id = session_id
        self.tag = tag

    def get_chat_history(self) -> FirestoreChatMessageHistory:
        """
        Retrieve the chat history using the session ID.
        """
        return FirestoreChatMessageHistory(
            session_id=self.session_id,
            client=client,
            collection=self.collection_name
        )

    async def store_conversation(self, user_id: str, message: str, response: str="") -> None:
        """
        Store a conversation in Firestore and update the sessions collection.

        This method stores the conversation using langchain_google_firestore,
        then records (or updates) the session information in the "sessions" collection
        using the session_id as the document id, and storing the user_id and tag.
        """
        chat_history = self.get_chat_history()
        

        chat_history.add_user_message(message)
        chat_history.add_ai_message(response)

        session_data = {
            "user_id": user_id,
            "tag": self.tag,
            "updated_at": datetime.utcnow()
        }

        client.collection("sessions").document(self.session_id).set(session_data, merge=True)

    async def get_user_conversations(self, limit: int = 10) -> List[Dict]:
        """
        Retrieve recent conversations for this session.
        
        Note: This method assumes that messages are stored in pairs (user and AI)
        and retrieves the last `limit` messages from the history.
        """
        chat_history = self.get_chat_history()
        
        # Get the last N messages from chat history
        messages = chat_history.messages[-limit:]
        conversations = []
        
        # Process messages in pairs (user message followed by AI response)
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                conversations.append({
                    'message': messages[i].content,
                    'response': messages[i + 1].content,
                    'timestamp': datetime.now()
                })
        
        return conversations
    

    async def retrieve_messages(self, session_id: str, user_id: str, tag: Optional[str] = None) -> List[Dict]:
        """
        Retrieve messages for a given session if the session document matches the
        provided user_id and (if given) tag.

        The method performs the following steps:
          1. Retrieves the session document from the "sessions" collection using the session_id.
          2. Validates that the document's user_id matches the provided user_id.
          3. If a tag is provided, verifies that the document's tag matches.
          4. If all checks pass, retrieves the chat messages from the "chat_history" collection.
          
        Returns:
          A list of dictionaries, each representing a chat message with its content,
          role, and a placeholder for the timestamp.
        """
        session_doc = client.collection("sessions").document(session_id).get()
        if not session_doc.exists:
            return []

        session_data = session_doc.to_dict()


        if session_data.get("user_id") != user_id:
            return []

        if tag is not None and session_data.get("tag") != tag:
            return []

        chat_history = FirestoreChatMessageHistory(
            session_id=session_id,
            client=client,
            collection=self.collection_name
        )

        # Convert messages to a list of dictionaries
        messages_list = []
        
        for i in range(0, len(chat_history.messages), 2):
            if i + 1 < len(chat_history.messages):
                messages_list.append({
                    "id": chat_history.messages[i].id,
                    "role": "user",
                    "content": chat_history.messages[i].content,
                    'timestamp': datetime.now()
                })

                messages_list.append({
                    "role": "system",
                    "content": chat_history.messages[i + 1].content,
                    'timestamp': datetime.now()
                })

        return messages_list
    

    async def get_all_sessions_for_user(self, user_id: str) -> List[Dict]:
        """
        Retrieve all session documents from the "sessions" collection for a given user_id.

        This method queries Firestore for all sessions associated with the provided user_id
        and returns a list of dictionaries containing session details.
        """
        sessions_ref = client.collection("sessions")
        query = sessions_ref.where("user_id", "==", user_id)
        docs = query.stream()
        sessions = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            sessions.append(data)
        return sessions


    async def create_collection_record(self, user_id: str, name: str, color: str) -> Dict:
        """
        Create a new collection record in the "collections" collection tied to the given user_id.
        """
        record_data = {
            "name": name,
            "color": color,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        # Create a new document with an auto-generated ID in the "collections" collection
        doc_ref = client.collection("collections").document()
        doc_ref.set(record_data)
        return {"id": doc_ref.id, **record_data}
    

    async def get_collections_for_user(self, user_id: str) -> List[Dict]:
        """
        Retrieve all collection records from the "collections" collection for a given user_id.
        """
        collections_ref = client.collection("collections")
        query = collections_ref.where("user_id", "==", user_id)
        docs = query.stream()
        collections = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            collections.append(data)
        return collections
    
