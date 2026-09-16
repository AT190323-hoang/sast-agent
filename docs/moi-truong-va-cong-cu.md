# Môi trường & công cụ

Máy: **WSL2 Ubuntu trên Windows 11**. Mạng công ty có **TLS inspection (Vingroup Web Gateway)**.

## 1. Ràng buộc của máy — đọc trước khi cài gì

| Thứ | Trạng thái | Hệ quả |
|---|---|---|
| `sudo` | **Cần mật khẩu** | Claude không tự chạy `apt install` được. Cần cài gì thì user tự chạy bằng `! <lệnh>` trong prompt Claude Code |
| `python3` | ✅ 3.10.6 | |
| `pip` | ✅ đã bootstrap thủ công (`--user`) | Gọi bằng `python3 -m pip`, không có lệnh `pip3` |
| `node` / `npm` | ❌ **chưa có** | 🔴 Blocker cho codebase-memory-mcp (Tuần 2) và chạy Juice Shop thật |
| `docker` | ✅ đã hoạt động (16/09) | WSL integration đã bật sẵn từ trước. Lệnh docker cần chạy qua `sg docker -c "..."` vì shell hiện tại chưa nạp lại group `docker` (đã có trong `/etc/group`) — mở terminal WSL mới cũng tự hết |
| `git`, `curl`, `wget` | ✅ | |
| Opengrep | ✅ v1.30.0 | `~/.local/bin/opengrep` (đã có trong PATH qua `.bashrc`) |

## 2. Vấn đề TLS inspection — nguyên nhân & cách xử lý

**Triệu chứng:** tool báo `SSL: CERTIFICATE_VERIFY_FAILED — unable to get local issuer certificate`
khi tải gì đó từ internet, trong khi `curl` tới cùng domain đó lại chạy bình thường.

**Nguyên nhân:** gateway công ty chặn giữa (TLS inspection) và ký lại certificate bằng CA của
Vingroup. CA này **đã có** trong trust store hệ thống:

```
/usr/local/share/ca-certificates/vingroup/*.crt   → đã merge vào /etc/ssl/certs/ca-certificates.crt
```

Nên `curl`, `git`, `apt` (dùng trust store hệ thống) chạy bình thường. Nhưng nhiều tool Python
**bundle CA riêng** (qua thư viện `certifi`) và bỏ qua trust store hệ thống → không biết CA
Vingroup → fail. Opengrep là một ví dụ: nó nhúng cả interpreter Python riêng trong
`~/.cache/opengrep/`.

**Cách xử lý (áp dụng cho mọi tool Python gặp lỗi tương tự):**

```bash
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

> Đây **không phải lỗi code**. Đừng đi sửa code hay tắt xác thực TLS (`verify=False`,
> `--insecure`) — vừa không cần thiết vừa là thói quen xấu về bảo mật.

Muốn đặt vĩnh viễn thì thêm 2 dòng trên vào `~/.bashrc`.

## 3. Opengrep — cách dùng

### Cài đặt (đã làm)

```bash
curl -fsSL https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh | bash
# → ~/.opengrep/cli/v1.30.0/opengrep, symlink ~/.local/bin/opengrep
```

Lưu ý: **không có package `opengrep` trên PyPI** — `pip install opengrep` sẽ báo không tìm thấy.
Phải dùng install script hoặc tải binary từ GitHub releases.

### Lệnh scan chuẩn của dự án

```bash
export PATH="$HOME/.local/bin:$PATH"
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

# Quét bằng rule pack từ Semgrep registry
opengrep scan --config auto \
  ~/projects/targets/juice-shop/routes \
  ~/projects/targets/juice-shop/lib \
  ~/projects/targets/juice-shop/models \
  ~/projects/targets/juice-shop/config \
  ~/projects/targets/juice-shop/app.ts \
  ~/projects/targets/juice-shop/server.ts \
  --json --output ~/projects/vinsoc-sast-agent/reports/week1/findings_raw_auto.json

