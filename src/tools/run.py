#!/usr/bin/env python3
"""
Скрипт управления проектом Rope Shop (Local & Prod helper).

Использование из корня проекта:
    python src/tools/run.py            (по умолчанию: запуск start)
    python src/tools/run.py start      (сборка и запуск контейнеров)
    python src/tools/run.py stop       (остановка контейнеров)
    python src/tools/run.py check      (проверка доступности сервисов)
    python src/tools/run.py migrate    (применение миграций Alembic)
    python src/tools/run.py seed       (наполнение тестовыми данными)

Флаги окружения (для start, stop, check, migrate, seed):
    --prod   — запуск production-стека (docker-compose.prod.yaml)
    --local  — запуск локального стека с фронтендом и nginx (docker-compose.local.yaml)
    (по умолчанию используется docker-compose.yaml)
"""
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Безопасная кодировка для консоли Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Корень проекта
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"
EXAMPLE_ENV = ROOT_DIR / ".env.local.example"
if not EXAMPLE_ENV.exists():
    EXAMPLE_ENV = ROOT_DIR / ".example.env"


def generate_secret(nbytes: int = 32) -> str:
    """Генерация надежного случайного ключа."""
    return secrets.token_hex(nbytes)


def is_port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """Быстрая проверка доступности TCP-порта."""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def ensure_env_file():
    """Создает .env из шаблона, если он отсутствует, подставляя безопасные секреты."""
    if ENV_FILE.exists():
        return False

    if not EXAMPLE_ENV.exists():
        print(f"[!] Ошибка: Не найден шаблон окружения: {EXAMPLE_ENV}")
        sys.exit(1)

    print("[*] Создание файла конфигурации .env из шаблона...")
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

    # Сохраняем пароль админа в понятный файл для разработчика/заказчика
    creds_file = ROOT_DIR / "ADMIN_CREDENTIALS.txt"
    creds_content = (
        "==============================================\n"
        "      ROPE SHOP - ДАННЫЕ АДМИНИСТРАТОРА       \n"
        "==============================================\n\n"
        "Адрес админ-панели (при запущенном фронтенде): http://localhost:8080/admin/ или http://localhost/admin/\n"
        "Документация API (Swagger UI):                http://localhost:8018/docs\n"
        "Логин:                                        admin\n"
        f"Пароль:                                       {admin_password}\n\n"
        "Внимание: не передавайте этот файл третьим лицам.\n"
    )
    creds_file.write_text(creds_content, encoding="utf-8")

    print("[+] Файл .env успешно создан!")
    print(f"[+] Учетные данные админа сохранены в: {creds_file.name}")
    return True


def run_cmd(cmd: list[str], check: bool = True):
    """Выполнение системной команды в корне проекта."""
    try:
        return subprocess.run(cmd, cwd=str(ROOT_DIR), check=check)
    except subprocess.CalledProcessError as e:
        print(f"[!] Ошибка выполнения команды: {' '.join(cmd)}")
        sys.exit(e.returncode)


