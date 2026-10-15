from backend.database import Base, engine
from backend.models import SensorReading

Base.metadata.create_all(bind=engine)

print("Database tables initialized successfully.")