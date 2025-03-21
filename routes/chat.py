from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from routes.auth import validate_token
from models.chat import ChatRequest
from services.youtube_service import YoutubeService
router = APIRouter()
security = HTTPBearer()

@router.post("/chat")
async def analyze_finances(
    query: ChatRequest,
    token: str = Depends(security)
):
    print(token.credentials)
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