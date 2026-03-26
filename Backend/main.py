from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from typing import List
from database import init_database, get_table_info
from graph import build_graph
from llm import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "Backend is running!"}


@app.get("/api/graph")
def get_graph():
    return build_graph()


@app.get("/api/tables")
def get_tables():
    return get_table_info()


class ChatRequest(BaseModel):
    question: str
    history: List = []


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    result = chat(req.question, req.history)
    return result


@app.get("/api/node/{node_id}")
def get_node(node_id: str):
    graph = build_graph()
    for node in graph["nodes"]:
        if node["id"] == node_id:
            return node
    return {"error": "Node not found"}