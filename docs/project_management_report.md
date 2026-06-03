# Bao cao Quan tri Du an & Lot trinh Sprint - Tuan 3

Bao cao duoc thuc hien boi **Do Hoang Long (Project Manager & DevOps Specialist)**.

## 1. Phan chia Vai tro trong Du an (Scrum Roles)
Du an phat trien he thong Discord Bot duoc van hanh theo quy trinh Agile/Scrum voi cac vai tro:
* **Product Owner & Backend Lead:** Tran Duc Manh (`POWER4392`) - Thiet ke database, lap trinh REST API Backend.
* **Scrum Master & PM/DevOps:** Do Hoang Long (`Long432`) - Dieu phoi Sprint, trien khai he thong len Render Cloud.
* **AI/ML Developer:** Nguyen Duc Duy (`duynguyen1012`) - Phien ban AI Chatbot, chong spam.
* **QA & Security Analyst:** Mai Van Viet (`vanviet2k6-creator`) - Kiem thu QA va danh gia bao mat.

## 2. Ke hoach cac Sprint (Sprint Backlog & Roadmap)
Du an chia lam 3 Sprint chinh thuc:
* **Sprint 1 (Tuan 1):** Phantich yeu cau, khoi tao repository va cau truc DB SQLite.
* **Sprint 2 (Tuan 2):** Xay dung tinh nang Discord Cog co ban (Moderation, Welcome, Admin GUI local).
* **Sprint 3 (Tuan 3):** Tich hop AI Chatbot Gemini, xay dung REST API cho dashboard, trien khai cloud deployment.

## 3. Bang quan ly rui ro (Risk Management Matrix)
| Rui ro | Muc do anh huong | Ke hoach khac phuc |
| --- | --- | --- |
| Lo API key hoac Token Bot Discord | Rat cao (High) | Su dung `.env` de cach ly bien moi truong, update `.gitignore` khong push file nhay cam. |
| Co so du lieu local SQLite bi mat khi deploy cloud | Trung binh (Medium) | Trien khai Neon Cloud PostgreSQL de dong bo du lieu dong. |
| Call limit / Over rate limit tu Gemini API | Thap (Low) | Cai dat co che chong Spam (Sliding Window) cua Duy de gioi han luot hoi bot. |
