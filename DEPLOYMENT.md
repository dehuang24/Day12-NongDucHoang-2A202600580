# Deployment Information

Đây là tài liệu ghi nhận thông tin triển khai (deployment) của hệ thống Production AI Agent lên Cloud Platform phục vụ chấm điểm cho Giai đoạn 2.

## 🌐 Public URL
Hệ thống đã được deploy thành công lên Railway:
👉 **[Public URL](https://day12-nongduchoang-2a202600580-production.up.railway.app)**

---

## 🏗️ Platform
- **Platform sử dụng:** Railway Cloud Platform
- **Hình thức build:** Dockerfile (Multi-stage Build) được phát hiện tự động thông qua cấu hình `railway.toml`.
- **Cơ sở dữ liệu bổ trợ:** In-memory SQLite / local file (hoặc cấu hình Redis nếu scale out).

---

## 🛠️ Test Commands

Dưới đây là các câu lệnh kiểm thử trực tiếp lên hệ thống đã triển khai:

### 1. Health Check Endpoint
Kiểm tra trạng thái hoạt động tổng thể của ứng dụng (liveness probe).
```bash
curl -i https://day12-nongduchoang-2a202600580-production.up.railway.app/health
```
* **Kết quả dự kiến (HTTP 200 OK):**
```json
{
  "status": "ok",
  "uptime_seconds": 2431.9,
  "platform": "Railway",
  "timestamp": "2026-06-12T09:36:21.187130+00:00"
}
```

### 2. API Test (Không có Authentication)
Kiểm tra endpoint `/ask` khi thiếu Header xác thực API key.
```bash
curl -i -X POST https://day12-nongduchoang-2a202600580-production.up.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello Agent"}'
```
* **Kết quả dự kiến (HTTP 401 Unauthorized / 422 Unprocessable Entity tuỳ phiên bản triển khai):**
Hệ thống sẽ từ chối xử lý và yêu cầu Header `X-API-Key`.

### 3. API Test (Có Authentication)
Gửi câu hỏi kèm theo API Key bảo mật.
```bash
curl -i -X POST https://day12-nongduchoang-2a202600580-production.up.railway.app/ask \
  -H "X-API-Key: YOUR_AGENT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```
* **Kết quả dự kiến (HTTP 200 OK):**
```json
{
  "question": "What is Docker?",
  "answer": "Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!",
  "platform": "Railway"
}
```

---

## ⚙️ Environment Variables Set
Các biến môi trường được cấu hình trực tiếp trên Dashboard của Railway để bảo mật tuyệt đối, tránh lộ lọt khoá bí mật:
1. `PORT`: Đặt cổng dịch vụ hoạt động (Railway tự động liên kết).
2. `AGENT_API_KEY`: Lưu trữ API Key hợp lệ phục vụ xác thực người dùng.
3. `ENVIRONMENT`: Đặt thành `production` để tối ưu hiệu năng và ẩn tài liệu `/docs`.
4. `LOG_LEVEL`: Cấu hình mức độ hiển thị log hệ thống (`info` hoặc `warning`).

---

## 📸 Screenshots
*(Vui lòng chụp ảnh màn hình hoạt động thực tế trên tài khoản của bạn và lưu vào thư mục `screenshots/` theo danh sách dưới đây)*:
- 📊 **Deployment Dashboard:** [screenshots/dashboard.png](screenshots/dashboard.png) (Ảnh chụp dashboard Railway đang hiển thị dịch vụ running).
- 🟢 **Service Running:** [screenshots/running.png](screenshots/running.png) (Ảnh chụp logs dịch vụ hiển thị khởi chạy thành công).
- 🧪 **Test Results:** [screenshots/test.png](screenshots/test.png) (Ảnh chụp kết quả chạy thử curl hoặc Postman thành công).
