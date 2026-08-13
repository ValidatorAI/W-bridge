import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from hermpers.environment import DATABASE_URL

if DATABASE_URL.startswith("sqlite:///"):
	sqlite_file_path = DATABASE_URL.replace("sqlite:///", "", 1)
	if sqlite_file_path.startswith("/"):
		sqlite_dir = os.path.dirname(sqlite_file_path)
		if sqlite_dir:
			os.makedirs(sqlite_dir, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
