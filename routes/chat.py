from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from app.routes.auth import validate_token
from models.chat import ChatRequest
from services.youtube_service import YoutubeService
router = APIRouter()
security = HTTPBearer()

@router.post("/chat")
async def analyze_finances(
    query: ChatRequest,
    token: str = Depends(security)
):
    user = await validate_token(token)

    youtube_service = YoutubeService(session_id=query.session_id, user_id=user["uid"])
    result = youtube_service.get_youtube_summary(query.prompt)
    return result