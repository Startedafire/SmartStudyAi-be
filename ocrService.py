from google.cloud import documentai_v1 as documentai
import requests
import os

# Load credentials (make sure key.json exists in project folder)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "key.json"

def run_ocr_file(file_path, project_id, location, processor_id):
    """Extract text from a local file (PDF, PNG, JPG)"""
    client = documentai.DocumentProcessorServiceClient()
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
    # Download the image temporarily
    response = requests.get(image_url)
    response.raise_for_status()

    client = documentai.DocumentProcessorServiceClient()
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
