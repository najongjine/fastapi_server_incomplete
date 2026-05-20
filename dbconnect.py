import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()

"""
DB 에 접속하고난 객체를 퉤 뱉는놈
"""
def getConnect():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_table():
    """Create sample memo tables if they do not exist."""
    title_sql = """
    CREATE TABLE IF NOT EXISTS t_tile(
    id SERIAL PRIMARY KEY,
    title VARCHAR,
    subtitle VARCHAR,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """
    contents_sql = """
    CREATE TABLE IF NOT EXISTS t_item(
    id SERIAL PRIMARY KEY,
    content VARCHAR,
    img_url TEXT,
    price INT4 DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """
    # conn에 DB 접속해주는 전문가 넣어요
    conn=getConnect();
    try:
        with conn.cursor() as cursor:
            cursor.execute(title_sql)
            cursor.execute(contents_sql)
            # 영구 저장해. commit 이란거 안하면 지혼자 상상만 하고 끝
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return {"result": "success"}
