from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from .database import Base
import enum

class NotificationType(str, enum.Enum):
    FCM = "fcm"
    EMAIL = "email"

class ScheduledNotification(Base):
    __tablename__ = "scheduled_notifications"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, nullable=False)
    text = Column(String, nullable=False)
    notification_time = Column(DateTime, nullable=False)
    notification_type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    recipient = Column(String, nullable=False)
    status = Column(String, default="scheduled")  # scheduled, sent, cancelled, error 