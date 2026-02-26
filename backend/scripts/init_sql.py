import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine

# Add project root to path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

# Load .env
load_dotenv(BASE_DIR / ".env")

from app.models.sql_models import Base

async def init_db():
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_host = os.getenv("MYSQL_HOST", "")
    mysql_port = os.getenv("MYSQL_PORT", "3306")
    mysql_db = os.getenv("MYSQL_DB", "uni_rec")
    
    if not mysql_password:
        print("[Error] Please set MYSQL_PASSWORD in .env")
        return

    # Construct async connection string
    # mysql+aiomysql://user:password@host:port/db
    db_url = f"mysql+aiomysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    
    print(f"[MySQL] Connecting to {db_url.replace(mysql_password, '******')}...")
    
    try:
        engine = create_async_engine(db_url, echo=True)
        
        async with engine.begin() as conn:
            print("[MySQL] Creating tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        print("[Success] Database initialized successfully!")
        await engine.dispose()
        
    except Exception as e:
        print(f"[Error] Database initialization failed: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
