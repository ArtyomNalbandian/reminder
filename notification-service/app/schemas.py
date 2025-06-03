from pydantic import BaseModel
from datetime import datetime
from .models import NotificationType

class NotificationCreate(BaseModel):
    reminder_id: int
    text: str
    notification_time: datetime
    notification_type: NotificationType
    recipient: str

class NotificationResponse(NotificationCreate):
    id: int
    status: str

    class Config:
        from_attributes = True 