# Danh sach Test Cases kiem thu he thong - Tuan 3

| ID | Module / Tinh Nang | Muc dich kiem thu | Cac buoc thuc hien | Ket qua mong doi | Trang thai |
|---|---|---|---|---|---|
| TC-AI-01 | AI Chatbot | Kiem tra phan hoi thong thuong | Mention bot va hoi "Hello" | Bot tra loi tu nhien qua Gemini API | Cho thuc hien |
| TC-AI-02 | AI Chatbot | Kiem tra khi thieu API Key | Xoa GEMINI_API_KEY trong .env va nhan tin | Bot ghi log loi va khong crash | Cho thuc hien |
| TC-API-01 | API Server | Lay thong tin stats dashboard | Goi endpoint API voi action GET_DASHBOARD_STATS | Tra ve JSON chua status, ping va cogs | Cho thuc hien |
| TC-API-02 | API Server | Kiem tra X-API-Key sai | Goi endpoint voi key sai | Tra ve 401 Unauthorized | Cho thuc hien |
