"""
API Endpoints for SOP Knowledge Base Discovery and Querying.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.knowledge.loader import sop_loader, SOPDocument
from app.knowledge.vector_store import vector_store, SearchResult

router = APIRouter()


class SearchQueryRequest(BaseModel):
    query: str
    top_k: int = 3
    threshold: float = 0.15


class SearchItemResponse(BaseModel):
    sop_id: str
    title: str
    category: str
    symptoms: List[str]
    score: float
    reason: str
    first_step_instruction: str


@router.get("/", response_model=List[SOPDocument])
async def list_all_sops():
    """Returns all loaded Standard Operating Procedures in the knowledge base."""
    return sop_loader.all()


@router.get("/{sop_id}", response_model=SOPDocument)
async def get_sop_details(sop_id: str):
    """Retrieves a specific SOP document and its execution steps by ID."""
    doc = sop_loader.get(sop_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"SOP with ID '{sop_id}' not found")
    return doc


@router.post("/search", response_model=List[SearchItemResponse])
async def search_sops(request: SearchQueryRequest):
    """Performs semantic vector search and symptom matching against SOP knowledge base."""
    results = vector_store.search(
        query=request.query,
        top_k=request.top_k,
        threshold=request.threshold,
    )
    
    response_items = []
    for r in results:
        first_step = r.sop.steps[0].instruction_spoken if r.sop.steps else ""
        response_items.append(
            SearchItemResponse(
                sop_id=r.sop.sop_id,
                title=r.sop.title,
                category=r.sop.category,
                symptoms=r.sop.symptoms,
                score=r.score,
                reason=r.reason,
                first_step_instruction=first_step,
            )
        )
    return response_items
