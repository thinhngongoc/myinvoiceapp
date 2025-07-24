from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import os
from datetime import date, timedelta
from sqlmodel import Session, select
from typing import Optional, Union

# Import các modules backend của bạn
from backend import database, models, schemas, auth, crud
from backend.routers import customers, products, invoices, reports, users

# --- BẮT ĐẦU CẤU HÌNH APP CHÍNH THỨC (CHỈ DUY NHẤT MỘT LẦN) ---
app = FastAPI()

# Cấu hình StaticFiles cho thư mục "static"
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cấu hình Jinja2Templates cho thư mục "templates"
templates = Jinja2Templates(directory="templates", extensions=["jinja2.ext.do"])

# Định nghĩa SECRET_KEY an toàn hơn
# QUAN TRỌNG: Hãy thay thế "mot_khoa_bi_mat_rat_manh_va_can_thay_doi_ngay_lap_tuc_abcxyz123"
# bằng một khóa bí mật mạnh, được tạo ngẫu nhiên!
# Bạn có thể dùng lệnh `python -c "import secrets; print(secrets.token_hex(32))"` để tạo.
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "mot_khoa_bi_mat_rat_manh_va_can_thay_doi_ngay_lap_tuc_abcxyz123")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Include các router từ thư mục backend/routers
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(invoices.router)
app.include_router(reports.router)
app.include_router(users.router)

# --- HÀM ON_STARTUP CỦA BẠN (CHỈ XUẤT HIỆN MỘT LẦN VÀ TRƯỚC CÁC ROUTE CỦA APP) ---
@app.on_event("startup")
def on_startup():
    print("--- Running on_startup event ---")
    try:
        database.create_db_and_tables()
        print("--- database.create_db_and_tables() completed ---")

        session_generator = database.get_session()
        session = None
        try:
            session = next(session_generator)

            # Biến cờ để kiểm tra xem có thay đổi nào cần commit không
            changes_made = False

            # 1. Tạo tài khoản admin
            if not crud.get_user_by_username(session, "admin"):
                print("Admin user 'admin' not found, attempting to create...")
                try:
                    # crud.create_user giờ không commit, chỉ add vào session
                    crud.create_user(session, schemas.UserCreate(username="admin", password="0936266648"), is_admin=True)
                    print("Admin user 'admin' added to session.")
                    changes_made = True
                except IntegrityError:
                    print("Admin user 'admin' already exists (IntegrityError).")
                    # Không cần rollback ở đây vì chưa commit
                except Exception as e:
                    print(f"Error adding admin user 'admin' to session: {e}")
                    import traceback
                    traceback.print_exc()

            else:
                print("Admin user 'admin' already exists.")

            # 2. Tạo tài khoản ketoan1
            if not crud.get_user_by_username(session, "ketoan1"):
                print("User 'ketoan1' not found, attempting to create...")
                try:
                    # crud.create_user giờ không commit, chỉ add vào session
                    crud.create_user(session, schemas.UserCreate(username="ketoan1", password="123456a@"), is_admin=False)
                    print("User 'ketoan1' added to session.")
                    changes_made = True
                except IntegrityError:
                    print("User 'ketoan1' already exists (IntegrityError).")
                except Exception as e:
                    print(f"Error adding user 'ketoan1' to session: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("User 'ketoan1' already exists.")

            # 3. Tạo tài khoản ketoan2
            if not crud.get_user_by_username(session, "ketoan2"):
                print("User 'ketoan2' not found, attempting to create...")
                try:
                    # crud.create_user giờ không commit, chỉ add vào session
                    crud.create_user(session, schemas.UserCreate(username="ketoan2", password="123456a@"), is_admin=False)
                    print("User 'ketoan2' added to session.")
                    changes_made = True
                except IntegrityError:
                    print("User 'ketoan2' already exists (IntegrityError).")
                except Exception as e:
                    print(f"Error adding user 'ketoan2' to session: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("User 'ketoan2' already exists.")

            # THỰC HIỆN COMMIT CUỐI CÙNG NẾU CÓ THAY ĐỔI
            if changes_made:
                try:
                    session.commit()
                    print("All initial users committed successfully.")
                except Exception as e:
                    session.rollback() # Rollback nếu commit cuối cùng thất bại
                    print(f"Error during final commit of initial users: {e} (rolled back)")
                    import traceback
                    traceback.print_exc()
            else:
                print("No new users to commit.")

        except Exception as e:
            print(f"!!! CRITICAL ERROR DURING ON_STARTUP SESSION MANAGEMENT: {e}")
            import traceback
            traceback.print_exc()
            # Đảm bảo rollback nếu có lỗi lớn không được bắt ở trên
            if session:
                session.rollback()
                print("Session rolled back due to critical error.")
        finally:
            if session:
                try:
                    session.close()
                except Exception as e:
                    print(f"Error closing session in on_startup finally block: {e}")
            try:
                session_generator.close()
            except StopIteration:
                pass
            except Exception as e:
                print(f"Error during session generator cleanup in on_startup finally block: {e}")

    except Exception as e:
        print(f"!!! CRITICAL ERROR IN ON_STARTUP: {e}")
        import traceback
        traceback.print_exc()
        
# --- Authentication API Endpoints (cần được đặt sau cấu hình app) ---
@app.get("/forgot-password-page", response_class=HTMLResponse, summary="Forgot Password Page")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.get("/reset-password-page", response_class=HTMLResponse, summary="Reset Password Page")
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse("reset_password.html", {"request": request, "token": token})
    
@app.post("/login", response_model=schemas.Token, summary="API Login Endpoint")
async def api_login_for_access_token(
    user_data: schemas.UserLogin,
    request: Request,
    db: Session = Depends(database.get_session)
):
    # Chuyển đổi username từ input thành chữ thường trước khi tìm kiếm
    # Điều này khớp với cách bạn lưu và tìm kiếm trong crud.py
    user = crud.get_user_by_username(db, user_data.username.lower()) # <-- THÊM .lower() Ở ĐÂY
    
    if not user or not auth.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không hợp lệ",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tài khoản của bạn đã bị vô hiệu hóa."
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    request.session['access_token'] = access_token
    request.session['token_type'] = "bearer"
    request.session['username'] = user.username

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/logout", summary="Logout user")
async def logout(request: Request):
    request.session.pop('access_token', None)
    request.session.pop('token_type', None)
    request.session.pop('username', None)
    request.session.pop('is_admin', None)
    
    request.session['flash_message'] = "Bạn đã đăng xuất."
    request.session['flash_category'] = 'info'
    
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)


# CÁC ROUTE HTML ĐƯỢC BẢO VỆ
@app.get("/", response_class=HTMLResponse)
async def read_root(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user})


