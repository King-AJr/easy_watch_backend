from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from routes.auth import validate_token
from models.chat import ChatRequest
from services.firestore_service import FirestoreService
from services.youtube_service import YoutubeService
from starlette.status import HTTP_404_NOT_FOUND



router = APIRouter()
security = HTTPBearer()

@router.post("/chat")
async def analyze_finances(
    query: ChatRequest,
    token: str = Depends(security)
):
    if token.credentials.startswith("guest"):
        user_id = token.credentials
    else:
        print('validating')
        user = await validate_token(token.credentials)
        user_id = user.id

    print(query.session_id)
    youtube_service = YoutubeService(session_id=query.session_id, user_id=user_id, tag=query.tag)

    result = await youtube_service.get_youtube_summary(query.prompt)
    return result

@router.get('/sessions')
async def get_sessions(
    token: str = Depends(security)
):           
    user = await validate_token(token.credentials)
    user_id = user.id
    firestore_service = FirestoreService()

    result = await firestore_service.get_all_sessions_for_user(user_id=user_id)

    return result


@router.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, token: str = Depends(security)):

    user = await validate_token(token.credentials)
    user_id = user.id

    firestore_service = FirestoreService(session_id=session_id)

    messages = await firestore_service.retrieve_messages(session_id=session_id, user_id=user_id)
    
    if not messages:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Session not found or access denied")
    
    return messages