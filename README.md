# **YouTube Video Summarization API**

## **Overview**
This project automates the process of searching for YouTube videos, extracting transcripts, and generating structured summaries. It leverages function calling to streamline the workflow using FastAPI, YouTube API, Groq LLM, and Firestore for data storage.

---

## **Features**
- 🔎 **YouTube Video Search** - Finds relevant videos based on user queries.
- 📝 **Transcript Extraction** - Retrieves video transcripts using the YouTube API.
- 📄 **AI-Powered Summarization** - Generates structured summaries using LLMs.
- 💾 **Firestore Storage** - Saves search results, transcripts, and summaries for retrieval.
- 🛠 **FastAPI Integration** - Provides API endpoints for seamless interaction.

---

## **Installation**
### **1. Clone the Repository**
```sh
$ git clone https://github.com/your-repo/easy_watch_backend.git
$ cd easy_watch_backend
```

### **2. Set Up Virtual Environment**
```sh
$ python -m venv venv
$ source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### **3. Install Dependencies**
```sh
$ pip install -r requirements.txt
```

### **4. Set Up Environment Variables**
Create a `.env` file and add the following:
```
GROQ_API_KEY=your_groq_api_key
YOUTUBE_API_KEY=your_youtube_api_key
FIREBASE_CREDENTIALS=your_firebase_credentials.json
```

### **5. Run the FastAPI Server**
```sh
$ uvicorn main:app --reload
```

---

## **API Endpoints**
### **1. Search for YouTube Videos**
**Endpoint:** `POST /api/search`

**Request Body:**
```json
{
  "query": "latest AI advancements"
}
```

**Response:**
```json
{
  "videos": [
    {
      "video_id": "abc123",
      "title": "Latest AI Breakthroughs",
      "url": "https://www.youtube.com/watch?v=abc123"
    }
  ]
}
```

### **2. Get Transcript & Summary**
**Endpoint:** `POST /api/summarize`

**Request Body:**
```json
{
  "video_url": "https://www.youtube.com/watch?v=xyz456"
}
```

**Response:**
```json
{
  "summary": "The video explains recent AI advancements including deep learning, NLP, and robotics."
}
```

---

## **Function Interactions**
### **1. `youtube_search(query: str) -> List[Dict]`**
- **Purpose:** Searches YouTube for videos.
- **Returns:** A list of top 10 video results.

### **2. `get_transcript_from_url(youtube_url: str) -> str`**
- **Purpose:** Extracts the video transcript.
- **Returns:** The full text transcript.

### **3. `get_youtube_summary(query: str) -> str`**
- **Purpose:** Handles search, transcript extraction, and summary generation.
- **Returns:** A structured summary.

---

## **Example Workflow**
### **Scenario 1: User Searches for AI Videos**
1. User sends a query: _"Latest AI advancements."_
2. `youtube_search` retrieves a list of videos.
3. The system selects a relevant video.
4. `get_transcript_from_url` fetches the transcript.
5. AI generates a structured summary.
6. Summary is returned and saved in Firestore.

### **Scenario 2: User Provides a YouTube URL**
1. User sends: _"https://www.youtube.com/watch?v=xyz456"_
2. `get_transcript_from_url` retrieves transcript.
3. AI generates a structured summary.
4. Summary is returned and saved.

---

## **Contributing**
1. Fork the repository 📌
2. Create a feature branch 🛠️
3. Commit changes 📄
4. Open a pull request ✅

---

## **License**
This project is licensed under the MIT License.

---

## **Contact**
For questions, reach out via [talk2king.aj@gmail.com](mailto:talk2king.aj@gmail.com), [Alliekundayo6@gmail.com](mailto:Alliekundayo6@gmail.com).

