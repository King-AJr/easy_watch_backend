from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from routes.auth import validate_token
from models.chat import ChatRequest, CollectionCreateRequest
from services.firestore_service import FirestoreService
from services.youtube_service import YoutubeService
from starlette.status import HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED, HTTP_200_OK



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
        user = await validate_token(token)
        user_id = user["uid"]

    print(query.session_id)
    youtube_service = YoutubeService(session_id=query.session_id, user_id=user_id, tag=query.tag)

    result = await youtube_service.get_youtube_summary(query.prompt)
    return result

@router.get('/sessions')
async def get_sessions(
    token: str = Depends(security)
):           

    user = await validate_token(token)
    user_id = user["uid"]
    firestore_service = FirestoreService()

    result = await firestore_service.get_all_sessions_for_user(user_id=user_id)

    return result


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, token: str = Depends(security)):

    user = await validate_token(token)
    user_id = user["uid"]

    firestore_service = FirestoreService(session_id=session_id)

    messages = await firestore_service.retrieve_messages(session_id=session_id, user_id=user_id)
    
    if not messages:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Session not found or access denied")
    
    return messages

@router.post("/collections", status_code=HTTP_200_OK)
async def create_collection(
    collection_req: CollectionCreateRequest,
    token: str = Depends(security)
):

    user = await validate_token(token)
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = user["uid"]

    # Initialize FirestoreService (session_id and tag are not used in this method)
    firestore_service = FirestoreService()
    new_collection = await firestore_service.create_collection_record(
        user_id=user_id,
        name=collection_req.name,
        color=collection_req.color
    )

    return new_collection

@router.get("/collections", status_code=HTTP_200_OK)
async def get_user_collections(token: str = Depends(security)):
    user = await validate_token(token)
    if not user:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = user["uid"]

    firestore_service = FirestoreService()
    collections = await firestore_service.get_collections_for_user(user_id=user_id)
    return collections
