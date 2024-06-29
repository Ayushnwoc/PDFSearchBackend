from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FileMetadata(Base):
    __tablename__ = "files"

    id = Column(String, primary_key=True, index=True)
    file_name = Column(String, index=True)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)
