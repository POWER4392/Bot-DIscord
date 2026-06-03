# Huong dan Trien khai He thong (Deployment Guide) - Tuan 3

Huong dan nay duoc thuc hien boi **Do Hoang Long (Project Manager & DevOps Specialist)**.

## 1. Trien khai Cloud (Render.com)
He thong su dung cau hinh Infrastructure-as-Code (IaC) thong qua file `render.yaml` de trien khai tu dong len Render:
* **Loai dich vu:** Web Service (ho tro dong thoi Web API Backend va khoi chay Bot chay ngam).
* **Cac bien moi truong (Environment Variables) can thiet lap:**
  * `DISCORD_TOKEN`: Token cua bot Discord.
  * `DATABASE_URL`: URI ket noi co so du lieu Neon PostgreSQL.
  * `GEMINI_API_KEY`: API Key kết nối Google Gemini.
  * `API_SECRET`: Key bao mat de authenticate Web Dashboard.

## 2. Co so du lieu Neon PostgreSQL
* Cau hinh Neon Serverless PostgreSQL tren giao dien quan tri cloud.
* Dong bo du lieu bang cach khai bao bien `DATABASE_URL` tren Render. He thong bot tu dong phat hien va khoi tao schema ban dau.

## 3. Uptime & Giam sat (UptimeRobot)
* Dang ky giam sat tai UptimeRobot.
* Cau hinh HTTP GET ping den dia chi url cua Render Web Service (vd: `https://bot-discord-xyz.onrender.com/`) moi 5 phut de bot luon online va khong bi ngu (sleep mode).
