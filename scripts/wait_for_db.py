"""
Универсальный скрипт проверки PostgreSQL
Работает локально и с удаленной ВМ
"""

import os
import socket
import sys
import time


def check_port(host: str, port: int, timeout: int = 5) -> bool:
    """Проверяет доступность порта"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def check_postgresql():
    """Основная проверка PostgreSQL"""
    try:
        import psycopg2
        from psycopg2 import OperationalError
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: poetry install")
        return False

    # Определяем хост
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = int(os.environ.get("POSTGRES_PORT", "5432"))

    print(f"Checking PostgreSQL at {host}:{port}")

    # Сначала проверяем порт
    if not check_port(host, port):
        print(f"ERROR: Cannot connect to {host}:{port}")
        print("Possible solutions:")
        print("  1. Start PostgreSQL: docker-compose up -d postgres")
        print(f"  2. Check if {host} is reachable")
        print(f"  3. Verify port {port} is open")
        return False

    # Если порт открыт, пробуем подключиться
    config = {
        "host": host,
        "port": port,
        "dbname": os.environ.get("POSTGRES_DB", "postgres"),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
    }

    for attempt in range(1, 6):
        try:
            conn = psycopg2.connect(**config)
            conn.close()
            print("SUCCESS: PostgreSQL connection established")
            return True
        except Exception as e:
            if attempt < 5:
                print(f"  Attempt {attempt}/5: {e}")
                time.sleep(2)
            else:
                print(f"FAILED: {e}")
                return False

    return False


if __name__ == "__main__":
    sys.exit(0 if check_postgresql() else 1)
