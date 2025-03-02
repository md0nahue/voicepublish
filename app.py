import os
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
import boto3
from botocore.exceptions import NoCredentialsError, BotoCoreError, ClientError
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")

    # Generate a unique filename in S3
    file_key = f"audio/{uuid.uuid4()}.wav"

    # Stream directly to S3 using Multipart Upload
    await uploader.multipart_upload_s3(websocket, file_key)

@app.post("/submit")
async def handle_form(request: Request, user_input: str = Form(...)):
    pdb.set_trace()  # This will pause execution for debugging
    return {"message": "Form received!", "user_input": user_input}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
