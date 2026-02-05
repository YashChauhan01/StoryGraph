from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["rag"])

class QueryRequest(BaseModel):
    manuscript_id: str
    question: str

class QueryResponse(BaseModel):
    answer: str

@router.post("/query", response_model=QueryResponse)
async def ask_story(payload: QueryRequest):
    try:
        answer = await rag_service.answer_question(payload.manuscript_id, payload.question)
        return QueryResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))