@app.get("/customers-page", response_class=HTMLResponse)
async def customers_page(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    return templates.TemplateResponse("customers.html", {"request": request, "current_user": current_user})

@app.get("/products-page", response_class=HTMLResponse)
async def products_page(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    return templates.TemplateResponse("products.html", {"request": request, "current_user": current_user})

@app.get("/invoices-page", response_class=HTMLResponse)
async def invoices_page(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    return templates.TemplateResponse("invoices.html", {"request": request, "current_user": current_user})

@app.get("/create-invoice-page", response_class=HTMLResponse)
async def create_invoice_page(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    today_iso = date.today().isoformat()
    return templates.TemplateResponse("create_invoice.html", {"request": request, "current_user": current_user, "today": today_iso})
    
@app.get("/reports-page", response_class=HTMLResponse, summary="Reports Page")
async def reports_page(
    request: Request,
    current_user_or_redirect: Union[models.User, RedirectResponse] = Depends(auth.get_current_user_for_html_pages)
):
    if isinstance(current_user_or_redirect, RedirectResponse):
        return current_user_or_redirect
    current_user = current_user_or_redirect
    return templates.TemplateResponse("reports-page.html", {"request": request, "now": date.today(), "current_user": current_user})

@app.get("/admin-dashboard", response_class=HTMLResponse, summary="Admin Dashboard Page")
async def admin_dashboard_page(
    request: Request,
    current_user: models.User = Depends(auth.admin_required)
):
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "current_user": current_user})

@app.post("/users/", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED, summary="Create new user (Admin only)")
async def create_new_user(
    user_create: schemas.UserCreate,
    db: Session = Depends(database.get_session),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền tạo người dùng mới."
        )

    db_user = crud.get_user_by_username(db, user_create.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Tên người dùng đã tồn tại")
    
    return crud.create_user(db=db, user_create=user_create, is_admin=False)


@app.get("/login-page", response_class=HTMLResponse, summary="Login Page")
async def login_page_route(request: Request):
    # Bạn có thể thêm logic ở đây nếu muốn kiểm tra session trước khi hiển thị trang login
    # Ví dụ: nếu đã đăng nhập, chuyển hướng về trang chính
    if request.session.get('access_token'):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("login.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)