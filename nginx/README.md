# Nginx Production Setup для API_rope_shop

Данная директория содержит готовую конфигурацию **Nginx** для развёртывания бэкенда в производственной среде (Production).

---

## Архитектура файлов

```
nginx/
├── nginx.conf                 # Глобальные настройки Nginx (Gzip, воркеры, буферы, Rate Limiting)
├── conf.d/
│   ├── app.conf               # Основной виртуальный хост (HTTPS, HTTP->HTTPS redirect, reverse proxy, /media/)
│   └── app.http.conf.example  # HTTP-only хост (для первичного запуска и генерации сертификата Certbot)
└── README.md                  # Данная инструкция
```

---

## Пошаговая инструкция первого развертывания на боевом сервере

### Шаг 1. Настройка домена и переменных окружения
1. Направьте DNS А-запись вашего домена (например, `api.your-domain.com`) на IP-адрес вашего сервера.
2. В файле `.env` на сервере убедитесь, что заданы боевые переменные (`DB_NAME`, `POSTGRES_PASSWORD`, `SECRET_KEY`, `BASE_DIR`, и т.д.).
3. В файле `nginx/conf.d/app.conf` замените `your-domain.com` на ваш реальный домен.

---

### Шаг 2. Первичный запуск (получение SSL-сертификата Let's Encrypt)

Для первого запуска (когда SSL-сертификаты ещё не созданы certbot'ом), временно активируйте HTTP-режим:

```bash
# 1. Временно копируем HTTP-конфиг
cp nginx/conf.d/app.http.conf.example nginx/conf.d/app.conf

# 2. Запускаем только Nginx и бэкенд
docker compose -f docker-compose.prod.yaml up -d nginx backend_rope_shopo

# 3. Выпускаем сертификат через Certbot (замените api.your-domain.com и почту):
docker compose -f docker-compose.prod.yaml run --rm certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  -d api.your-domain.com \
  --email admin@your-domain.com \
  --agree-tos \
  --no-eff-email
```

---

### Шаг 3. Включение боевого HTTPS

После успешного получения сертификатов верните боевой `app.conf`:

```bash
# 1. Восстановите боевой app.conf (с вашим доменом в путях ssl_certificate)
git checkout nginx/conf.d/app.conf

# 2. Запустите весь production-стек (включая certbot-демон для автообновления):
docker compose -f docker-compose.prod.yaml up -d

# 3. Проверьте валидность конфига Nginx:
docker compose -f docker-compose.prod.yaml exec nginx nginx -t

# 4. Перезагрузите Nginx без остановки сервиса:
docker compose -f docker-compose.prod.yaml exec nginx nginx -s reload
```

---

## Полезные команды для эксплуатации

* **Проверить синтаксис конфигов Nginx:**
  ```bash
  docker compose -f docker-compose.prod.yaml exec nginx nginx -t
  ```

* **Перезагрузить Nginx после правок (zero-downtime):**
  ```bash
  docker compose -f docker-compose.prod.yaml exec nginx nginx -s reload
  ```

* **Просмотр логов доступа и ошибок:**
  ```bash
  docker compose -f docker-compose.prod.yaml logs -f nginx
  ```

* **Тест обновления сертификатов (Dry Run):**
  ```bash
  docker compose -f docker-compose.prod.yaml run --rm certbot renew --dry-run
  ```

---

## Ключевые возможности данной конфигурации

1. **Раздача статики `/media/`**:
   - Картинки отдаются Nginx напрямую в обход Python (высокая скорость, нулевая нагрузка на FastAPI).
   - Заголовки кэширования браузера `Cache-Control: public, max-age=2592000` (30 дней).
   - Защита от запуска скриптов и доступа к скрытым файлам.

2. **Защита Uvicorn и Rate Limiting**:
   - `client_max_body_size 25M` защищает от переполнения памяти при upload файлов.
   - Nginx буферизует медленные соединения клиентов, защищая ASGI-сервер.
   - Заголовки `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` гарантируют корректную работу SlowAPI и логирования в FastAPI.

3. **Gzip-сжатие**:
   - Ответы каталога и конфигуратора в формате JSON сжимаются на лету, экономя трафик.

4. **Security Headers**:
   - `HSTS`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`, скрытие версии сервера (`server_tokens off;`).
