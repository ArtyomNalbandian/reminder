# Reminder Application Backend

Это бэкенд-часть приложения для создания напоминаний, состоящая из двух микросервисов:
1. Storage Service - сервис для хранения напоминаний
2. Notification Service - сервис для отправки уведомлений

## Предварительные требования

1. Docker и Docker Compose
2. Firebase проект (для Push-уведомлений)
3. Яндекс почта (для email-уведомлений)

## Настройка Firebase Cloud Messaging (FCM)

1. Создайте проект в [Firebase Console](https://console.firebase.google.com/)
2. Перейдите в настройки проекта (шестеренка) -> Сервисные аккаунты
3. Нажмите "Создать закрытый ключ" для Firebase Admin SDK
4. Сохраните полученный JSON-файл как `firebase-credentials.json` в корневой папке проекта
5. В Android-приложении:
   - Убедитесь, что `google-services.json` добавлен в папку `app/`
   - Проверьте, что FCM-токен успешно генерируется и отправляется на сервер
   - Проверьте реализацию `FirebaseMessagingService` и наличие notification channel

## Настройка Яндекс Почты

1. Создайте или используйте существующий аккаунт Яндекс Почты
2. Включите доступ к почте через внешние приложения:
   - Войдите в настройки почты
   - Перейдите в раздел "Безопасность"
   - Включите "Доступ к почтовому ящику с помощью почтовых клиентов"
   - Создайте пароль приложения
3. Сохраните email и пароль приложения для использования в конфигурации

## Конфигурация

1. Создайте файл `.env` в корневой папке проекта со следующим содержимым:
```env
SMTP_USERNAME=ваш_яндекс_email
SMTP_PASSWORD=пароль_приложения_яндекс
```

## Запуск приложения

1. Убедитесь, что файл `firebase-credentials.json` находится в корневой папке проекта
2. Запустите сервисы с помощью Docker Compose:
```bash
docker-compose up --build
```

3. Проверьте статус сервисов через health check endpoints:
   - Storage Service: http://localhost:8000/health
   - Notification Service: http://localhost:8001/health

## API Endpoints

### Storage Service (http://localhost:8000)

Swagger UI: http://localhost:8000/docs

Endpoints:
- POST /reminders/ - Создание нового напоминания
- GET /reminders/ - Получение списка всех напоминаний
- GET /reminders/{reminder_id} - Получение информации о конкретном напоминании
- DELETE /reminders/{reminder_id} - Отмена напоминания
- GET /health - Проверка состояния сервиса

### Notification Service (http://localhost:8001)

Swagger UI: http://localhost:8001/docs

Endpoints:
- POST /notifications/ - Создание нового уведомления (используется внутренне)
- DELETE /notifications/{notification_id} - Отмена уведомления (используется внутренне)
- GET /health - Проверка состояния сервиса

## Примеры использования

### Создание напоминания с Push-уведомлением

```bash
curl -X POST "http://localhost:8000/reminders/" \
-H "Content-Type: application/json" \
-d '{
  "text": "Тестовое напоминание",
  "notification_time": "2024-01-01T12:00:00",
  "notification_type": "fcm",
  "recipient": "FCM_TOKEN"
}'
```

### Создание напоминания с Email-уведомлением

```bash
curl -X POST "http://localhost:8000/reminders/" \
-H "Content-Type: application/json" \
-d '{
  "text": "Тестовое напоминание",
  "notification_time": "2024-01-01T12:00:00",
  "notification_type": "email",
  "recipient": "your.email@example.com"
}'
```

## Структура проекта

```
.
├── docker-compose.yml
├── firebase-credentials.json
├── storage-service/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       ├── models.py
│       ├── schemas.py
│       └── database.py
└── notification-service/
    ├── Dockerfile
    ├── requirements.txt
    └── app/
        ├── main.py
        ├── models.py
        ├── schemas.py
        ├── database.py
        └── notifications.py
```

## Troubleshooting

### FCM Push-уведомления не приходят

1. Проверьте валидность `firebase-credentials.json`:
   - Убедитесь, что файл содержит актуальные credentials
   - Проверьте, что проект в Firebase Console активен
   - Убедитесь, что у сервисного аккаунта есть необходимые права

2. Проверьте FCM-токен:
   - Токен должен быть актуальным (они могут обновляться)
   - Убедитесь, что токен корректно передается в API

3. Проверьте логи notification-service:
```bash
docker-compose logs notification-service
```

4. Проверьте Android-приложение:
   - Наличие правильного `google-services.json`
   - Корректность реализации `FirebaseMessagingService`
   - Наличие и настройку notification channel
   - Разрешения на уведомления в настройках приложения

### Проблемы с базой данных

1. Проверьте статус сервисов через health check endpoints
2. Проверьте логи сервисов:
```bash
docker-compose logs storage-service
docker-compose logs notification-service
```

3. При необходимости пересоздайте контейнеры:
```bash
docker-compose down -v
docker-compose up --build
``` 