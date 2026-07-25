from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import agent, ingest, rag, wiki
from .db import init_db
from .llm import model_status
from .retrieval import hybrid_search

app = FastAPI(title="Kora", version="0.1.0", description="Living knowledge product prototype")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskBody(BaseModel):
    question: str = Field(min_length=1)
    session_id: str | None = None
    mode: Literal["rag", "agent"] = "rag"
    top_k: int = 6


class SessionBody(BaseModel):
    title: str = "New chat"
    mode: Literal["rag", "agent"] = "rag"


class WikiBody(BaseModel):
    document_id: str


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True, "product": "Kora", "models": model_status()}


@app.get("/api/documents")
def api_list_documents() -> list[dict[str, Any]]:
    return ingest.list_documents()


@app.get("/api/documents/{doc_id}")
def api_get_document(doc_id: str) -> dict[str, Any]:
    doc = ingest.get_document(doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    return doc


@app.delete("/api/documents/{doc_id}")
def api_delete_document(doc_id: str) -> dict[str, bool]:
    if not ingest.delete_document(doc_id):
        raise HTTPException(404, "document not found")
    return {"ok": True}


@app.post("/api/documents/upload")
async def api_upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
) -> dict[str, Any]:
    raw = await file.read()
    if not raw:
        raise HTTPException(400, "empty file")
    return await ingest.ingest_file(file.filename or "untitled.txt", raw, title=title)


@app.post("/api/documents/text")
async def api_ingest_text(title: str = Form(...), content: str = Form(...)) -> dict[str, Any]:
    if not content.strip():
        raise HTTPException(400, "empty content")
    return await ingest.ingest_document(title, "paste.txt", content)


@app.get("/api/search")
async def api_search(q: str, top_k: int = 6) -> list[dict[str, Any]]:
    return await hybrid_search(q, top_k=top_k)


@app.post("/api/sessions")
def api_create_session(body: SessionBody) -> dict[str, Any]:
    return rag.create_session(body.title, body.mode)


@app.get("/api/sessions")
def api_list_sessions() -> list[dict[str, Any]]:
    return rag.list_sessions()


@app.get("/api/sessions/{session_id}/messages")
def api_session_messages(session_id: str) -> list[dict[str, Any]]:
    return rag.get_session_messages(session_id)


@app.post("/api/ask")
async def api_ask(body: AskBody) -> dict[str, Any]:
    session_id = body.session_id
    if not session_id:
        session = rag.create_session(body.question[:48] or "New chat", body.mode)
        session_id = session["id"]

    if body.mode == "agent":
        result = await agent.agent_answer(session_id, body.question)
    else:
        result = await rag.rag_answer(session_id, body.question, top_k=body.top_k)
    result["session_id"] = session_id
    return result


@app.get("/api/wiki")
def api_list_wiki() -> list[dict[str, Any]]:
    return wiki.list_wiki_pages()


@app.get("/api/wiki/{slug}")
def api_get_wiki(slug: str) -> dict[str, Any]:
    page = wiki.get_wiki_page(slug)
    if not page:
        raise HTTPException(404, "wiki page not found")
    return page


@app.post("/api/wiki/distill")
async def api_distill(body: WikiBody) -> dict[str, Any]:
    try:
        return await wiki.distill_wiki(body.document_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
