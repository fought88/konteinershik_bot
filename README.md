
# Контейнерщик Бот

## Что делает бот:
- Собирает заявки от клиентов
- Сохраняет в Google Sheets
- Присылает уведомления администратору

## Как запустить:
1. Установи зависимости:
```
pip install -r requirements.txt
```

2. Укажи свой токен и ID в `config.py`

3. Замени файл `google_credentials.json` на свой из Google Cloud Console

4. Запусти бота:
```
python bot.py
```

## Интеграция Google Sheets
- Создай таблицу с названием "Konteinershik Leads"
- Подключи сервисный аккаунт Google и дай доступ таблице
