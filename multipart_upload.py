import asyncio
from botocore.exceptions import ClientError
from fastapi import WebSocket, WebSocketDisconnect
from s3_client import s3_client  # Import the S3 client
from s3_client import S3_BUCKET_NAME  # Import bucket name

# Minimum S3 part size for multipart upload (5MB)
MIN_PART_SIZE = 5 * 1024 * 1024  

class S3MultipartUploader:
    def __init__(self):
        self.s3_client = s3_client
        self.bucket_name = S3_BUCKET_NAME

    async def multipart_upload_s3(self, websocket: WebSocket, file_key: str):
        """Handles multipart upload to S3 with fallback for small files."""
        try:
            # Step 1: Initiate Multipart Upload
            response = self.s3_client.create_multipart_upload(Bucket=self.bucket_name, Key=file_key)
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
                        part_response = self.s3_client.upload_part(
                            Bucket=self.bucket_name,
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
                            part_response = self.s3_client.upload_part(
                                Bucket=self.bucket_name,
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
                            self.s3_client.complete_multipart_upload(
                                Bucket=self.bucket_name,
                                Key=file_key,
                                UploadId=upload_id,
                                MultipartUpload={"Parts": part_etags}
                            )
                            print(f"Upload completed: {file_key}")
                        else:
                            print("No parts uploaded, skipping completion.")
                    except Exception as e:
                        print(f"Error completing upload: {e}")
                    return

        except ClientError as e:
            # Handle the EntityTooSmall error
            if e.response['Error']['Code'] == 'EntityTooSmall':
                print(f"Multipart upload too small, falling back to a standard upload for {file_key}")

                # Abort Multipart Upload
                self.s3_client.abort_multipart_upload(Bucket=self.bucket_name, Key=file_key, UploadId=upload_id)

                # Standard S3 upload
                self.s3_client.put_object(Bucket=self.bucket_name, Key=file_key, Body=bytes(buffer))
                print(f"Fallback upload completed for {file_key}")

            else:
                print(f"Error during upload: {e}")
                if 'upload_id' in locals():
                    self.s3_client.abort_multipart_upload(Bucket=self.bucket_name, Key=file_key, UploadId=upload_id)
                    print(f"Upload aborted: {file_key}")
