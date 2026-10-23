\# LMS API



REST API для системи керування навчальним контентом.



\## Технології



\- Python 3.12+

\- FastAPI

\- PostgreSQL

\- SQLAlchemy 2

\- Alembic

\- JWT

\- Docker Compose

\- Pytest



\## 1. Локальний запуск



Створіть віртуальне середовище:



&#x20;   python -m venv .venv



Linux/macOS:



&#x20;   source .venv/bin/activate



Windows PowerShell:



&#x20;   .venv\\Scripts\\Activate.ps1



Встановіть залежності:



&#x20;   pip install -e ".\[dev]"



Запустіть PostgreSQL і створіть базу lms.

Налаштуйте .env.development.



Linux/macOS:



&#x20;   export APP\_ENV=development



Windows PowerShell:



&#x20;   $env:APP\_ENV = "development"



Створіть початкову міграцію:



&#x20;   alembic revision --autogenerate -m "initial schema"



Перевірте файл міграції, а потім застосуйте її:



&#x20;   alembic upgrade head



Запустіть API:



&#x20;   uvicorn app.main:app --app-dir src --reload



Адреси:



\- API: http://localhost:8000

\- Swagger: http://localhost:8000/docs

\- Health: http://localhost:8000/health



\## 2. Запуск у Docker



Зберіть і запустіть сервіси:



&#x20;   docker compose up --build -d



Створіть початкову міграцію, якщо її ще немає:



&#x20;   docker compose exec api alembic revision --autogenerate -m "initial schema"



Застосуйте міграції:



&#x20;   docker compose exec api alembic upgrade head



Перегляньте логи:



&#x20;   docker compose logs -f api



Зупиніть сервіси:



&#x20;   docker compose down



Щоб видалити також дані бази (ОБЕРЕЖНО):



&#x20;   docker compose down -v



\## 3. Development



&#x20;   export APP\_ENV=development

&#x20;   uvicorn app.main:app --app-dir src --reload



Для локального запуску PostgreSQL має бути доступний за адресою,

вказаною в DATABASE\_URL.



\## 4. Test



Налаштуйте окрему базу lms\_test і змінні .env.test.



&#x20;   export APP\_ENV=test

&#x20;   alembic upgrade head

&#x20;   pytest -q



\## 5. Production



Перед запуском:



1\. Створіть окрему production-базу PostgreSQL.

2\. Передайте секрети через менеджер секретів або середовище виконання.

3\. Згенеруйте випадковий JWT\_SECRET\_KEY.

4\. Вимкніть DEBUG.

5\. Налаштуйте HTTPS, CORS і резервне копіювання бази.

6\. Перевірте та застосуйте міграції контрольовано.

7\. Запустіть сервер без --reload.



Приклад:



&#x20;   export APP\_ENV=production

&#x20;   alembic upgrade head

&#x20;   uvicorn app.main:app --host 0.0.0.0 --port 8000



Не використовуйте development/test секрети в production.



\## Основні маршрути



\- POST /api/v1/auth/register

\- POST /api/v1/auth/login

\- GET  /api/v1/auth/me

\- GET  /api/v1/courses

\- POST /api/v1/courses

\- GET  /api/v1/courses/{course\_id}

\- PATCH /api/v1/courses/{course\_id}

\- DELETE /api/v1/courses/{course\_id}

\- GET  /api/v1/courses/{course\_id}/lessons

\- POST /api/v1/courses/{course\_id}/lessons

\- PATCH /api/v1/lessons/{lesson\_id}

\- DELETE /api/v1/lessons/{lesson\_id}

\- POST /api/v1/enrollments

\- GET  /api/v1/enrollments/me

