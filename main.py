import asyncio
import shutil
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg2.extras import RealDictCursor

from batch import batch_job
from dbconnect import create_table, getConnect


UPLOAD_DIR = Path("public/uploads")

# 서버 시작하면 실행하는 코드
@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    create_table()
    task = asyncio.create_task(batch_job())
    yield
    task.cancel()

# 서버 만드는 코드
app = FastAPI(lifespan=lifespan)
# 보안 해제 코드
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
def page():
    return FileResponse("pages/index.html")


@app.get("/upload")
def upload_page():
    return FileResponse("pages/upload.html")


@app.get("/select")
def select_page():
    return FileResponse("pages/select.html")


@app.get("/MY_TYPE.js")
def my_type_js():
    return FileResponse("pages/MY_TYPE.js", media_type="application/javascript")


@app.get("/api/title")
def get_title():
    # 과제. subtitle 칼럼 추가하기
    sql = """
    SELECT
    d.id,
    d.title
    FROM t_title as d
    ORDER BY d.id desc
    
    """
    conn = getConnect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()

            if row is None:
                return {"result": "success", "data": None}

            return {"result": "success", "data": dict(row)}
    finally:
        conn.close()
"""
인터넷 주소창으로 치고 들어갈수 있음.
보안에 취약.
"""
@app.get("/api/items")
def get_items():
    sql = """
    SELECT
    c.id,
    c.content,
    c.img_url,
    c.price
    FROM t_item as c
    ORDER BY c.id desc
    
    """
    conn = getConnect()
    try:
         with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()

            return {"result": "success", "data": [dict(row) for row in rows]}
    finally:
        conn.close()

"""
인터넷 주소창 치고 들어갈수 없음.
데이터는 body에 실려서 전달됨.
파일 업로드도 수행할수 있음
"""
@app.post("/api/add_title")
def add_title(
    title: str = Form(...),
    subtitle: str = Form(...),
):
    """
    %s 이건 SQL injection 방어 기법
    SQL injection: 사용자 입력창에 의도적으로 공격이나 데이터 탈취 가능한
    SQL 명령문을 입력하여 시스템이 오작동하거나, 데이터베이스 명령을 실행해서
    공격 받거나 데이터 탈취되는 공격
    """
    sql = """
    INSERT INTO t_title(title,subtitle)
    VALUES (%s, %s)
    RETURNING id, title, subtitle, created_at
    """
    conn = getConnect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, (title, subtitle))
            row = cursor.fetchone()
            conn.commit()
            return {"result": "success", "data": dict(row)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@app.post("/api/add_item")
def add_item(
    content: str = Form(...),
    img_url: Optional[str] = Form(None),
    price: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
):
    save_img_url = img_url

    if image and image.filename:
        ext = Path(image.filename).suffix
        filename = f"{uuid4().hex}{ext}"
        save_path = UPLOAD_DIR / filename
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        save_img_url = f"/public/uploads/{filename}"

    sql = """
    INSERT INTO t_item(content,img_url,price)
    VALUES(%s,%s,%s)
    RETURNING id, content, img_url, price, created_at
    """
    conn = getConnect()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(sql, (content, save_img_url, price))
            row = cursor.fetchone()
            conn.commit()
            return {"result": "success", "data": dict(row)}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

# 서버 실행하는게 어려운데, 서버 실행 명령어를 간단하게 만들어준다
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
