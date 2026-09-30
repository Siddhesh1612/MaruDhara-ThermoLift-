import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/thermolift.db")

# If using SQLite relative path, ensure directory exists
if DATABASE_URL.startswith("sqlite:///"):
    db_path_str = DATABASE_URL.replace("sqlite:///", "")
    # Check if absolute or relative
    db_path = Path(db_path_str)
    if not db_path.is_absolute():
        # Root of workspace
        workspace_root = Path(__file__).resolve().parent.parent.parent
        db_path = workspace_root / db_path
        DATABASE_URL = f"sqlite:///{db_path.as_posix()}"
    db_path.parent.mkdir(parents=True, exist_ok=True)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_engine():
    """Return the SQLAlchemy engine."""
    return engine

def get_session():
    """Return a new SQLAlchemy session."""
    return SessionLocal()
