from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from .config import get_settings
from .models import ChatRequest, ChatResponse
from .agent import handle_chat


load_dotenv()
app = FastAPI(title="Zomato RAG Complaint Agent")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        settings = get_settings()
        result = handle_chat(request.message, request.order_id, request.session_id, settings)
        return ChatResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
