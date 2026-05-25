# 本地 Magic Link 联调步骤

按顺序做；**我已在你的 SQLite 上跑过迁移**，`magic_link_tokens` / `auth_sessions` 已存在。

## 0. 先改 `.env`（项目根目录）

在现有变量基础上**增加一行**（端口要和浏览器里打开前端的一致）：

```env
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

说明：

- 前端 Vite 默认 **5173**；若你用 `http://localhost:5173`，把上面改成 `http://localhost:5173`（须与地址栏完全一致）。
- `RESEND_API_KEY` 你已配置；测试发件人 `onboarding@resend.dev` 时，邮件**只能发到 Resend 账号注册邮箱**。

---

## 1. 启动后端（终端 1）

```powershell
cd c:\Users\ranxi\AILanguageLearning\frontend\my-web-ui\backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

看到 `[OK] CORS allow_origins=...` 即表示 CORS 白名单已加载。

---

## 2. 启动前端（终端 2）

```powershell
cd c:\Users\ranxi\AILanguageLearning\frontend\my-web-ui
npm run dev
```

浏览器打开：**http://127.0.0.1:5173**（与 `FRONTEND_ORIGIN` 一致）。

---

## 3. 发登录邮件（界面方式）

1. 点 **登录**。
2. 填邮箱（Resend 测试域请用你 Resend 账号邮箱）。
3. 点 **「发送邮箱登录链接」**（不必填密码）。
4. 等绿色提示；去邮箱点 **Login**。

邮件里的链接形如：`http://127.0.0.1:5173/auth/callback?token=...`

---

## 4. 完成登录

1. 点击邮件链接 → 自动打开 `/auth/callback` → 显示「登录成功，正在跳转…」。
2. 回到首页后，右上角应显示已登录（头像/用户信息）。

---

## 5. 验证 `/api/auth/me`（可选）

登录后打开浏览器 **F12 → Network**，刷新页面，找带 `me` 的请求，状态应为 **200**。

或用 PowerShell（需先完成步骤 4，并把下面的 `SESSION` 换成 verify 返回的 `session_token`）：

```powershell
$SESSION = "粘贴 session_token"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/me" -Headers @{ Authorization = "Bearer $SESSION" }
```

---

## 6. 用 API 文档自测（可选）

打开 http://127.0.0.1:8000/docs

- `POST /api/auth/magic-link/request` → body: `{"email":"你的邮箱"}`
- 收邮件后 `POST /api/auth/magic-link/verify` → body: `{"token":"邮件链接里的 token"}`

---

## 常见问题

| 现象 | 处理 |
|------|------|
| CORS 报错 | 前端地址须在白名单内；默认含 `127.0.0.1:5173` 和 `localhost:5173` |
| 收不到邮件 | 检查 `RESEND_API_KEY`；测试域只能发到 Resend 注册邮箱 |
| 链接打开 404 | 确认前端已启动，路径为 `/auth/callback` |
| verify 失败 | 链接只能用一次；重新点「发送邮箱登录链接」 |
| 邮件链到 `:3000` | 未设 `FRONTEND_ORIGIN`；按步骤 0 改为 5173 并重启后端 |

---

## 表结构已就绪时不必再迁移

若换机器或库被清空，再执行：

```powershell
cd c:\Users\ranxi\AILanguageLearning
python migrate_add_magic_link_auth_tables.py
```
