# backend/database.py

from sqlmodel import create_engine, Session, SQLModel
from typing import Generator
import os

# --- THÊM DÒNG IMPORT TẤT CẢ CÁC MODEL CỦA BẠN TẠI ĐÂY ---
from backend.models import (
    User,
    Customer,
    Product,
    Invoice,
    InvoiceDetail,
    ProductPriceHistory # Thêm bất kỳ model nào khác bạn có vào đây
)

# THAY ĐỔI DÒNG DATABASE_URL NÀY ĐỂ TRỎ ĐẾN SUPABASE TRANSACTION POOLER
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.izulhxhucaucqgfdxdwk:Baochau@2024@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"
)

# Tạo engine cho PostgreSQL
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Tạo tất cả các bảng trong cơ sở dữ liệu dựa trên các mô hình SQLModel."""
    print("Attempting to create database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created or already exist.")

def get_session() -> Generator[Session, None, None]:
    """Dependency để lấy một phiên làm việc (session) với cơ sở dữ liệu."""
    with Session(engine) as session:
        yield session
