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

#### Exercise 2.4: Docker Compose stack
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

---

## Part 4: API Security

### Exercise 4.1-4.3: Test results

#### 1. API Key Authentication (Exercise 4.1)
Dưới đây là câu trả lời cho các câu hỏi về API Key Authentication trong file `04-api-gateway/develop/app.py`:
- **API key được check ở đâu?**
  - API key được kiểm tra tập trung trong hàm dependency `verify_api_key` (dòng 39-54). Hàm này được truyền vào endpoint `/ask` thông qua cơ chế Dependency Injection của FastAPI: `_key: str = Depends(verify_api_key)`.
  - FastAPI sử dụng `APIKeyHeader(name="X-API-Key", auto_error=False)` để tự động trích xuất giá trị từ HTTP Header `X-API-Key`.
- **Điều gì xảy ra nếu sai key?**
  - **Nếu thiếu header `X-API-Key`:** Hệ thống trả về mã trạng thái HTTP `401 Unauthorized` kèm thông tin lỗi: `{"detail": "Missing API key. Include header: X-API-Key: <your-key>"}`.
  - **Nếu cung cấp sai key:** Hệ thống trả về mã trạng thái HTTP `403 Forbidden` kèm thông tin lỗi: `{"detail": "Invalid API key."}`.
- **Làm sao rotate key?**
  - Để rotate (xoay vòng) API key, ta chỉ cần thay đổi giá trị của biến môi trường `AGENT_API_KEY` (ví dụ trên môi trường Docker, file `.env`, Railway dashboard, v.v.).
  - Khi đó, dòng lệnh `API_KEY = os.getenv("AGENT_API_KEY", "demo-key-change-in-production")` sẽ tự động nạp giá trị key mới mà không yêu cầu lập trình viên phải sửa trực tiếp mã nguồn ứng dụng.

---

#### 2. JWT + Rate Limiting Test Outputs (Exercise 4.2-4.3)
Dưới đây là kết quả kiểm thử chạy thực tế bằng script `04-api-gateway/production/test_security.py` kết nối tới server production bảo mật (JWT + Rate limiting + Cost guard):

```text
--- 1. Test GET /health (Public) ---
Status: 200
Response: {"status":"ok","uptime_seconds":8.6,"security":"JWT + RateLimit + CostGuard","timestamp":"2026-06-12T09:08:25.647200+00:00"}

--- 2. Test POST /ask (Không có Token - Expected 401) ---
Status: 401
Response: {"detail":"Authentication required. Include: Authorization: Bearer <token>"}

--- 3. Đăng nhập lấy JWT Token (student / demo123) ---
Token lấy thành công (20 kí tự đầu): eyJhbGciOiJIUzI1NiIs

--- 4. Gửi câu hỏi POST /ask hợp lệ (Có Token - Expected 200) ---
Status: 200
Response: {"question":"Hi, what is Docker?","answer":"Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!","usage":{"requests_remaining":9,"budget_remaining_usd":1.9e-05}}

--- 5. Spam 12 requests liên tiếp để kích hoạt Rate Limiting (Expected 429) ---
Request 1: Success (200) - Remaining requests: 8
Request 2: Success (200) - Remaining requests: 7
Request 3: Success (200) - Remaining requests: 6
Request 4: Success (200) - Remaining requests: 5
Request 5: Success (200) - Remaining requests: 4
Request 6: Success (200) - Remaining requests: 3
Request 7: Success (200) - Remaining requests: 2
Request 8: Success (200) - Remaining requests: 1
Request 9: Success (200) - Remaining requests: 0
Request 10: Failed (429) - {"detail":{"error":"Rate limit exceeded","limit":10,"window_seconds":60,"retry_after_seconds":39}}
```

**Phân tích chi tiết về Rate Limiting:**
- **Thuật toán sử dụng:** **Sliding Window Counter**. Thuật toán này sử dụng một hàng đợi hai đầu (`deque`) lưu trữ các timestamp của request. Khi có request mới, các timestamp cũ hơn 60 giây (ngoài window) sẽ bị loại bỏ bằng `popleft()`. Nếu kích thước hàng đợi vẫn đạt giới hạn cấu hình, hệ thống sẽ từ chối request.
- **Giới hạn số requests:**
  - Đối với vai trò **user** (ví dụ tài khoản `student`): Giới hạn là **10 requests/minute**.
  - Đối với vai trò **admin** (ví dụ tài khoản `teacher`): Giới hạn là **100 requests/minute**.
