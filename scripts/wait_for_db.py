import os
import sys
import time

import psycopg2
from django.db import connections
from django.db.utils import OperationalError


def wait_for_db():
    """Wait for database to be ready"""
    max_retries = 30
    retry_delay = 2

    db_config = {
        "dbname": os.environ.get("POSTGRES_DB", "habitflow_db"),
        "user": os.environ.get("POSTGRES_USER", "habitflow_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", "secure_password_123"),
        "host": os.environ.get("POSTGRES_HOST", "db"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }

    print("Waiting for PostgreSQL database...")

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(**db_config)
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"  Attempt {i + 1}/{max_retries}: {str(e)[:50]}...")
                time.sleep(retry_delay)
            else:
                print(f"❌ PostgreSQL not ready after {max_retries} attempts")
                return False

    return False


if __name__ == "__main__":
    sys.exit(0 if wait_for_db() else 1)
