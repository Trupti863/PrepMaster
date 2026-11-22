
import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project folder
BASE_DIR = Path(__file__).resolve().parent

# Load .env from the project folder
load_dotenv(BASE_DIR / ".env")

class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = "sqlite:///prepmaster.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