# Quét bằng custom rule của dự án
opengrep scan --config ~/projects/vinsoc-sast-agent/harness/rules/ <target> --json --output <out>.json

# Kiểm tra cú pháp custom rule trước khi chạy
opengrep validate ~/projects/vinsoc-sast-agent/harness/rules/
```

### Bẫy đã gặp

1. **Một `--config` sai làm hỏng cả lần chạy.** `--config p/nodejsscantypescript` trả HTTP 404
   → kết quả là **0 finding trên toàn bộ lần chạy**, không phải chạy một phần. Luôn kiểm tra:
   ```bash
   python3 -c "import json; d=json.load(open('<out>.json')); print(len(d['results']), 'results,', len(d['errors']), 'errors'); [print(e) for e in d['errors']]"
   ```
2. **Rule pack có thật đã dùng được:** `p/javascript`, `p/typescript`, `p/security-audit`,
   `p/owasp-top-ten`, `p/secrets`, `p/expressjs`, và `auto`.
3. **Chỉ quét file được git track.** Opengrep mặc định giới hạn theo git — file chưa commit/bị
   gitignore sẽ bị bỏ qua (log ghi "Scan was limited to files tracked by git").
4. **Registry pack gần như không có rule cho `missing_control` và `broken_invariant`.** Đây là
   phát hiện có giá trị cho đề tài (dẫn chứng: rule OSS chung không encode được route/guard
   binding riêng của từng app) chứ không phải lỗi cấu hình. Bù bằng custom rule trong
   `harness/rules/`.

### Viết custom rule — lỗi cú pháp đã gặp

- Pattern `try { ... } catch (...) { ... }` **không parse được** với TypeScript. Cần viết lại
  theo cú pháp khác (vd dùng `pattern-not-inside` với dạng pattern hợp lệ, hoặc
  `pattern-regex`).
- Lỗi YAML "mapping values are not allowed in this context" thường do **message nhiều dòng
  dùng `>` nhưng bên trong có dấu `:`** — bọc trong quote hoặc dùng `|` cho đúng.
- Luôn `opengrep validate <thư mục rule>` trước khi chạy scan thật.

## 4. App mẫu

| App | Đường dẫn | Dùng cho | Trạng thái |
|---|---|---|---|
| OWASP Juice Shop | `~/projects/targets/juice-shop` | App chính Tuần 1 (Express/TypeScript, Sequelize) | ✅ đã clone |
| crAPI | chưa clone | `missing_control` (chuyên lỗi authorization API) | ⬜ cần docker |
| WebGoat | chưa clone | Nguồn dự phòng, có thể hữu ích cho `broken_invariant` (Java) | ⬜ |

### Cấu trúc Juice Shop cần biết

```
server.ts          # ⭐ nơi bind toàn bộ route + middleware (guard nằm ở đây, KHÔNG nằm trong routes/)
app.ts
routes/            # handler từng endpoint
lib/insecurity.ts  # ⭐ module bảo mật: isAuthorized, denyAll, appendUserId, sanitize*, hash/hmac
models/            # Sequelize models
config/            # file cấu hình YAML, override theo môi trường (package `config`)
frontend/          # Angular app (chưa đưa vào phạm vi scan)
```

Hai file đánh dấu ⭐ là chìa khoá của cả đề tài: **finding nằm ở `routes/` nhưng context quyết
định TP/FP lại nằm ở `server.ts` và `lib/insecurity.ts`** — đúng bài toán "SAST thiếu context".

## 5. Cần cài thêm (theo tuần)

**Trước Tuần 2:**
```bash
# user tự chạy (cần sudo):
! sudo apt update && sudo apt install -y nodejs npm
# hoặc dùng nvm để khỏi cần sudo:
! curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash
```
- Anthropic SDK cho harness: `python3 -m pip install --user anthropic`
- codebase-memory-mcp: https://github.com/DeusData/codebase-memory-mcp

**crAPI (đã chuyển vào Tuần 1):** Docker đã sẵn sàng, chạy `git clone` rồi `sg docker -c "docker compose up -d"` trong thư mục crAPI.
