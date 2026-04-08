import os


TEST_DB_NAME = "swiswim_test"

_db_user = os.getenv("DB_USER", "user")
_db_password = os.getenv("DB_PASSWORD", "1234")
_db_host = os.getenv("DB_HOST", "db")
_db_port = os.getenv("DB_PORT", "5432")

TEST_DB_URL = f"postgresql+psycopg://{_db_user}:{_db_password}@{_db_host}:{_db_port}/{TEST_DB_NAME}"
