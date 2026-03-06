UMKOVO v2 starter

Запуск (Windows):
1) python -m venv .venv
2) .venv\Scripts\activate
3) pip install -r requirements.txt
4) copy .env.example .env
5) Впиши BOT_TOKEN в .env
6) python -m src.main

Запуск (Linux/Mac):
1) python3 -m venv .venv
2) source .venv/bin/activate
3) pip install -r requirements.txt
4) cp .env.example .env
5) Впиши BOT_TOKEN в .env
6) python -m src.main

Важно:
- Запускать только как модуль: python -m src.main
- Импорты внутри проекта только через src.*