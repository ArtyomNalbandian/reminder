from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .models import NotificationType

class ReminderBase(BaseModel):
    text: str
    notification_time: datetime
    notification_type: NotificationType
    recipient: str

class ReminderCreate(ReminderBase):
    pass

class ReminderResponse(ReminderBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReminderUpdate(BaseModel):
    status: str 