from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import ocrService, aiService
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")
PROCESSOR_ID = os.getenv("PROCESSOR_ID")
app = FastAPI()
LOCATION = "us"

class OCRUrlRequest(BaseModel):
    imageUrl: str

class NotesRequest(BaseModel):
    notes: str
    num_questions: int = 5

@app.get("/")
def root():
    return {"msg": "App is live!"}


async def ocr_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Please upload a PDF file"}

    temp_path = file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    text = ocrService.run_ocr_file(temp_path, PROJECT_ID, LOCATION, PROCESSOR_ID)
    return {
        "file": file.filename,
        "pages": text.split("\f"),
        "full_text": text
    }


@app.post("/ai/generate-quiz")
async def generate_quiz(req: NotesRequest):
    quiz = aiService.generate_questions(req.notes, req.num_questions)
    return quiz


@app.post("/ocr-to-quiz/pdf")
async def ocr_to_quiz_pdf(file: UploadFile = File(...), num_questions: int = 5):
    if not file.filename.endswith(".pdf"):
        return {"error": "Please upload a PDF file"}

    temp_path = file.filename
    with open(temp_path, "wb") as f:
        f.write(await file.read())

    text = ocrService.run_ocr_file(temp_path, PROJECT_ID, LOCATION, PROCESSOR_ID)
    quiz = aiService.generate_questions(text, num_questions)
    return {
        "file": file.filename,
        "quiz": quiz
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  

    uvicorn.run(app, host="0.0.0.0", port=port)