- **Cách bypass/áp dụng linh hoạt giới hạn cho admin:**
  - Trong file `auth.py`, thông tin role (`admin` hoặc `user`) được mã hóa trực tiếp bên trong JWT Payload khi người dùng đăng nhập thành công.
  - Khi trích xuất và giải mã JWT thành công tại endpoint `/ask`, hệ thống kiểm tra trường `user["role"]`.
  - Endpoint định tuyến và áp dụng dynamic rate limiter: `limiter = rate_limiter_admin if role == "admin" else rate_limiter_user`. Nhờ vậy, admin sẽ có quota lớn hơn và không bị block dễ dàng khi thao tác hệ thống.

---

### Exercise 4.4: Cost guard implementation

#### 1. Phương pháp tiếp cận (Our Approach)
Để ngăn ngừa rủi ro phát sinh hóa đơn LLM khổng lồ do vòng lặp vô tận (infinite loop) hoặc các cuộc tấn công DDoS/spam từ phía client, chúng tôi xây dựng lớp trung gian **Cost Guard** với cơ chế hoạt động như sau:
- **Đơn vị hóa chi phí (Token Pricing):** Định nghĩa cấu trúc giá tiền dựa trên đơn vị $1k tokens thực tế của model (Ví dụ: `GPT-4o-mini` có giá `0.00015 USD` cho 1k input tokens và `0.0006 USD` cho 1k output tokens).
- **Theo dõi định kỳ (Daily Tracking):** Sử dụng đối tượng dữ liệu `UsageRecord` để lưu trữ lượng token và chi phí tích lũy theo ngày (`YYYY-MM-DD`) của từng user.
- **Kiểm soát hai lớp (Dual Budget Protection):**
  1. **Lớp User:** Giới hạn chi phí tối đa hàng ngày cho mỗi người dùng (`daily_budget_usd = $1.0`). Khi vượt qua, hệ thống trả về mã lỗi HTTP `402 Payment Required`.
  2. **Lớp Hệ thống (Global):** Đặt giới hạn chi phí tối đa cho toàn hệ thống (`global_daily_budget_usd = $10.0`) nhằm bảo vệ tổng ví tiền của admin. Khi vượt qua, hệ thống tự động ngắt kết nối và trả về mã lỗi HTTP `503 Service Temporarily Unavailable`.
- **Cảnh báo sớm (Warning threshold):** Khi lượng chi phí tích lũy của user đạt từ `80%` (warn_at_pct), hệ thống sẽ log một dòng cảnh báo nguy cơ cạn kiệt budget để quản trị viên có thể kịp thời nạp tiền hoặc nâng cấp gói dịch vụ.

#### 2. Định hướng triển khai Production
Trong demo in-memory, dữ liệu tiêu thụ được lưu trữ trong một dictionary `self._records` trên RAM của tiến trình ứng dụng. Trên môi trường production thực tế chạy multi-instance (qua Load Balancer), chúng tôi áp dụng các cải tiến sau:
- **Lưu trữ tập trung bằng Redis:** Thay thế dictionary local bằng Redis để chia sẻ trạng thái giữa nhiều instance của API container.
- **Tính toán nguyên tử (Atomic Increments):** Sử dụng lệnh `r.incrbyfloat(key, cost)` để cập nhật chi phí một cách an toàn mà không lo lắng về tranh chấp luồng (race conditions).
- **Tự động dọn dẹp bằng TTL:** Thiết lập thời gian hết hạn cho key Redis tự động (ví dụ: `expire(key, 32 * 24 * 3600)`) để hệ thống tự động giải phóng bộ nhớ khi sang chu kỳ tháng mới.

---

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes

#### 1. Health Checks - Liveness & Readiness Probes (Exercise 5.1)
- **Liveness Probe (`/health`):**
  - **Mục tiêu:** Trả lời câu hỏi "Tiến trình của Agent có còn hoạt động bình thường không?". Nếu gặp lỗi treo cứng (deadlock) hoặc tràn RAM, liveness probe sẽ trả về mã lỗi và cloud platform (Railway/Render/Kubernetes) sẽ tự động khởi động lại (restart) container.
  - **Triển khai:** Endpoint trả về trạng thái tổng thể `"status": "ok"` hoặc `"degraded"`, thông tin uptime hệ thống, phiên bản ứng dụng, và mức tiêu thụ tài nguyên thực tế (`psutil.virtual_memory()`).
