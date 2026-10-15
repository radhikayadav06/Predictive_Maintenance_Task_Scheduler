from sqlalchemy import text
from backend.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT DATABASE()"))
        print("Connected to database:", result.scalar())
except Exception as error:
    print("Database connection failed:", error)