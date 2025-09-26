from google.cloud import documentai_v1 as documentai
from google.oauth2 import service_account
import requests
import os
import json

# Load credentials once from environment
credentials_info = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)

# Create a single client using credentials
client = documentai.DocumentProcessorServiceClient(credentials=credentials)

def run_ocr_file(file_path, project_id, location, processor_id):
    """Extract text from a local file (PDF, PNG, JPG)"""
    name = client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as f:
        file_content = f.read()

    raw_document = documentai.RawDocument(
        content=file_content,
        mime_type="application/pdf" if file_path.endswith(".pdf") else "image/jpeg"
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
    )

    result = client.process_document(request=request)
    return result.document.text


def run_ocr_url(image_url, project_id, location, processor_id):
    """Extract text from an image URL"""
    response = requests.get(image_url)
    response.raise_for_status()

    name = client.processor_path(project_id, location, processor_id)

    raw_document = documentai.RawDocument(
        content=response.content,
        mime_type="image/jpeg"  # assume JPG/PNG
    )

    request = documentai.ProcessRequest(
        name=name,
        raw_document=raw_document,
    )

    result = client.process_document(request=request)
    return result.document.text
