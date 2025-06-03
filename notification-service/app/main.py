from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from . import models, schemas, database, notifications
import os
import httpx
import logging

app = FastAPI(title="Reminder Notification Service")

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

STORAGE_SERVICE_URL = "http://storage-service:8000"

# Configure APScheduler with SQLAlchemy job store
jobstores = {
    'default': SQLAlchemyJobStore(url=os.getenv("DATABASE_URL"))
}
scheduler = AsyncIOScheduler(jobstores=jobstores)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_notification(notification_id: int):
    # Create a new database session for this job
    db = next(database.get_db())
    try:
        notification = db.query(models.ScheduledNotification).filter(
            models.ScheduledNotification.id == notification_id
        ).first()
        
        if not notification or notification.status != "scheduled":
            logger.info(f"Notification {notification_id} skipped: status={notification.status if notification else 'not found'}")
            return
        
        logger.info(f"Sending notification {notification_id} (reminder_id={notification.reminder_id})")
        
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
        logger.info(f"Notification {notification_id} delivery status: {'success' if success else 'error'}")

        # Notify storage service about the status
        async with httpx.AsyncClient() as client:
            try:
                logger.info(f"Updating reminder {notification.reminder_id} status to {'sent' if success else 'error'}")
                status_response = await client.put(
                    f"{STORAGE_SERVICE_URL}/reminders/{notification.reminder_id}/status",
                    params={"status": "sent" if success else "error"}
                )
                if status_response.status_code != 200:
                    logger.error(f"Failed to update status in storage service. Status code: {status_response.status_code}, Response: {status_response.text}")
                else:
                    logger.info(f"Successfully updated reminder {notification.reminder_id} status")
            except httpx.RequestError as e:
                logger.error(f"Failed to update status in storage service: {str(e)}")
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