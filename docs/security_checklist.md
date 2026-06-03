# Bao cao Danh gia Security & QA Checklist - Tuan 3

Bao cao duoc thuc hien boi **Mai Van Viet (QA & Security Engineer)**.

## 1. Kich ban Kiem thu QA (Quality Assurance)
Cac test cases da duoc thiet lap va xac nhan chay thanh cong tren local:
* **TC-AI-01:** Phai hoi thong thuong qua mention bot hoac qua channel AI duoc cau hinh -> **DAT** (Bot phan hoi dung noi dung tu Gemini API).
* **TC-AI-02:** Xử lý ngoại lệ khi thiếu `GEMINI_API_KEY` -> **DAT** (Bot bao loi than thien, khong bi crash event loop).
* **TC-API-01:** Kiem tra Dashboard API endpoint `GET_DASHBOARD_STATS` -> **DAT** (Tra ve day du trang thai bot, latency, user_count, active_voice).

## 2. Danh gia An toan thong tin (Security Audit)
* **Bao mat Credential:** Da cach ly thanh cong file `cookies.txt` va `.env` ra khoi Git de tranh lo lot phien dang nhap Youtube va bot token.
* **Xac thuc API Dashboard:** Endpoint API yeu cau Header `X-API-Key` trung khop voi `API_SECRET` moi co quyen lay stats hoac sua doi cau hinh.
* **SQL Injection Prevention:** Su dung tham so hoa cau truy van (Parameterized Queries) trong adapter co so du lieu cho tat ca cac thao tac luu tru.