def check_docker():
    """Проверка, установлен ли и запущен ли Docker daemon."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            print("\n" + "=" * 50)
            print("[!] ОШИБКА: Docker daemon не запущен!")
            print("Пожалуйста, запустите Docker Desktop и повторите попытку.")
            print("=" * 50 + "\n")
            sys.exit(1)
    except FileNotFoundError:
        print("\n" + "=" * 50)
        print("[!] ОШИБКА: Docker не установлен или не найден в PATH!")
        print("Пожалуйста, установите Docker Desktop и добавьте его в системные пути.")
        print("=" * 50 + "\n")
        sys.exit(1)


def get_compose_cmd(extra_args: list[str] | None = None) -> list[str]:
    """Формирует базовую команду docker compose с нужными -f файлами."""
    args = extra_args if extra_args is not None else sys.argv[1:]
    cmd = ["docker", "compose"]

    if "--prod" in args:
        cmd.extend(["-f", "docker-compose.prod.yaml"])
    elif "--local" in args:
        cmd.extend(["-f", "docker-compose.prod.yaml", "-f", "docker-compose.local.yaml"])
    else:
        compose_default = ROOT_DIR / "docker-compose.yaml"
        if compose_default.exists():
            cmd.extend(["-f", "docker-compose.yaml"])
    return cmd


def has_service(service_name: str, compose_base: list[str]) -> bool:
    """Проверяет, объявлен ли сервис в текущем compose-файле."""
    try:
        result = subprocess.run(
            [*compose_base, "config", "--services"],
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        services = [s.strip() for s in result.stdout.splitlines() if s.strip()]
        return service_name in services
    except Exception:
        return False


def get_active_service_info() -> tuple[str, list[str]]:
    """Возвращает базовый URL и тестовые маршруты в зависимости от открытого порта."""
    candidates = [
        (80, "http://127.0.0.1:80", ["/health", "/api/products", "/admin/"]),
        (8080, "http://127.0.0.1:8080", ["/health", "/api/products", "/admin/"]),
        (8018, "http://127.0.0.1:8018", ["/docs", "/products", "/configurator_settings"]),
    ]
    for port, base_url, paths in candidates:
        if is_port_open(port):
            return base_url, paths

    # Если порт пока не открыт, определяем по флагам вызова
    args = sys.argv[1:]
    if "--local" in args:
        return "http://127.0.0.1:8080", ["/health", "/api/products", "/admin/"]
    elif "--prod" in args:
        return "http://127.0.0.1:80", ["/health", "/api/products", "/admin/"]
    return "http://127.0.0.1:80", ["/health", "/api/products", "/admin/"]


def healthcheck(timeout: int = 30) -> bool:
    """Ожидание доступности сервисов по HTTP."""
    print("[*] Проверка доступности сервисов...")
    candidates = [
        (80, "http://127.0.0.1:80", ["/health", "/api/products", "/admin/"]),
        (8080, "http://127.0.0.1:8080", ["/health", "/api/products", "/admin/"]),
        (8018, "http://127.0.0.1:8018", ["/docs", "/products", "/configurator_settings"]),
    ]

    target = None
    start_time = time.time()
    while time.time() - start_time < timeout:
        for port, base_url, paths in candidates:
            if is_port_open(port):
                target = (base_url, paths)
                break
        if target:
            break
        time.sleep(1)

    if not target:
        print("[!] Внимание: Ни один из портов сервиса (8080, 80, 8018) не открыт.")
        print("    Для запуска проекта выполните: python src/tools/run.py start")
        return False

    base_url, paths = target
    all_ok = True
    for path in paths:
        url = f"{base_url}{path}"
        success = False
        path_start = time.time()
        while time.time() - path_start < 5:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status in (200, 301, 302, 404):
                        success = True
                        break
            except Exception:
                time.sleep(0.5)
        if success:
            print(f" [+] {url} доступен")
        else:
            print(f" [!] {url} пока не ответил 200 OK")
            all_ok = False
    return all_ok


def start():
    """Запуск стека контейнеров."""
    check_docker()
    ensure_env_file()
    compose_cmd = get_compose_cmd()

    desc = " ".join(compose_cmd[2:]) if len(compose_cmd) > 2 else "docker-compose.yaml"
    print(f"[*] Сборка и запуск контейнеров ({desc})...")
    run_cmd([*compose_cmd, "up", "-d", "--build", "--wait"])

    if has_service("nginx", compose_cmd):
        subprocess.run([*compose_cmd, "restart", "nginx"], cwd=str(ROOT_DIR), stdout=subprocess.DEVNULL)

    healthcheck(timeout=30)

    base_url, _ = get_active_service_info()
    print("\n" + "=" * 55)
    print(" [OK] ПРОЕКТ УСПЕШНО ЗАПУЩЕН!")
    print("=" * 55)
    if "8080" in base_url or "80" == base_url.split(":")[-1]:
        print(f"  * Главная страница (сайт): {base_url}")
        print(f"  * Каталог товаров:        {base_url}/catalog/")
        print(f"  * Панель администратора:  {base_url}/admin/")
        print(f"  * Документация API:       {base_url}/docs (или http://localhost:8018/docs)")
    else:
        print("  * Сервер API:             http://localhost:8018")
        print("  * Документация API:       http://localhost:8018/docs")
        print("  * ReDoc:                  http://localhost:8018/redoc")
    print("=" * 55 + "\n")


def stop():
    """Остановка стека контейнеров."""
    compose_cmd = get_compose_cmd()
    desc = " ".join(compose_cmd[2:]) if len(compose_cmd) > 2 else "docker-compose.yaml"
    print(f"[*] Остановка контейнеров ({desc})...")
    run_cmd([*compose_cmd, "down"])
    print("[+] Проект остановлен.")


def migrate():
    """Применение миграций базы данных (Alembic upgrade head)."""
    check_docker()
    compose_cmd = get_compose_cmd()
    print("[*] Применение миграций Alembic...")
    run_cmd([*compose_cmd, "exec", "backend_rope_shopo", "alembic", "upgrade", "head"])
    print("[+] Миграции успешно применены.")


def seed():
    """Наполнение базы данных тестовыми данными."""
    check_docker()
    compose_cmd = get_compose_cmd()
    print("[*] Генерация тестовых данных...")
    run_cmd([*compose_cmd, "exec", "backend_rope_shopo", "python", "-m", "src.tools.create_test_data"])
    print("[+] Тестовые данные успешно созданы.")


def print_help():
    """Вывод справочной информации."""
    print(
        "\nСкрипт управления проектом Rope Shop (Local & Prod helper)\n\n"
        "Использование:\n"
        "    python src/tools/run.py [КОМАНДА] [ФЛАГИ]\n\n"
        "Доступные команды:\n"
        "    start     — Сборка и запуск контейнеров (по умолчанию)\n"
        "    stop      — Остановка контейнеров\n"
        "    check     — Проверка доступности запущенных сервисов (healthcheck)\n"
        "    migrate   — Применение миграций Alembic в контейнере\n"
        "    seed      — Заполнение базы данных тестовыми данными\n"
        "    help      — Вывод этой справки\n\n"
        "Флаги окружения:\n"
        "    --prod    — Использовать стек docker-compose.prod.yaml\n"
        "    --local   — Использовать стек docker-compose.local.yaml с Nginx и фронтендом\n"
        "    (без флагов запускается стандартный docker-compose.yaml)\n"
    )


if __name__ == "__main__":
    raw_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    action = raw_args[0].lower() if raw_args else "start"

    if action in ("start", "up"):
        start()
    elif action in ("stop", "down"):
        stop()
    elif action in ("check", "health"):
        healthcheck(timeout=3)
    elif action in ("migrate", "upgrade"):
        migrate()
    elif action in ("seed", "test-data"):
        seed()
    elif action in ("help", "-h", "--help"):
        print_help()
    else:
        print(f"[!] Неизвестная команда: {action}")
        print_help()
        sys.exit(1)
