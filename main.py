from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
import os
import uuid
from database import SessionLocal, FileMetadata
from sqlalchemy.orm import Session
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import datetime
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
load_dotenv()

origins = [
    "http://localhost",
    "http://localhost:3000",  # Add the frontend URL (including port) if applicable
    "https://pdf-search-frontend.vercel.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)



UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY")
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

filepath = None

class Question(BaseModel):
    question: str
    file_path: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/answer/" )
def get_answer(question: Question, db: Session = Depends(get_db)):
    file_path = question.file_path
    
    if file_path:
        loader = PyMuPDFLoader(file_path)
        data = loader.load()
        full_text = " ".join([str(doc) for doc in data])

        try:
            model = ChatGoogleGenerativeAI(model="gemini-pro", convert_system_message_to_human=True)
            response = model(
                [
                    SystemMessage(content=full_text),
                    HumanMessage(content=question.question),
                ]
            )
            return response.content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing question: {e}")
    else:
        raise HTTPException(status_code=404, detail="No files found")




@app.post("/uploadPDF/")
async def upload_PDF(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIRECTORY, f"{file_id}.pdf")
    
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        file_metadata = FileMetadata(
            id=file_id,
            file_name=file.filename,
            upload_date=datetime.datetime.utcnow()
        )
        db.add(file_metadata)
        db.commit()
        return {"message": "PDF Uploaded Successfully", "status": 200, "file_path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)