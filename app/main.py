from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import pipeline
from app.schemas import ConfirmRequest, QueryRequest, QueryResponse

app = FastAPI(
    title="Ops Assistant Demo",
    description="Desensitized isomorphic demo of FAQ → intent → tools → RAG",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ops-assistant-demo"}


@app.post("/api/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    return pipeline.handle(req.query, inject=req.inject)


@app.post("/api/actions/confirm")
def confirm(req: ConfirmRequest):
    return pipeline.confirm(req.proposal_id, req.token)
