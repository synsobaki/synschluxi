# UMKOVO v2 starter

Телеграм-бот на Python.

## Быстрый запуск (Windows)

1. `python -m venv .venv`
2. `.venv\Scripts\activate`
3. `pip install -r requirements.txt`
4. `copy .env.example .env`
5. Укажи `BOT_TOKEN` и `ADMIN_ID` в файле `.env`
   - Если у тебя старый формат `ADMIN_IDS=[123456789]`, он тоже поддерживается.
6. `python -m src.main`

## Быстрый запуск (Linux/macOS)

1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `cp .env.example .env`
5. Укажи `BOT_TOKEN` и `ADMIN_ID` в файле `.env`
   - Если у тебя старый формат `ADMIN_IDS=[123456789]`, он тоже поддерживается.
6. `python -m src.main`

## Важно

- Запускать проект только как модуль: `python -m src.main`.
- Импорты внутри проекта использовать только через `src.*`.
