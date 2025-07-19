from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = FastAPI()

# CORS for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["AI_Results"]
summaries = db["summaries"]

# Format summary to send to frontend
def format_summary(doc):
    return {
        "repo_meta": {
            "repo": doc["repo_meta"]["repo"],
            "branch": doc["repo_meta"]["branch"],
            "author": doc["repo_meta"]["author"]
        },
        "commit_id": doc["commit_id"],
        "codediff": doc.get("codediff", ""),
        "summary": doc["summary"],
        "timestamp": doc["timestamp"]
    }

@app.get("/summaries")
def get_summaries(
    offset: int = 0,
    limit: int = 10,
    query: str = Query(None),
    author: str = Query(None),
    date: str = Query(None),
    time: str = Query(None),
):
    mongo_query = {}

    if query:
        mongo_query["summary"] = {"$regex": query, "$options": "i"}

    if author:
        mongo_query["repo_meta.author"] = {"$regex": author, "$options": "i"}

    if date or time:
        try:
            if date and time:
                start = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                end = start.replace(second=59)
            elif date:
                start = datetime.strptime(date, "%Y-%m-%d")
                end = start.replace(hour=23, minute=59, second=59)
            elif time:
                today = datetime.today().strftime("%Y-%m-%d")
                start = datetime.strptime(f"{today} {time}", "%Y-%m-%d %H:%M")
                end = start.replace(second=59)

            mongo_query["timestamp"] = {"$gte": start, "$lte": end}
        except ValueError:
            pass

    results = summaries.find(mongo_query).sort("timestamp", -1).skip(offset).limit(limit)
    return jsonable_encoder([format_summary(doc) for doc in results])
