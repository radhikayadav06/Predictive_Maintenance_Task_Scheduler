from fastapi import FastAPI, Depends, HTTPException
from backend.models import SensorReading
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel

from backend.scheduler import (
    generate_maintenance_jobs,
    assign_available_technicians,
    allocate_spare_parts
)


from backend.database import get_db
from ml.predict_failure import predict_failure

app = FastAPI(title="Predictive Maintenance Task Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensorData(BaseModel):
    machine_id: int
    temperature: float
    vibration: float
    pressure: float
    runtime: float


@app.get("/")
def home():
    return {
        "message": "Predictive Maintenance API is running"
    }


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "api": "running",
        "database": "connected"
    }



@app.post("/predict")
def predict(data: SensorData, db: Session = Depends(get_db)):
    result = predict_failure(
        data.temperature,
        data.vibration,
        data.pressure,
        data.runtime
    )

    # Get machine criticality from the database
    machine = db.execute(
    text(
        "SELECT criticality FROM machines "
        "WHERE machine_id = :machine_id"
    ),
    {"machine_id": data.machine_id}
    ).fetchone()

    if machine is None:
        raise HTTPException(status_code=404, detail="Machine not found")

    risk = result["failure_risk_percent"]
    criticality = machine[0]

    # Calculate maintenance priority score
    priority_score = round(
        (0.7 * risk) + (0.3 * criticality * 20), 2
    )

    if priority_score >= 70:
        priority = "Critical"
    elif priority_score >= 50:
        priority = "High"
    elif priority_score >= 30:
        priority = "Medium"
    else:
        priority = "Low"

    
    reading = SensorReading(
        machine_id=data.machine_id,
        temperature=data.temperature,
        vibration=data.vibration,
        pressure=data.pressure,
        runtime=data.runtime,
        failure_prediction=result["failure_prediction"],
        failure_risk_percent=risk,
        priority_score=priority_score,
        maintenance_priority=priority
    )


    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {
        "reading_id": reading.reading_id,
        "machine_id": reading.machine_id,
        **result,
        "priority_score": priority_score,
        "maintenance_priority": priority,
        "message": "Prediction and priority saved successfully"
    }



@app.get("/readings")
def get_readings(db: Session = Depends(get_db)):
    readings = (
        db.query(SensorReading)
        .order_by(SensorReading.reading_id.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "reading_id": r.reading_id,
            "machine_id": r.machine_id,
            "temperature": r.temperature,
            "vibration": r.vibration,
            "pressure": r.pressure,
            "runtime": r.runtime,
            "failure_prediction": r.failure_prediction,
            "failure_risk_percent": r.failure_risk_percent,
            "priority_score": r.priority_score,
            "maintenance_priority": r.maintenance_priority,
            "created_at": (
                r.created_at.isoformat()
                if r.created_at is not None
                else None
            )
        }
        for r in readings
    ]

@app.post("/scheduler/generate")
def generate_jobs(db: Session = Depends(get_db)):
    try:
        return generate_maintenance_jobs(db)
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to generate maintenance jobs"
        )


@app.get("/scheduler/jobs")
def get_maintenance_jobs(db: Session = Depends(get_db)):
    jobs = db.execute(
        text("""
            SELECT
                mj.job_id,
                mj.machine_id,
                m.machine_name,
                mj.technician_id,
                t.technician_name,
                mj.part_id,
                mj.priority_score,
                mj.description,
                mj.status,
                mj.scheduled_at,
                mj.created_at
            FROM maintenance_jobs mj
            JOIN machines m ON mj.machine_id = m.machine_id
            LEFT JOIN technicians t
                ON mj.technician_id = t.technician_id
            ORDER BY
                CASE mj.status
                    WHEN 'In Progress' THEN 1
                    WHEN 'Pending' THEN 2
                    WHEN 'Scheduled' THEN 3
                    WHEN 'Completed' THEN 4
                    ELSE 5
                END,
                mj.priority_score DESC,
                mj.created_at ASC
        """)
    ).mappings().all()

    return [dict(job) for job in jobs]


@app.post("/scheduler/assign")
def assign_technicians(db: Session = Depends(get_db)):
    try:
        return assign_available_technicians(db)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to assign technicians"
        )
@app.post("/scheduler/allocate-parts")
def allocate_parts(db: Session = Depends(get_db)):
    return allocate_spare_parts(db)

@app.get("/spare-parts")
def get_spare_parts(db: Session = Depends(get_db)):
    parts = db.execute(
        text("""
            SELECT
                part_id,
                part_name,
                quantity,
                minimum_quantity
            FROM spare_parts
            ORDER BY part_id
        """)
    ).fetchall()

    return [
        {
            "part_id": part.part_id,
            "part_name": part.part_name,
            "quantity": part.quantity,
            "minimum_quantity": part.minimum_quantity,
            "low_stock": (
                part.minimum_quantity is not None
                and part.quantity <= part.minimum_quantity
            )
        }
        for part in parts
    ]
