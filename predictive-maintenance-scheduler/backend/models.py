from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from backend.database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    reading_id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, nullable=False)

    temperature = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    pressure = Column(Float, nullable=False)
    runtime = Column(Float, nullable=False)

    failure_prediction = Column(Integer, nullable=False)
    failure_risk_percent = Column(Float, nullable=False)

    priority_score = Column(Float, nullable=True)
    maintenance_priority = Column(String(20), nullable=True)

    created_at = Column(DateTime, server_default=func.now())