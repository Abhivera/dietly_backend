import boto3
import os
import uuid
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        # Debug: Print environment variables (remove in production)
        print(f"AWS_ACCESS_KEY_ID exists: {bool(os.getenv('AWS_ACCESS_KEY_ID'))}")
        print(f"AWS_SECRET_ACCESS_KEY exists: {bool(os.getenv('AWS_SECRET_ACCESS_KEY'))}")
        print(f"AWS_S3_BUCKET_NAME: {os.getenv('AWS_S3_BUCKET_NAME')}")
        
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'ap-south-1')
        self.bucket_name = os.getenv('AWS_S3_BUCKET_NAME')
        
        # Check if credentials are loaded
        if not all([self.aws_access_key_id, self.aws_secret_access_key, self.bucket_name]):
            missing = []
            if not self.aws_access_key_id:
                missing.append('AWS_ACCESS_KEY_ID')
            if not self.aws_secret_access_key:
                missing.append('AWS_SECRET_ACCESS_KEY')
            if not self.bucket_name:
                missing.append('AWS_S3_BUCKET_NAME')
            
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        
        # Try different methods to create S3 client
        try:
            # Method 1: Explicit credentials
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            
            # Test the connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info("S3 client initialized successfully with explicit credentials")
            
        except ClientError as e:
            logger.error(f"Failed to initialize S3 client with explicit credentials: {e}")
            
            # Method 2: Use default credential chain (IAM roles, profiles, etc.)
            try:
                self.s3_client = boto3.client('s3', region_name=self.aws_region)
                self.s3_client.head_bucket(Bucket=self.bucket_name)
                logger.info("S3 client initialized successfully with default credentials")
            except Exception as fallback_error:
                logger.error(f"Failed to initialize S3 client with default credentials: {fallback_error}")
                raise ValueError("Could not initialize S3 client with any method")
        
        except NoCredentialsError:
            logger.error("No AWS credentials found")
            raise ValueError("AWS credentials not found or invalid")
        
        except Exception as e:
            logger.error(f"Unexpected error initializing S3 client: {e}")
            raise ValueError(f"Failed to initialize S3 client: {str(e)}")

    def upload_file(self, file_obj, user_id: int, original_filename: str) -> Dict:
        """Upload file to S3 and return file information"""
        try:
            # Generate unique filename
            file_extension = original_filename.split('.')[-1].lower()
            unique_filename = f"{user_id}/{uuid.uuid4().hex}.{file_extension}"
            
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            # Upload to S3
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    'ContentType': self._get_content_type(file_extension),
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Generate presigned URL instead of direct URL
            file_url = self.generate_presigned_url(unique_filename, expiration=86400)  # 24 hours
            
            return {
                'success': True,
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_url': file_url,  # This is now a presigned URL
                's3_key': unique_filename,
                'bucket': self.bucket_name
            }
            
        except ClientError as e:
            logger.error(f"AWS S3 error: {str(e)}")
            return {'success': False, 'error': f"S3 upload failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return {'success': False, 'error': f"Upload failed: {str(e)}"}

    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {str(e)}")
            return False

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """Generate a presigned URL for private file access"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None

    def get_file_content(self, s3_key: str) -> Optional[bytes]:
        """Get file content directly from S3 (for analysis purposes)"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"Error getting file content: {str(e)}")
            return None

    def get_file_stream(self, s3_key: str):
        """Get file stream directly from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body']
        except ClientError as e:
            logger.error(f"Error getting file stream: {str(e)}")
            return None

    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence: {str(e)}")
            return False

    def upload_file_with_public_access(self, file_obj, user_id: int, original_filename: str) -> Dict:
        """Upload file to S3 with public read access (use only if needed)"""
        try:
            # Generate unique filename
            file_extension = original_filename.split('.')[-1].lower()
            unique_filename = f"{user_id}/{uuid.uuid4().hex}.{file_extension}"
            
            # Reset file pointer to beginning
            file_obj.seek(0)
            
            # Upload to S3 with public read ACL
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    'ContentType': self._get_content_type(file_extension),
                    'ServerSideEncryption': 'AES256',
                    'ACL': 'public-read'  # This makes the file publicly readable
                }
            )
            
            # Generate direct URL (will work if bucket allows public access)
            file_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{unique_filename}"
            
            return {
                'success': True,
                'filename': unique_filename,
                'original_filename': original_filename,
                'file_url': file_url,
                's3_key': unique_filename,
                'bucket': self.bucket_name
            }
            
        except ClientError as e:
            logger.error(f"AWS S3 error: {str(e)}")
            return {'success': False, 'error': f"S3 upload failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return {'success': False, 'error': f"Upload failed: {str(e)}"}

    def _get_content_type(self, file_extension: str) -> str:
        """Get content type based on file extension"""
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'bmp': 'image/bmp',
            'tiff': 'image/tiff',
            'pdf': 'application/pdf',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'json': 'application/json'
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')