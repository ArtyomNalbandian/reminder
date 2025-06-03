from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
from . import models, schemas, database
from typing import List, Optional
from enum import Enum

class ReminderStatus(str, Enum):
    PENDING = "pending"
    CANCELLED = "cancelled"
    ERROR = "error"
    SENT = "sent"

app = FastAPI(title="Reminder Storage Service")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

NOTIFICATION_SERVICE_URL = "http://notification-service:8000"

@app.post("/reminders/", response_model=schemas.ReminderResponse)
async def create_reminder(reminder: schemas.ReminderCreate, db: Session = Depends(database.get_db)):
    db_reminder = models.Reminder(
        **reminder.dict(),
        status="pending",
        created_at=datetime.utcnow()
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)
    
    # Send reminder to notification service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/",
                json={
                    "reminder_id": db_reminder.id,
                    "text": db_reminder.text,
                    "notification_time": db_reminder.notification_time.isoformat(),
                    "notification_type": db_reminder.notification_type,
                    "recipient": db_reminder.recipient
                }
            )
            if response.status_code != 200:
                db_reminder.status = "error"
                db.commit()
                raise HTTPException(status_code=500, detail="Failed to schedule notification")
        except httpx.RequestError:
            db_reminder.status = "error"
            db.commit()
            raise HTTPException(status_code=500, detail="Failed to connect to notification service")
    
    return db_reminder

@app.get("/reminders/", response_model=List[schemas.ReminderResponse])
def get_reminders(
    status: Optional[ReminderStatus] = Query(None, description="Filter reminders by status"),
    db: Session = Depends(database.get_db)
):
    query = db.query(models.Reminder)
    
    # Фильтруем только если указан параметр status
    if status:
        query = query.filter(models.Reminder.status == status)
    
    return query.all()

@app.get("/reminders/{reminder_id}", response_model=schemas.ReminderResponse)
def get_reminder(reminder_id: int, db: Session = Depends(database.get_db)):
    reminder = db.query(models.Reminder).filter(
        models.Reminder.id == reminder_id,
        models.Reminder.status != "cancelled"
    ).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder

#fdfsfhdj


@app.delete("/reminders/{reminder_id}")
async def cancel_reminder(reminder_id: int, db: Session = Depends(database.get_db)):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    # Cancel reminder in notification service
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{NOTIFICATION_SERVICE_URL}/notifications/{reminder_id}")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to cancel notification")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to connect to notification service")
    
    reminder.status = "cancelled"
    db.commit()
    return {"message": "Reminder cancelled successfully"}

@app.put("/reminders/{reminder_id}/status", response_model=schemas.ReminderResponse)
async def update_reminder_status(
    reminder_id: int,
    status: ReminderStatus,
    db: Session = Depends(database.get_db)
):
    reminder = db.query(models.Reminder).filter(models.Reminder.id == reminder_id).first()
    if reminder is None:
        raise HTTPException(status_code=404, detail="Reminder not found")
    
    reminder.status = status
    db.commit()
    db.refresh(reminder)
    return reminder 