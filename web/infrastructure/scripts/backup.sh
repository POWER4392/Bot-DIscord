#!/bin/bash

# Script tự động sao lưu Cơ sở dữ liệu PostgreSQL cho Discord Bot
# Được lập lịch chạy định kỳ qua Cron Job trên máy chủ VPS/Production

# 1. Khai báo các cấu hình
BACKUP_DIR="/var/backups/bot-discord"
DB_NAME="bot_discord_db"
DB_USER="bot_user"
DB_HOST="localhost"
DB_PORT="5432"
DATE=$(date +%Y-%m-%d_%H%M%S)
FILENAME="${BACKUP_DIR}/${DB_NAME}_backup_${DATE}.sql"

# Tạo thư mục lưu trữ sao lưu nếu chưa tồn tại
mkdir -p "${BACKUP_DIR}"

echo "📅 [$(date)] Bắt đầu tiến trình sao lưu cơ sở dữ liệu ${DB_NAME}..."

# 2. Thực thi lệnh pg_dump
# Xuất cấu trúc và dữ liệu thành file SQL nén Gzip
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -F p > "${FILENAME}"

if [ $? -eq 0 ]; then
    echo "✅ [$(date)] Sao lưu thành công! File lưu trữ tại: ${FILENAME}"
    # Nén file sao lưu để tiết kiệm dung lượng
    gzip "${FILENAME}"
    echo "📦 Đã nén thành công file ${FILENAME}.gz"
else
    echo "❌ [$(date)] Lỗi: Quá trình sao lưu cơ sở dữ liệu thất bại!" >&2
    exit 1
fi

# 3. Dọn dẹp các bản sao lưu cũ hơn 7 ngày để tránh đầy bộ nhớ đĩa
echo "🧹 Đang dọn dẹp các bản sao lưu cũ hơn 7 ngày..."
find "${BACKUP_DIR}" -name "${DB_NAME}_backup_*.sql.gz" -mtime +7 -exec rm -f {} \;
echo "✨ [$(date)] Hoàn thành dọn dẹp và sao lưu!"