- **Readiness Probe (`/ready`):**
  - **Mục tiêu:** Trả lời câu hỏi "Agent đã sẵn sàng nhận kết nối từ người dùng chưa?". Load Balancer sẽ dựa vào endpoint này để quyết định có điều hướng traffic vào container này hay không.
  - **Triển khai:** Chỉ trả về trạng thái `200 OK` khi biến trạng thái `_is_ready = True` (sau khi nạp xong model, kết nối thành công tới Redis/Database). Nếu không, trả về `503 Service Unavailable` và tạm thời loại bỏ container khỏi danh sách định tuyến.

---

#### 2. Graceful Shutdown (Exercise 5.2)
- **Cơ chế hoạt động:**
  - Khi platform gửi tín hiệu `SIGTERM` (yêu cầu tắt container), Uvicorn sẽ bắt tín hiệu này thông qua `lifespan` context manager.
  - Ứng dụng ngay lập tức chuyển trạng thái `_is_ready = False` (để `/ready` trả về lỗi và Load Balancer ngừng gửi request mới đến instance này).
  - Ứng dụng sử dụng một middleware `track_requests` theo dõi số lượng `_in_flight_requests` (các yêu cầu đang xử lý dở dang). Tiến trình shutdown sẽ đợi (sleep) cho đến khi toàn bộ request đang xử lý hoàn thành (hoặc hết timeout 30 giây) rồi mới ngắt kết nối phụ trợ và dừng container sạch sẽ.
- **Kết quả thực nghiệm:** Requests đang xử lý dở dang được hoàn tất trọn vẹn trước khi tiến trình tắt hẳn, loại bỏ hoàn toàn lỗi đứt gãy kết nối đột ngột (connection reset) phía client.

---

#### 3. Stateless Design & Load Balancing (Exercise 5.3 - 5.5)
Dưới đây là kết quả kiểm thử chạy thực tế bằng script `05-scaling-reliability/production/test_stateless.py` kết nối tới hệ thống Load Balancer Nginx điều phối traffic tới 3 instances agent độc lập và dùng Redis lưu trữ session tập trung:

```text
============================================================
Stateless Scaling Demo
============================================================

Session ID: 4db2fe75-ef77-412e-a58e-1a875cf6aee8

Request 1: [instance-efbee4]
  Q: What is Docker?
  A: Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!...

Request 2: [instance-f31af7]
  Q: Why do we need containers?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

Request 3: [instance-2e5d3d]
  Q: What is Kubernetes?
  A: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé....

Request 4: [instance-efbee4]
  Q: How does load balancing work?
  A: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận....

Request 5: [instance-f31af7]
  Q: What is Redis used for?
  A: Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ O...

------------------------------------------------------------
Total requests: 5
Instances used: {'instance-2e5d3d', 'instance-efbee4', 'instance-f31af7'}
✅ All requests served despite different instances!

--- Conversation History ---
Total messages: 10
  [user]: What is Docker?...
  [assistant]: Container là cách đóng gói app để chạy ở mọi nơi. Build once...
  [user]: Why do we need containers?...
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây...
  [user]: What is Kubernetes?...
  [assistant]: Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đ...
  [user]: How does load balancing work?...
  [assistant]: Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã đư...
  [user]: What is Redis used for?...
  [assistant]: Đây là câu trả lời từ AI agent (mock). Trong production, đây...

✅ Session history preserved across all instances via Redis!
```

**Nhận xét:**
- Mặc dù mỗi request được định tuyến ngẫu nhiên (Round-Robin) tới các instance khác nhau (`instance-2e5d3d`, `instance-efbee4`, `instance-f31af7`), cuộc trò chuyện không hề bị đứt quãng.
- Toàn bộ lịch sử trò chuyện (Conversation History) đã được bảo toàn nguyên vẹn trên tất cả các instance vì chúng được lưu trữ và truy vấn chung thông qua cơ sở dữ liệu **Redis** chứ không phụ thuộc vào bộ nhớ RAM cục bộ (in-memory) của từng máy chủ. Đây là nguyên tắc cốt lõi của **Stateless Design** để scale-out ứng dụng vô hạn trong thực tế.


