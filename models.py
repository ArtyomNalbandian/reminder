from sqlalchemy import Column, Integer, String, DateTime
from database import Base

class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    date_time = Column(DateTime)  # Когда отправить уведомление
    notification_type = Column(String)  # "push" или "email"
    user_email = Column(String, nullable=True)  # Если email-уведомление
    device_token = Column(String, nullable=True)  # Если push-уведомление