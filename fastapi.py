from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
import boto3
from botocore.exceptions import NoCredentialsError
import asyncio
import uuid

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = "your_access_key"
AWS_SECRET_ACCESS_KEY = "your_secret_key"
S3_BUCKET_NAME = "your_s3_bucket_name"
S3_REGION = "your_s3_region"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

app = FastAPI()

async def upload_to_s3(data: bytes, filename: str):
    try:
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=filename, Body=data)
        print(f"Uploaded {filename} to S3.")
    except NoCredentialsError:
        print("Credentials not available.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")
    try:
        while True:
            audio_data = await websocket.receive_bytes()  # Receiving binary audio data
            file_name = f"audio/{uuid.uuid4()}.wav"  # Generate a unique filename
            asyncio.create_task(upload_to_s3(audio_data, file_name))
    except WebSocketDisconnect:
        print("WebSocket connection closed.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
