# Bao cao Quan tri Du an & Lot trinh Sprint - Tuan 5

Bao cao duoc thuc hien boi **Do Hoang Long (Project Manager & DevOps Specialist)**.

## 1. Phan chia Vai tro trong Du an (Scrum Roles)
Du an phat trien he thong Discord Bot duoc van hanh theo quy trinh Agile/Scrum voi cac vai tro:
* **Product Owner & Backend Lead:** Tran Duc Manh (`POWER4392`) - Thiet ke database, lap trinh REST API Backend.
* **Scrum Master & PM/DevOps:** Do Hoang Long (`Long432`) - Dieu phoi Sprint, trien khai he thong len Render Cloud.
* **UI/UX & Content Designer:** Tong Xuan Nghia (`hendrix810`) - Thiet ke giao dien Web Dashboard, GUI, embeds va content.
* **AI/ML Developer:** Nguyen Duc Duy (`duynguyen1012`) - Phien ban AI Chatbot, chong spam.
* **QA & Security Analyst:** Mai Van Viet (`vanviet2k6-creator`) - Kiem thu QA va danh gia bao mat.

## 2. Ke hoach va Phan cong cac Sprint (Sprint Backlog & Assignees)
Du an chia lam 5 Sprint chinh thuc voi phan cong nhiem vu chi tiet nhu sau:

* **Sprint 1 (Tuan 1):** Phan tich yeu cau, khoi tao repository va cau truc DB SQLite.
  * **Tran Duc Manh:** Khoi tao main core bot, event handler va setup database connection class.
  * **Do Hoang Long:** Khoi tao GitHub repo, quan tri tien do va cac vai tro du an.
  * **Nguyen Duc Duy:** Thiet ke regex scam va thuat toan anti-spam.
  * **Tong Xuan Nghia:** Phac thao cau truc embeds va kịch ban command line.
  * **Mai Van Viet:** Xay dung test plan ban dau cho he thong.

* **Sprint 2 (Tuan 2):** Xay dung tinh nang Discord Cog co ban (Moderation, Welcome, Admin GUI local).
  * **Tran Duc Manh:** Xay dung Moderation Cogs (Kick, Ban, Mute, Clear), Utilities Cogs (Ticket), Music Player base.
  * **Nguyen Duc Duy:** Viet Economy & Leveling Cogs, Social media crawler system (YouTube, TikTok, Reddit).
  * **Tong Xuan Nghia:** Thiet ke GUI admin desktop bang `customtkinter` (setting_gui.py).
  * **Do Hoang Long:** Cấu hình CI/CD workflow, set up global config loader.
  * **Mai Van Viet:** Viet test cases local, setup file configuration template.

* **Sprint 3 (Tuan 3):** Tich hop AI Chatbot Gemini, xay dung REST API cho dashboard, trien khai cloud deployment.
  * **Nguyen Duc Duy:** Tich hop Gemini SDK, prompt engineering, anti-spam sliding window cho AI chatbot.
  * **Tong Xuan Nghia:** Phac thao layout Web Dashboard, structure embeds.
  * **Tran Duc Manh:** Xay dung REST API endpoints backend, support parameters query.
  * **Do Hoang Long:** Trien khai code len Render Cloud hosting, cloud database Neon PostgreSQL.
  * **Mai Van Viet:** Thiet lap test cases kiem thu black-box, white-box cho AI chatbot va REST API.

* **Sprint 4 (Tuan 4):** Nang cap AI Chatbot, hoan thien Web Dashboard va bao mat QA.
  * **Tong Xuan Nghia (Issue #31):** Lap trinh UI/UX Web Dashboard, HTML/CSS/JS frontend dark mode.
  * **Tran Duc Manh (Issue #32):** Backend endpoints cho dashboard, nang cap chat history database.
  * **Do Hoang Long (Issue #33):** Health monitoring check endpoint `/health`, devops uptime check.
  * **Mai Van Viet (Issue #34):** Trien khai CORS middleware, rate limiter, security audit.
  * **Nguyen Duc Duy (Issue #35):** AI Vision, database token stats counter analytics.

* **Sprint 5.1 (Tuan 5 - Phan 1):** Nang cap AI Vision, RAG, Web Dashboard analytics & CI/CD workflow.
  * **Nguyen Duc Duy (Issue #42):** Nang cap AI Vision, basic RAG, lay token usage counter.
  * **Tran Duc Manh (Issue #43):** Toi uu database pool, WAL mode, API endpoint cho reaction roles.
  * **Mai Van Viet (Issue #44):** Thiet lap integration tests, stress test va load tests.
  * **Tong Xuan Nghia (Issue #45):** Giao dien Web Dashboard dynamic voi Chart.js ve token stats va danh sach Reaction Roles.
  * **Do Hoang Long (Issue #46):** Setup CI/CD workflow, auto deploy len Render Cloud.

* **Sprint 5.2 (Tuan 5 - Phan 2):** Kiem thu tong the, sua loi, hoan thien tai lieu SDD va phat hanh Release 0.1.0.
  * **Tran Duc Manh (Issue #51):** Sua cac loi ve DB lock, review va merge code tu cac nhanh tinh nang.
  * **Do Hoang Long (Issue #52):** Hop nhat code on dinh vao nhanh `main`, gan tag release `v0.1.0`, verify he thong tren Render Cloud.
  * **Nguyen Duc Duy (Issue #53):** Kiem tra an toan token Gemini, error handling cho AI Vision.
  * **Tong Xuan Nghia (Issue #54):** Hoan thien tai lieu dac ta Use Case va standardizing diagrams trong SDD.md.
  * **Mai Van Viet (Issue #55):** Kiem thu dong goi load_test tren cloud, ky duyet release chat luong bot truoc khi ban giao.

## 3. Bang quan ly rui ro (Risk Management Matrix)
| Rui ro | Muc do anh huong | Ke hoach khac phuc |
| --- | --- | --- |
| Lo API key hoac Token Bot Discord | Rat cao (High) | Su dung `.env` de cach ly bien moi truong, update `.gitignore` khong push file nhay cam. |
| Co so du lieu local SQLite bi mat khi deploy cloud | Trung binh (Medium) | Trien khai Neon Cloud PostgreSQL de dong bo du lieu dong. |
| Call limit / Over rate limit tu Gemini API | Thap (Low) | Cai dat co che chong Spam (Sliding Window) cua Duy de gioi han luot hoi bot. |
