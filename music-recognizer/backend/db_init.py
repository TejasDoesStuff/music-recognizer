import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from db import metadata

import os
from dotenv import load_dotenv

from models import songs, fingerprints

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

def init_db():
    metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Initialized.")
