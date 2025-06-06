import json
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket
from db import create_db_and_tables

# --- Pydantic Models for API Validation ---

# --- FastAPI Application (runs in the main process) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
  """This function is called by FastAPI on application startup and shutdown."""
  create_db_and_tables()
  yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
  """A simple root endpoint."""
  return {"message": "Welcome to the Async AI Inference Service!"}

@app.websocket("/chat")
async def chat(websocket: WebSocket):
  """WebSocket endpoint for real-time communication."""
  await websocket.accept()
  try:
    while True:
      data = await websocket.receive_text()
      message = json.loads(data)
      response = {"status": "ok", "echo": message}
      await websocket.send_text(json.dumps(response))
  except Exception as e:
    await websocket.close(code=1000, reason=str(e))

# --- Main application entrypoint ---

if __name__ == "__main__":
  uvicorn.run(app)
