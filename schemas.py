from pydantic import BaseModel
from datetime import datetime

class ReminderCreate(BaseModel):
    title: str
    description: str
    date_time: datetime  # Например, "2024-05-20T15:30:00"
    notification_type: str  # "push" или "email"
    user_email: str | None = None  # Обязательно, если notification_type = "email"
    device_token: str | None = None  # Обязательно, если notification_type = "push"

class ReminderResponse(BaseModel):
    id: int
    title: str
    description: str
    date_time: datetime
    notification_type: str

    class Config:
        from_attributes = True  # Работает с SQLAlchemy моделями