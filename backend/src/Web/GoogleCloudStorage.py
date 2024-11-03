import os
import tempfile

from google.cloud import storage
from google.oauth2 import service_account
from src import ABS_GOOGLE_APPLICATION_CREDENTIALS_PATH
from src.Logging.Logging import logger


def get_gcs_client():
    """Initialize and return a Google Cloud Storage client."""
    key_path = ABS_GOOGLE_APPLICATION_CREDENTIALS_PATH
    if not key_path:
        logger.error("GOOGLE_APPLICATION_CREDENTIALS is not set.")
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS is not set.")

    credentials = service_account.Credentials.from_service_account_file(key_path)
    return storage.Client(credentials=credentials)


def get_bucket():
    """Retrieve the GCS bucket from configuration."""
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    if not bucket_name:
        logger.error("GCS_BUCKET_NAME is not set in configuration.")
        raise EnvironmentError("GCS_BUCKET_NAME is not set in configuration.")
    client = get_gcs_client()
    return client.bucket(bucket_name)


def upload_file(file_stream, filename):
    """Upload a file to Google Cloud Storage."""
    try:
        bucket = get_bucket()
        blob = bucket.blob(filename)
        blob.upload_from_file(file_stream)
        logger.info(f"File '{filename}' uploaded to GCS bucket '{bucket.name}'.")
        return f"File '{filename}' uploaded successfully."
    except Exception as e:
        logger.error(f"Failed to upload file '{filename}': {str(e)}")
        raise Exception(f"Failed to upload file: {str(e)}")


def download_file(filename):
    """Download a file from Google Cloud Storage"""
    try:
        bucket = get_bucket()
        blob = bucket.blob(filename)
        if not blob.exists():
            logger.warning(f"File '{filename}' does not exist in bucket '{bucket.name}'.")
            raise FileNotFoundError(f"File '{filename}' does not exist.")

        temp_file_path = tempfile.mktemp()
        blob.download_to_filename(temp_file_path)
        logger.info(f"File '{filename}' downloaded from GCS bucket '{bucket.name}'.")
        return temp_file_path
    except Exception as e:
        logger.error(f"Failed to download file '{filename}': {str(e)}")
        raise Exception(f"Failed to download file: {str(e)}")


def list_files():
    """List all files in the Google Cloud Storage bucket."""
    try:
        bucket = get_bucket()
        blobs = bucket.list_blobs()
        files = [blob.name for blob in blobs]
        logger.info(f"Listed {len(files)} files from GCS bucket '{bucket.name}'.")
        return files
    except Exception as e:
        logger.error(f"Failed to list files: {str(e)}")
        raise Exception(f"Failed to list files: {str(e)}")


def delete_file(filename):
    """Delete a file from Google Cloud Storage."""
    try:
        bucket = get_bucket()
        blob = bucket.blob(filename)
        if not blob.exists():
            logger.warning(f"File '{filename}' does not exist in bucket '{bucket.name}'.")
            raise FileNotFoundError(f"File '{filename}' does not exist.")

        blob.delete()
        logger.info(f"File '{filename}' deleted from GCS bucket '{bucket.name}'.")
        return f"File '{filename}' deleted successfully."
    except Exception as e:
        logger.error(f"Failed to delete file '{filename}': {str(e)}")
        raise Exception(f"Failed to delete file: {str(e)}")
