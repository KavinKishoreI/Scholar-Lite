from pymongo import AsyncMongoClient
import os
from dotenv import load_dotenv

load_dotenv("../.env")

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncMongoClient(MONGO_URI)

db = client["research"]

papers = db["Papers"]

