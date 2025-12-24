"""Storage service for file upload/download using MinIO/S3."""

import io
from typing import BinaryIO, Optional
from uuid import UUID

from boto3 import client
from botocore.exceptions import ClientError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class StorageService:
    """MinIO/S3 storage service."""

    def __init__(self):
        """Initialize storage service."""
        self.client = client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
        )
        self.bucket = settings.S3_BUCKET
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure the storage bucket exists."""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info("Storage bucket exists", bucket=self.bucket)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                logger.info("Creating storage bucket", bucket=self.bucket)
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info("Storage bucket created", bucket=self.bucket)
                except Exception as create_error:
                    logger.error(
                        "Failed to create bucket",
                        bucket=self.bucket,
                        error=str(create_error),
                        exc_info=True,
                    )
            else:
                logger.error("Error checking bucket", error=str(e), exc_info=True)

    def upload_file(
        self,
        file_content: bytes,
        object_key: str,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to storage.
        
        Args:
            file_content: File content as bytes
            object_key: S3 object key (path)
            content_type: MIME type
            metadata: Additional metadata
            
        Returns:
            URL or path to uploaded file
        """
        logger.info("Uploading file to storage", object_key=object_key)
        
        try:
            extra_args = {}
            
            if content_type:
                extra_args["ContentType"] = content_type
            
            if metadata:
                extra_args["Metadata"] = {
                    k: str(v) for k, v in metadata.items()
                }
            
            # Upload file
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=file_content,
                **extra_args,
            )
            
            logger.info("File uploaded successfully", object_key=object_key)
            
            # Return the object key (we'll construct full URL when needed)
            return object_key
            
        except Exception as e:
            logger.error(
                "Failed to upload file",
                object_key=object_key,
                error=str(e),
                exc_info=True,
            )
            raise

    def download_file(self, object_key: str) -> bytes:
        """
        Download file from storage.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            File content as bytes
        """
        logger.info("Downloading file from storage", object_key=object_key)
        
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=object_key)
            content = response["Body"].read()
            
            logger.info(
                "File downloaded successfully",
                object_key=object_key,
                size_bytes=len(content),
            )
            
            return content
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "NoSuchKey":
                logger.warning("File not found", object_key=object_key)
                raise FileNotFoundError(f"File not found: {object_key}")
            else:
                logger.error(
                    "Failed to download file",
                    object_key=object_key,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def delete_file(self, object_key: str) -> None:
        """
        Delete file from storage.
        
        Args:
            object_key: S3 object key (path)
        """
        logger.info("Deleting file from storage", object_key=object_key)
        
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_key)
            logger.info("File deleted successfully", object_key=object_key)
            
        except Exception as e:
            logger.error(
                "Failed to delete file",
                object_key=object_key,
                error=str(e),
                exc_info=True,
            )
            raise

    def file_exists(self, object_key: str) -> bool:
        """
        Check if file exists in storage.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.head_object(Bucket=self.bucket, Key=object_key)
            return True
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                return False
            raise

    def get_file_metadata(self, object_key: str) -> dict:
        """
        Get file metadata.
        
        Args:
            object_key: S3 object key (path)
            
        Returns:
            Dictionary with metadata
        """
        try:
            response = self.client.head_object(Bucket=self.bucket, Key=object_key)
            
            return {
                "content_type": response.get("ContentType"),
                "content_length": response.get("ContentLength"),
                "last_modified": response.get("LastModified"),
                "metadata": response.get("Metadata", {}),
                "etag": response.get("ETag"),
            }
            
        except Exception as e:
            logger.error(
                "Failed to get file metadata",
                object_key=object_key,
                error=str(e),
                exc_info=True,
            )
            raise

    def generate_presigned_url(
        self, object_key: str, expiration: int = 3600
    ) -> str:
        """
        Generate presigned URL for temporary file access.
        
        Args:
            object_key: S3 object key (path)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
        """
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": object_key},
                ExpiresIn=expiration,
            )
            
            logger.info(
                "Generated presigned URL",
                object_key=object_key,
                expiration=expiration,
            )
            
            return url
            
        except Exception as e:
            logger.error(
                "Failed to generate presigned URL",
                object_key=object_key,
                error=str(e),
                exc_info=True,
            )
            raise


# Global storage service instance
storage_service = StorageService()


def get_storage_service() -> StorageService:
    """Get storage service instance."""
    return storage_service
