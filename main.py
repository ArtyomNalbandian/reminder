from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import requests
from models import Reminder
from schemas import ReminderCreate, ReminderResponse
from database import SessionLocal, engine, Base

# Создаём таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Получение сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Эндпоинт для создания напоминания
@app.post("/reminders", response_model=ReminderResponse)
def create_reminder(reminder: ReminderCreate, db: Session = Depends(get_db)):
    # Сохраняем в БД
    db_reminder = Reminder(
        title=reminder.title,
        description=reminder.description,
        date_time=reminder.date_time,
        notification_type=reminder.notification_type,
        user_email=reminder.user_email,
        device_token=reminder.device_token,
    )
    db.add(db_reminder)
    db.commit()
    db.refresh(db_reminder)

    # Отправляем в Сервис уведомлений (если он есть)
    notification_service_url = "http://notification-service/schedule"
    try:
        requests.post(notification_service_url, json=reminder.model_dump())
    except:
        print("Сервис уведомлений недоступен")

    return db_reminder

# Получить все напоминания
@app.get("/reminders", response_model=list[ReminderResponse])
def get_reminders(db: Session = Depends(get_db)):
    return db.query(Reminder).all()

# Удалить напоминание
@app.delete("/reminders/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Напоминание не найдено")
    db.delete(reminder)
    db.commit()
    return {"status": "ok"}

# это я что-то новенькое добавил (корневой эндпоинт)
@app.get("/")
def home():
    return {"message": "Go to /docs for API documentation"}