from fastapi import FastAPI
from pydantic import BaseModel
import os

app = FastAPI(title="FastAPI on Cloud Run", version="1.0.0")

class Echo(BaseModel):
    message: str

@app.get("/")
def root():
    return {"status": "ok", "service": os.getenv("SERVICE_NAME", "fastapi-service")}

@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

@app.get("/ping")
def ping():
    return "pong"

@app.post("/echo")
def echo(body: Echo):
    return {"echo": body.message}
