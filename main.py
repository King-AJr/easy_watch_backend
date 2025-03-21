from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import get_settings
import firebase_admin
from routes import auth, chat

firebase_admin.initialize_app()

settings = get_settings()

app = FastAPI(title=settings.PROJECT_NAME)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
@app.get("/")
async def root():
    return {"message": "Welcome to the Youtube Assistant API"} 

@app.post("/clear-cache")
async def clear_cache():
    get_settings.cache_clear()
    return {"message": "Cache cleared"}