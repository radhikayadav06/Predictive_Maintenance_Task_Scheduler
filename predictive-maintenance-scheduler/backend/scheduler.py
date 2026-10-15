from sqlalchemy import text
from sqlalchemy.orm import Session


def generate_maintenance_jobs(db: Session):
    readings = db.execute(
        text("""
            SELECT
                sr.machine_id,
                sr.priority_score,
                sr.maintenance_priority
            FROM sensor_readings sr
            JOIN (
                SELECT machine_id, MAX(reading_id) AS latest_id
                FROM sensor_readings
                GROUP BY machine_id
            ) latest
                ON sr.reading_id = latest.latest_id
            WHERE sr.priority_score >= 30
              AND sr.maintenance_priority IS NOT NULL
            ORDER BY sr.priority_score DESC
        """)
    ).fetchall()

    created = 0

    for reading in readings:
        existing_job = db.execute(
            text("""
                SELECT job_id
                FROM maintenance_jobs
                WHERE machine_id = :machine_id
                  AND status IN ('Pending', 'Scheduled', 'In Progress')
                LIMIT 1
            """),
            {"machine_id": reading.machine_id}
        ).fetchone()

        if existing_job:
            continue

        db.execute(
            text("""
                INSERT INTO maintenance_jobs
                    (machine_id, priority_score, description, status)
                VALUES
                    (:machine_id, :priority_score, :description, 'Pending')
            """),
            {
                "machine_id": reading.machine_id,
                "priority_score": reading.priority_score,
                "description": (
                    f"Predictive maintenance required: "
                    f"{reading.maintenance_priority} priority"
                )
            }
        )
        created += 1

    db.commit()
    return {"created_jobs": created}


def assign_available_technicians(db: Session):
    jobs = db.execute(
        text("""
            SELECT job_id, required_specialization
            FROM maintenance_jobs
            WHERE status = 'Pending'
              AND technician_id IS NULL
            ORDER BY priority_score DESC, created_at ASC
        """)
    ).fetchall()

    assigned = 0
    skipped = 0

    for job in jobs:
        specialization = job.required_specialization

        if not specialization:
            skipped += 1
            continue

        technician = db.execute(
            text("""
                SELECT t.technician_id
                FROM technicians t
                WHERE t.availability = 'Available'
                  AND LOWER(t.specialization) = LOWER(:specialization)
                  AND NOT EXISTS (
                      SELECT 1
                      FROM maintenance_jobs active_job
                      WHERE active_job.technician_id = t.technician_id
                        AND active_job.status IN (
                            'Pending', 'Scheduled', 'In Progress'
                        )
                  )
                ORDER BY t.technician_id
                LIMIT 1
            """),
            {"specialization": specialization}
        ).fetchone()

        if technician is None:
            skipped += 1
            continue

        result = db.execute(
            text("""
                UPDATE maintenance_jobs
                SET technician_id = :technician_id,
                    status = 'Scheduled'
                WHERE job_id = :job_id
                  AND status = 'Pending'
                  AND technician_id IS NULL
            """),
            {
                "technician_id": technician.technician_id,
                "job_id": job.job_id
            }
        )

        if result.rowcount > 0:
            assigned += 1
        else:
            skipped += 1

    db.commit()

    return {
        "assigned_jobs": assigned,
        "unassigned_jobs": skipped
    }

def allocate_spare_parts(db: Session):
    machine_parts = {
        1: "Bearing",
        2: "Motor Belt",
        3: "Hydraulic Seal"
    }

    jobs = db.execute(
        text("""
            SELECT job_id, machine_id, part_id
            FROM maintenance_jobs
            WHERE status IN ('Pending', 'Scheduled')
              AND part_id IS NULL
            ORDER BY priority_score DESC, created_at ASC
        """)
    ).fetchall()

    allocated = 0
    unavailable = 0

    for job in jobs:
        part_name = machine_parts.get(job.machine_id)

        if not part_name:
            unavailable += 1
            continue

        part = db.execute(
            text("""
                SELECT part_id, quantity
                FROM spare_parts
                WHERE part_name = :part_name
                  AND quantity > 0
                LIMIT 1
                FOR UPDATE
            """),
            {"part_name": part_name}
        ).fetchone()

        if part is None:
            unavailable += 1
            continue

        result = db.execute(
            text("""
                UPDATE maintenance_jobs
                SET part_id = :part_id
                WHERE job_id = :job_id
                  AND part_id IS NULL
            """),
            {
                "part_id": part.part_id,
                "job_id": job.job_id
            }
        )

        if result.rowcount > 0:
            allocated += 1

    db.commit()

    return {
        "allocated_jobs": allocated,
        "unavailable_parts": unavailable
    }
