from pydantic import BaseModel, validator
from datetime import datetime, timezone
from typing import Optional
from .models import NotificationType

class ReminderBase(BaseModel):
    text: str
    notification_time: datetime
    notification_type: NotificationType
    recipient: str

class ReminderCreate(ReminderBase):
    @validator('notification_time')
    def validate_notification_time(cls, v):
        current_time = datetime.now(timezone.utc)
        notification_time = v.replace(tzinfo=timezone.utc)
        
        if notification_time <= current_time:
            raise ValueError("Notification time must be in the future")
        return v

class ReminderResponse(ReminderBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReminderUpdate(BaseModel):
    status: str 