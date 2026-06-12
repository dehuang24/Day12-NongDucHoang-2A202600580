# Day 12 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
Dưới đây là 5 lỗi thiết kế (anti-patterns) được phát hiện trong file `develop/app.py`:
1. **Lộ lọt thông tin nhạy cảm (Hardcoded Secrets):** Khai báo trực tiếp `OPENAI_API_KEY` và `DATABASE_URL` trong mã nguồn dưới dạng chuỗi trần. Khi đẩy code lên hệ thống kiểm soát phiên bản công khai như GitHub, khóa bí mật sẽ bị lộ ngay lập tức, dẫn đến rủi ro về chi phí tài khoản và rò rỉ dữ liệu database.
2. **Không quản lý cấu hình tập trung (No Config Management):** Các cài đặt cấu hình như `DEBUG = True`, `MAX_TOKENS = 500` bị viết cứng trong mã nguồn thay vì lưu trữ độc lập ở các tệp cấu hình hoặc biến môi trường. Điều này khiến cho việc chuyển đổi cấu hình giữa môi trường phát triển (dev) và thực tế (production) trở nên phức tạp do phải chỉnh sửa trực tiếp vào code.
3. **Sử dụng print() thay vì thư viện logging chuyên dụng:** Sử dụng câu lệnh `print()` thông thường, không định cấu trúc log (dễ phân tích như JSON) và không lọc thông tin. Đặc biệt nguy hiểm khi in ra cả `OPENAI_API_KEY` lên console log.
4. **Thiếu Endpoint kiểm tra sức khỏe hệ thống (No Health Check):** Ứng dụng không cung cấp các endpoint như `/health` hay `/ready`. Khi triển khai lên container/cloud, hệ thống tự động hóa sẽ không thể biết container có đang hoạt động tốt hay đã bị treo (deadlock, out of memory) để tiến hành restart.
5. **Cổng mạng (Port) và Host gán cứng:** Uvicorn được cấu hình chạy trên `localhost` (khiến bên ngoài container không thể kết nối tới) và Port cố định `8000` (gây xung đột trên production khi cloud platform tự động gán cổng động qua biến môi trường `PORT`). Đồng thời, tham số `reload=True` hoạt động liên tục ở production gây suy giảm hiệu năng.

---

### Exercise 1.3: Comparison table

| Feature | Develop | Production | Why Important? |
| :--- | :--- | :--- | :--- |
| **Config** | Viết trực tiếp (hardcoded) các cài đặt trong code (`DEBUG`, `MAX_TOKENS`). | Quản lý tập trung qua lớp `Settings` và nạp động từ biến môi trường (Environment Variables) bằng `os.getenv()`. | Giúp dễ dàng cấu hình linh hoạt cho từng môi trường (Dev/Staging/Prod) mà không cần chỉnh sửa hay biên dịch lại mã nguồn của ứng dụng. |
| **Health check** | Không có endpoint kiểm tra sức khỏe. | Tích hợp hai endpoint `/health` (Liveness probe) và `/ready` (Readiness probe). | Giúp nền tảng Cloud (Docker Compose, Kubernetes, Railway, Render) giám sát trạng thái của ứng dụng để tự động phục hồi (restart) khi gặp lỗi hoặc điều phối traffic một cách hợp lý. |
| **Logging** | Dùng hàm `print()`, không có định dạng chuẩn, ghi lại cả thông tin nhạy cảm (secrets). | Sử dụng module `logging` của Python, cấu hình log định dạng JSON có cấu trúc chặt chẽ và không log các thông tin nhạy cảm. | Giúp dễ dàng tích hợp với các hệ thống thu thập log tập trung (như Loki, Datadog) để phân tích lỗi, đồng thời bảo đảm an toàn thông tin nhạy cảm của hệ thống. |
| **Shutdown** | Tắt đột ngột (khi kết thúc tiến trình, các request đang dở dang sẽ bị ngắt lập tức). | Tích hợp cơ chế Graceful shutdown bằng cách xử lý tín hiệu `SIGTERM` và sử dụng `lifespan` trong FastAPI. | Cho phép dịch vụ hoàn thành nốt các request đang xử lý trước khi tắt hẳn, giải phóng an toàn các kết nối phụ trợ (DB, Redis) để bảo đảm trải nghiệm người dùng liền mạch. |
| **Host/Port Binding** | Bỏ qua biến môi trường, chỉ định cứng `host="localhost"`, `port=8000` và bật `reload=True`. | Đọc động cổng qua biến môi trường `PORT`, gán host là `0.0.0.0` để container có thể nhận traffic từ bên ngoài, chỉ `reload` khi bật `debug`. | Đảm bảo container chạy được trên môi trường Docker/Cloud, tự động thích ứng với cổng động do nhà cung cấp Cloud phân phát, và tối ưu hóa hiệu suất chạy production. |

---

## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. **Base image:** Base image được chọn là `python:3.11` (Bản phân phối Python đầy đủ, dung lượng lớn ~1 GB).
2. **Working directory:** Thư mục làm việc mặc định được đặt trong container là `/app` (tất cả các câu lệnh tiếp theo sẽ chạy tại đây).
3. **Tại sao COPY requirements.txt trước?** Nhằm tận dụng cơ chế lưu trữ đệm (layer cache) của Docker. Do danh sách các thư viện phụ thuộc ít khi thay đổi hơn mã nguồn ứng dụng, việc sao chép `requirements.txt` và chạy `pip install` trước giúp Docker bỏ qua bước cài đặt thư viện ở những lần build sau nếu tệp `requirements.txt` giữ nguyên, rút ngắn đáng kể thời gian build.
4. **CMD vs ENTRYPOINT khác nhau thế nào?**
   - `CMD` định nghĩa câu lệnh hoặc tham số chạy mặc định khi container khởi chạy, nhưng nó có thể dễ dàng bị ghi đè (override) khi truyền lệnh khác ở cuối câu lệnh `docker run`.
   - `ENTRYPOINT` định nghĩa một tiến trình cố định luôn chạy khi container khởi động. Các tham số truyền vào từ `docker run` hoặc `CMD` sẽ được gán làm tham số đầu vào cho `ENTRYPOINT`, giúp container hoạt động như một công cụ thực thi dòng lệnh chuyên biệt.

### Exercise 2.3: Image size comparison
- **Develop:** 1.66 GB
- **Production:** 236 MB
- **Difference:** Giảm khoảng **85.78%** dung lượng.
- **Giải thích Multi-stage build:**
  - **Stage 1 (Builder):** Sử dụng `python:3.11-slim` làm nền, cài đặt các công cụ biên dịch thiết yếu (`gcc`, `libpq-dev`) để biên dịch/cài đặt các thư viện phụ thuộc trong `requirements.txt` vào thư mục tạm thời `/root/.local`.
  - **Stage 2 (Runtime):** Sử dụng một base image sạch `python:3.11-slim`, tạo ra tài khoản người dùng bảo mật `appuser` (non-root) để chạy ứng dụng và chỉ sao chép thư mục thư viện `/root/.local` từ Stage 1 sang. Nhờ loại bỏ toàn bộ các công cụ build cồng kềnh và tệp tin rác phát sinh ở Stage 1, kích thước image cuối cùng cực kỳ nhỏ gọn, tối ưu và nâng cao tính bảo mật cho môi trường sản xuất.

### Exercise 2.4: Docker Compose stack
- **Mô hình kiến trúc (Architecture Diagram):**
```
      HTTP Traffic (Port 80)
                │
                ▼
      ┌──────────────────┐
      │   Nginx (LB)     │ (Port 80:80)
      └─────────┬────────┘
                │ (Internal Network)
                ▼
      ┌──────────────────┐
      │   Agent (FastAPI)│ (Port 8000)
      └────┬─────────┬───┘
           │         │
           ▼         ▼
      ┌─────────┐ ┌──────────┐
      │  Redis  │ │  Qdrant  │
      │ (Cache) │ │ (Vector) │
      └─────────┘ └──────────┘
```
- **Các dịch vụ được khởi chạy:**
  1. `nginx`: Đóng vai trò là Reverse Proxy và Load Balancer, nhận traffic cổng 80 từ bên ngoài và định tuyến cân bằng tải tới Agent.
  2. `agent`: FastAPI AI Agent xử lý logic ứng dụng và kết nối đến các tài nguyên phụ trợ.
  3. `redis`: Bộ nhớ đệm (Cache) lưu trữ session hội thoại và theo dõi rate limiting của người dùng.
  4. `qdrant`: Vector Database phục vụ lưu trữ embeddings của tài liệu cho ứng dụng RAG.
- **Cách thức các dịch vụ giao tiếp:**
  - Các container giao tiếp nội bộ với nhau thông qua mạng cầu nối ảo biệt lập (`internal` network).
  - Nginx định tuyến traffic đến `agent` qua DNS nội bộ của Docker bằng tên dịch vụ `agent:8000`.
  - Agent kết nối tới Redis qua URL `redis://redis:6379/0` và Qdrant qua `http://qdrant:6333`.
  - Chỉ duy nhất container `nginx` mở cổng (expose ports `80` và `443`) ra ngoài máy host, các dịch vụ còn lại hoàn toàn ẩn danh trong mạng nội bộ, giúp tăng tối đa tính bảo mật.

---

## Part 3: Cloud Deployment

### Exercise 3.1: Railway deployment
- **URL:** https://day12-nongduchoang-2a202600580-production.up.railway.app
- **Screenshot:** [Screenshots of deployment](screenshots/) (Bạn hãy chụp ảnh giao diện dashboard Railway hoạt động và kết quả chạy thử Swagger để thêm vào thư mục `screenshots/`)
- **Kết quả kiểm thử Endpoint `/health`:**
  ```json
  {
    "status": "ok",
    "uptime_seconds": 171.1,
    "platform": "Railway",
    "timestamp": "2026-06-12T08:54:24.186593+00:00"
  }
  ```
- **Kết quả kiểm thử Endpoint `/ask`:**
  ```json
  {
    "question": "hello",
    "answer": "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
    "platform": "Railway"
  }
  ```
