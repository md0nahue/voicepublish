import os
import asyncio
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import boto3
from botocore.exceptions import NoCredentialsError, BotoCoreError, ClientError

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION")

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=S3_REGION
)

app = FastAPI()

# Minimum S3 part size for multipart upload (5MB)
MIN_PART_SIZE = 5 * 1024 * 1024  

async def multipart_upload_s3(websocket: WebSocket, file_key: str):
    """Handles multipart upload to S3 with fallback for small files."""
    try:
        # Step 1: Initiate Multipart Upload
        response = s3_client.create_multipart_upload(Bucket=S3_BUCKET_NAME, Key=file_key)
        upload_id = response["UploadId"]
        print(f"Multipart upload started: {file_key}")

        buffer = bytearray()
        part_number = 1
        part_etags = []

        while True:
            try:
                audio_chunk = await websocket.receive_bytes()  # Receive binary data
                buffer.extend(audio_chunk)

                # Step 2: Upload Part when buffer reaches minimum size
                if len(buffer) >= MIN_PART_SIZE:
                    part_response = s3_client.upload_part(
                        Bucket=S3_BUCKET_NAME,
                        Key=file_key,
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=bytes(buffer)
                    )
                    part_etags.append({"ETag": part_response["ETag"], "PartNumber": part_number})
                    print(f"Uploaded part {part_number} ({len(buffer)} bytes) for {file_key}")

                    # Clear buffer and move to next part
                    buffer.clear()
                    part_number += 1

            except WebSocketDisconnect:
                print(f"WebSocket disconnected, completing upload: {file_key}")

                # Upload any remaining buffered data
                if buffer:
                    try:
                        part_response = s3_client.upload_part(
                            Bucket=S3_BUCKET_NAME,
                            Key=file_key,
                            PartNumber=part_number,
                            UploadId=upload_id,
                            Body=bytes(buffer)
                        )
                        part_etags.append({"ETag": part_response["ETag"], "PartNumber": part_number})
                        print(f"Uploaded final part {part_number} ({len(buffer)} bytes) for {file_key}")
                    except Exception as e:
                        print(f"Failed to upload remaining data: {e}")

                # Complete multipart upload
                try:
                    if part_etags:
                        s3_client.complete_multipart_upload(
                            Bucket=S3_BUCKET_NAME,
                            Key=file_key,
                            UploadId=upload_id,
                            MultipartUpload={"Parts": part_etags}
                        )
                        print(f"Upload completed: {file_key}")
                    else:
                        print("No parts uploaded, skipping completion.")
                except Exception as e:
                    print(f"Error completing upload: {e}")

        # Step 3: Upload Remaining Buffer (If Any)
        if buffer:
            part_response = s3_client.upload_part(
                Bucket=S3_BUCKET_NAME,
                Key=file_key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=bytes(buffer)
            )
            part_etags.append({"ETag": part_response["ETag"], "PartNumber": part_number})
            print(f"Uploaded final part {part_number} ({len(buffer)} bytes) for {file_key}")

        # Step 4: Complete Multipart Upload
        s3_client.complete_multipart_upload(
            Bucket=S3_BUCKET_NAME,
            Key=file_key,
            UploadId=upload_id,
            MultipartUpload={"Parts": part_etags}
        )
        print(f"Upload completed: {file_key}")

    except ClientError as e:
        # Handle the EntityTooSmall error
        if e.response['Error']['Code'] == 'EntityTooSmall':
            print(f"Multipart upload too small, falling back to a standard upload for {file_key}")

            # Abort Multipart Upload
            s3_client.abort_multipart_upload(Bucket=S3_BUCKET_NAME, Key=file_key, UploadId=upload_id)

            # Standard S3 upload
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_key, Body=bytes(buffer))
            print(f"Fallback upload completed for {file_key}")

        else:
            print(f"Error during upload: {e}")
            if 'upload_id' in locals():
                s3_client.abort_multipart_upload(Bucket=S3_BUCKET_NAME, Key=file_key, UploadId=upload_id)
                print(f"Upload aborted: {file_key}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")

    # Generate a unique filename in S3
    file_key = f"audio/{uuid.uuid4()}.wav"

    # Stream directly to S3 using Multipart Upload with proper buffering
    await multipart_upload_s3(websocket, file_key)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
