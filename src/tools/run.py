#!/usr/bin/env python3
"""
Скрипт управления проектом Rope Shop (Local & Prod helper).
Запуск:
    python run.py          (по умолчанию: start)
    python run.py start    (генерация .env при необходимости, docker compose up)
    python run.py stop     (docker compose down)
    python run.py check    (проверка доступности API и фронтенда)
"""
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Корень проекта
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
EXAMPLE_ENV = ROOT_DIR / ".env.local.example"
if not EXAMPLE_ENV.exists():
    EXAMPLE_ENV = ROOT_DIR / ".example.env"


def generate_secret(nbytes: int = 32) -> str:
    """Генерация надежного случайного ключа."""
    return secrets.token_hex(nbytes)


def ensure_env_file():
    """Создает backend/.env из шаблона, если он отсутствует, подставляя безопасные секреты."""
    if ENV_FILE.exists():
        return False

    if not EXAMPLE_ENV.exists():
        print(f"[!] Ошибка: Не найден шаблон окружения: {EXAMPLE_ENV}")
        sys.exit(1)

    print("[*] Создание файла конфигурации backend/.env...")
    content = EXAMPLE_ENV.read_text(encoding="utf-8")

    # Генерируем уникальные пароли
    secret_key = generate_secret(32)
    db_password = generate_secret(16)
    admin_password = generate_secret(12)

    # Подставляем вместо заглушек
    content = (
        content.replace("__SECRET_KEY__", secret_key)
        .replace("__DB_PASSWORD__", db_password)
        .replace("__ADMIN_PASSWORD__", admin_password)
        .replace("your_secret_key_here", secret_key)
        .replace("your_db_password", db_password)
        .replace("your_secure_admin_password_here", admin_password)
    )

    ENV_FILE.write_text(content, encoding="utf-8")

    # Сохраняем пароль админа в понятный файл для заказчика
    creds_file = ROOT_DIR / "ADMIN_CREDENTIALS.txt"
    creds_content = (
        "==============================================\n"
        "      ROPE SHOP - ДАННЫЕ АДМИНИСТРАТОРА       \n"
        "==============================================\n\n"
        "Адрес админ-панели: http://localhost:8080/admin/\n"
        "Логин:              admin\n"
        f"Пароль:             {admin_password}\n\n"
        "Внимание: не передавайте этот файл третьим лицам.\n"
    )
    creds_file.write_text(creds_content, encoding="utf-8")

    print(f"[+] Файл .env успешно создан!")
    print(f"[+] Учетные данные админа сохранены в: {creds_file.name}")
    return True


def run_cmd(cmd: list[str], check: bool = True):
    """Выполнение системной команды."""
    try:
        return subprocess.run(cmd, cwd=str(ROOT_DIR), check=check)
    except subprocess.CalledProcessError as e:
        print(f"[!] Ошибка выполнения команды: {' '.join(cmd)}")
        sys.exit(e.returncode)


def check_docker():
    """Проверка, запущен ли Docker daemon."""
    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        print("\n" + "=" * 50)
        print("[!] ОШИБКА: Docker не запущен!")
        print("Пожалуйста, запустите Docker Desktop и повторите попытку.")
        print("=" * 50 + "\n")
        sys.exit(1)


def healthcheck(urls: list[str], timeout: int = 30):
    """Ожидание доступности сервисов по HTTP."""
    print("[*] Проверка доступности сервисов...")
    start_time = time.time()
    for path in urls:
        url = f"http://127.0.0.1:8080{path}"
        success = False
        while time.time() - start_time < timeout:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status == 200:
                        success = True
                        break
            except Exception:
                time.sleep(1.5)
        if not success:
            print(f"[!] Внимание: Эндпоинт {url} пока не ответил 200 OK.")


def start():
    """Запуск стека контейнеров."""
    check_docker()
    ensure_env_file()

    print("[*] Сборка и запуск контейнеров...")
    run_cmd(["docker", "compose", "up", "-d", "--build", "--wait"])

    # Перезапуск nginx, чтобы применились свежие конфиги/dns
    subprocess.run(["docker", "compose", "restart", "nginx"], cwd=str(ROOT_DIR), stdout=subprocess.DEVNULL)

    healthcheck(["/", "/api/products", "/api/configurator_settings"])

    print("\n" + "=" * 55)
    print(" [✓] ПРОЕКТ УСПЕШНО ЗАПУЩЕН!")
    print("=" * 55)
    print("  • Главная страница: http://localhost:8080")
    print("  • Панель админа:    http://localhost:8080/admin/")
    print("  • Документация API: http://localhost:8018/docs")
    print("=" * 55 + "\n")


def stop():
    """Остановка стека."""
    print("[*] Остановка контейнеров...")
    run_cmd(["docker", "compose", "down"])
    print("[✓] Проект остановлен.")


if __name__ == "__main__":
    action = sys.argv[1].lower() if len(sys.argv) > 1 else "start"
    if action in ("start", "up"):
        start()
    elif action in ("stop", "down"):
        stop()
    elif action in ("check", "health"):
        healthcheck(["/", "/api/products", "/api/configurator_settings"])
    else:
        print(f"Неизвестная команда: {action}. Доступны: start, stop, check")