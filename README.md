# API Rope Shop

Backend REST API для интернет-магазина по продаже верёвок, конфигураций изделий и услуг сращивания (splicing).

## Стек технологий
- **Язык**: Python 3.12+
- **Фреймворк**: FastAPI, Pydantic v2
- **База данных**: PostgreSQL, SQLAlchemy 2.0 (asyncpg)
- **Миграции**: Alembic
- **Тестирование**: Pytest, pytest-asyncio
- **Контейнеризация**: Docker, Docker Compose

---

## Быстрый запуск (Docker)

### 1. Подготовка переменных окружения
Скопируйте шаблон переменных окружения:
```bash
cp .example.env .env
```
> **Важно:** при запуске в Docker убедитесь, что в `.env` указано `DB_HOST=postgres`. При локальном запуске вне контейнера используйте `DB_HOST=localhost`.

### 2. Запуск контейнеров
Соберите и запустите сервисы:
```bash
docker compose up -d --build
```
Сервис API запустится на порту `8018`.

### 3. Инициализация базы данных
Для создания структуры БД выберите один из вариантов:

- **Вариант 1 (рекомендуемый) — применение миграций Alembic:**
  ```bash
  docker compose exec backend_rope_shopo alembic upgrade head
  ```
  *(или локально: `alembic upgrade head`)*

- **Вариант 2 — запуск скрипта создания БД и таблиц:**
  ```bash
  docker compose exec backend_rope_shopo python -m src.tools.creating_db
  ```
  *(или локально: `python -m src.tools.creating_db`)*

### 4. Заполнение базы данных тестовыми данными (опционально)
Для наполнения БД демонстрационными/тестовыми данными выполните:
```bash
docker compose exec backend_rope_shopo python -m src.tools.create_test_data
```
*(или локально: `python -m src.tools.create_test_data`)*

---

## Документация API
После запуска интерактивная документация доступна по адресам:
- **Swagger UI**: [http://localhost:8018/docs](http://localhost:8018/docs)
- **ReDoc**: [http://localhost:8018/redoc](http://localhost:8018/redoc)

---

## Тестирование
Для запуска тестов подготовьте тестовое окружение:
```bash
cp .example.test.env .test.env
```
Запуск тестов:
```bash
pytest
```
