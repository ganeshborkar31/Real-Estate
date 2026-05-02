import os

from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def health() -> dict:
    return {
        "status": "ok",
        "project": os.getenv("PROJECT_NAME", "real-estate-starter"),
        "supabase_url_set": bool(os.getenv("SUPABASE_URL")),
        "pinecone_api_key_set": bool(os.getenv("PINECONE_API_KEY")),
    }
