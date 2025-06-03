from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from . import models, schemas, database, notifications
import os

app = FastAPI(title="Reminder Notification Service")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

# Configure APScheduler with SQLAlchemy job store
jobstores = {
    'default': SQLAlchemyJobStore(url=os.getenv("DATABASE_URL"))
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

async def send_notification(notification_id: int):
    # Create a new database session for this job
    db = next(database.get_db())
    try:
        notification = db.query(models.ScheduledNotification).filter(
            models.ScheduledNotification.id == notification_id
        ).first()
        
        if not notification or notification.status != "scheduled":
            return
        
        success = False
        if notification.notification_type == models.NotificationType.FCM:
            success = await notifications.send_fcm_notification(
                notification.recipient,
                "Reminder",
                notification.text
            )
        else:  # EMAIL
            success = await notifications.send_email_notification(
                notification.recipient,
                "Reminder Notification",
                notification.text
            )
        
        notification.status = "sent" if success else "error"
        db.commit()
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.post("/notifications/", response_model=schemas.NotificationResponse)
async def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(database.get_db)
):
    # Create notification record
    db_notification = models.ScheduledNotification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Schedule the notification
    try:
        scheduler.add_job(
            send_notification,
            'date',
            run_date=notification.notification_time,
            args=[db_notification.id],
            id=f"notification_{db_notification.id}"
        )
    except Exception as e:
        db_notification.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to schedule notification: {str(e)}")
    
    return db_notification

@app.delete("/notifications/{notification_id}")
async def cancel_notification(notification_id: int, db: Session = Depends(database.get_db)):
    notification = db.query(models.ScheduledNotification).filter(
        models.ScheduledNotification.reminder_id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Cancel the scheduled job
    try:
        scheduler.remove_job(f"notification_{notification.id}")
    except:
        pass  # Job might have already been executed or doesn't exist
    
    notification.status = "cancelled"
    db.commit()
    return {"message": "Notification cancelled successfully"}

@app.get("/notifications/{notification_id}", response_model=schemas.NotificationResponse)
async def get_notification(notification_id: int, db: Session = Depends(database.get_db)):
    notification = db.query(models.ScheduledNotification).filter(
        models.ScheduledNotification.reminder_id == notification_id,
        models.ScheduledNotification.status != "cancelled"
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return notification 