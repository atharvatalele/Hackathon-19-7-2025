from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os

router = APIRouter()

# Use exact casing "AI_Results"
client = MongoClient(os.getenv("MONGO_URI"))
db = client["AI_Results"]
users_col = db["users"]
tasks_col = db["tasks"]

# Models
class UserCreate(BaseModel):
    username: str

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    assigned_to: str
    keywords: Optional[List[str]] = []

# List & search users
@router.get("/api/users")
def list_users(search: Optional[str] = Query(None, alias="search")):
    query = {}
    if search:
        query["username"] = {"$regex": search, "$options": "i"}
    return [{"username": u["username"]} for u in users_col.find(query)]

# Create a new user
@router.post("/api/users", status_code=201)
def create_user(u: UserCreate):
    if users_col.find_one({"username": u.username}):
        raise HTTPException(400, "Username already exists")
    users_col.insert_one({"username": u.username, "taskIds": [], "completion": []})
    return {"ok": True}

# Get a user's tasks
@router.get("/api/users/{username}/tasks")
def get_tasks(username: str):
    user = users_col.find_one({"username": username})
    if not user:
        raise HTTPException(404, "User not found")
    active, completed = [], []
    for tid in user.get("taskIds", []):
        t = tasks_col.find_one({"_id": ObjectId(tid)})
        if t:
            active.append({"id": str(t["_id"]), "title": t["title"], "description": t["description"], "progress": t.get("progress",0), "review": t.get("review",False)})
    for cid in user.get("completion", []):
        t = tasks_col.find_one({"_id": ObjectId(cid)})
        if t:
            completed.append({"id": str(t["_id"]), "title": t["title"], "description": t["description"], "review": t.get("review",False)})
    return {"active": active, "completed": completed}

# Create a task
@router.post("/api/tasks", status_code=201)
def create_task(t: TaskCreate):
    if not users_col.find_one({"username": t.assigned_to}):
        raise HTTPException(404, "User not found")
    doc = {"title": t.title, "description": t.description, "assigned_to": t.assigned_to, "keywords": t.keywords, "commits": [], "timestamp": datetime.utcnow(), "progress": 0, "review": False}
    res = tasks_col.insert_one(doc)
    users_col.update_one({"username": t.assigned_to}, {"$push": {"taskIds": res.inserted_id}})
    return {"id": str(res.inserted_id)}

# Complete a task
@router.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: str):
    oid = ObjectId(task_id)
    task = tasks_col.find_one({"_id": oid})
    if not task:
        raise HTTPException(404, "Task not found")
    users_col.update_one({"username": task["assigned_to"]}, {"$pull": {"taskIds": oid}, "$push": {"completion": oid}})
    tasks_col.update_one({"_id": oid}, {"$set": {"progress": 100}})
    return {"ok": True}

# Request review
@router.post("/api/tasks/{task_id}/review")
def review_task(task_id: str):
    oid = ObjectId(task_id)
    if not tasks_col.find_one({"_id": oid}):
        raise HTTPException(404, "Task not found")
    tasks_col.update_one({"_id": oid}, {"$set": {"review": True}})
    return {"ok": True}

# Delete a task
@router.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    oid = ObjectId(task_id)
    task = tasks_col.find_one({"_id": oid})
    if not task:
        raise HTTPException(404, "Task not found")
    users_col.update_one({"username": task["assigned_to"]}, {"$pull": {"taskIds": oid, "completion": oid}})
    tasks_col.delete_one({"_id": oid})
    return {"ok": True}
