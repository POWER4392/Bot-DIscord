# Hướng dẫn Quy trình Git & Phân nhánh (Git Workflow Guide)

Tài liệu này hướng dẫn các thành viên của Nhóm 69 cách sử dụng Git, đặt tên nhánh, viết commit message và tạo Pull Request theo đúng tiêu chuẩn công nghiệp.

---

## 🌿 1. Mô hình Phân Nhánh (Branching Model)

Dự án áp dụng mô hình phân nhánh **Git Flow giản lược**:

```
main      [Production]    ------------------------------------> (Deploy Render)
                            ^
                            |  Pull Request (Merge khi ổn định)
develop   [Staging]       ------------------------------------> (Tích hợp tính năng)
                            ^   ^
                            |   |  Pull Requests
feature/  [Working]       --+   +-- feature/23-gemini-chatbot
```

### Chi tiết các nhánh:
- **`main`**: Nhánh chứa mã nguồn chạy ổn định nhất đã được release. Chỉ Project Manager mới có quyền merge vào nhánh này.
- **`develop`**: Nhánh làm việc chung của cả nhóm. Các tính năng mới sẽ được tích hợp tại đây để kiểm thử trước khi đưa lên `main`.
- **`feature/<issue_id>-<description>`**: Nhánh con của từng thành viên khi làm task. Ví dụ: `feature/23-chatbot-gemini`.

---

## 📝 2. Tiêu chuẩn Commit Message (Conventional Commits)

Commit message cần tuân theo định dạng:
`type(scope): description`

### Các loại `type` được chấp nhận:
- **`feat`**: Một tính năng mới cho hệ thống.
- **`fix`**: Sửa lỗi.
- **`docs`**: Thay đổi hoặc bổ sung tài liệu.
- **`style`**: Các thay đổi không ảnh hưởng đến logic code (khoảng trắng, định dạng dòng, viền CSS...).
- **`refactor`**: Tối ưu hóa hoặc tái cấu trúc code nhưng không thay đổi tính năng.
- **`chore`**: Cập nhật các tác vụ nhỏ nhặt (update dependencies, file gitignore...).

### Ví dụ cụ thể:
- `feat(ai): tích hợp API Gemini cho chatbot tự động`
- `fix(music): xử lý lỗi ngoại lệ khi URL bài hát không hợp lệ`
- `docs(pm): bổ sung báo cáo quản trị dự án tuần 3`

---

## 🔄 3. Quy trình Tạo Pull Request (PR Workflow)

1. **Trước khi làm**: Luôn pull code mới nhất từ `develop` về máy:
   ```bash
   git checkout develop
   git pull origin develop
   ```
2. **Tạo nhánh tính năng mới**:
   ```bash
   git checkout -b feature/23-gemini-chatbot
   ```
3. **Lập trình và Commit**: Đảm bảo chạy thử code local thành công trước khi commit.
4. **Push nhánh lên GitHub**:
   ```bash
   git push -u origin feature/23-gemini-chatbot
   ```
5. **Tạo Pull Request trên GitHub**:
   - Source: `feature/23-gemini-chatbot` -> Destination: `develop`.
   - Mô tả PR: Điền đầy đủ thông tin, mô tả các thay đổi và đính kèm từ khóa `Closes #23` ở phần mô tả để GitHub tự động đóng issue liên kết khi PR được duyệt.
