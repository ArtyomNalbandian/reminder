from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLAlchemyEnum
from .database import Base
import enum

class NotificationType(str, enum.Enum):
    FCM = "fcm"
    EMAIL = "email"

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    notification_time = Column(DateTime, nullable=False)
    notification_type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    recipient = Column(String, nullable=False)  # email address or FCM token
    status = Column(String, default="pending")  # pending, sent, cancelled
    created_at = Column(DateTime, nullable=False) 