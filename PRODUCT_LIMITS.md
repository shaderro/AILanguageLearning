# LinkText 功能数值上限

本文档整理当前代码中各类功能的限制数值，便于产品、运营与开发对齐。  
**主要代码来源：** `frontend/my-web-ui/backend/main.py`、`backend/config.py`、`backend/middleware/rate_limit.py`、前端 `UploadInterface.jsx` / `creditsUtils.js` 等。

> 生产环境可通过 `.env` 覆盖部分配置（见文末）。  
> 最后更新：2026-05-19

---

## 积分 / Token

| 项目 | 数值 | 说明 |
|------|------|------|
| 积分与 token 换算 | **1 积分 = 10,000 token** | 前后端展示层统一 |
| 新用户注册赠送 | **80 积分**（800,000 token） | 环境变量 `NEW_USER_SIGNUP_POINTS`，默认 80 |
| 积分不足阈值 | **1,000 token（0.1 积分）** | 低于此值无法使用 AI 聊天等功能 |
| 邀请码默认面额 | **100 积分**（1,000,000 token） | 脚本 `generate_invite_codes.py` 默认值；实际以 DB 中 `invite_codes.token_grant` 为准 |
| Admin 用户 | **不受积分限制** | `role === 'admin'` 跳过不足检查 |

---

## 文章上传

| 项目 | 数值 | 说明 |
|------|------|------|
| 每用户文章总数 | **50 篇** | 所有语言合计；仅统计 `processing` + `completed` |
| 单次上传正文长度 | **12,000 字符** | 超出可前端截取或拒绝 |
| 分段上传：单段长度 | **2,000 字符** | 首段 + `append-segment` 每段均受此限 |
| 分段上传：前端总长度 | **30,000 字符** | 超出自动截断后再分段（约最多 15 段） |
| 文章标题长度 | **80 字符** | 前端 `UploadInterface` 限制 |
| 支持上传格式 | `.txt` / `.md` / `.pdf` | 后端文件上传接口 |
| 上传请求超时 | **10 分钟** | 前端 API 请求 timeout |

**说明：** 没有「单篇文章最多收录 N 个词汇」的业务上限；词汇按用户维度累积，不按文章 cap。

---

## AI 聊天

| 项目 | 数值 | 说明 |
|------|------|------|
| 单次提问长度 | **300 字符** | 前后端一致 |
| 单次选中文本长度 | **500 字符** | 引用 / 划词上下文 |
| 每轮新增知识点 | **3 个** | 语法 + 词汇合计上限（`MAX_CHAT_KNOWLEDGE_ITEMS`） |
| 并发提问 | **1 条 / 用户** | 同时只能处理一条 chat |
| 1 小时 AI token 消耗上限 | **30,000 token** | 约 3 积分；非 admin 用户 |
| 对话历史保留（内存） | **100 轮** | `DataController(max_turns=100)` |
| 聊天历史 API 单次返回 | **默认 100 条，最大 500 条** | `/api/chat/history` |

---

## API 频率限制

| 接口类型 | 限制 | 窗口 |
|----------|------|------|
| `/api/chat` | **10 次 / 分钟 / 用户** | 60 秒 |
| 其他需登录接口 | **300 次 / 分钟 / 用户** | 60 秒 |
| 健康检查等公开接口 | 不限 | — |

开发环境下，带 `X-Sandbox-Test: 1` 的请求可绕过部分限流（压测用）。

> **注意：** `main.py` 启动日志中曾打印过 20/100，已过时；以 `backend/middleware/rate_limit.py` 为准。

---

## 账户 / 认证

| 项目 | 数值 | 说明 |
|------|------|------|
| 密码最短长度 | **6 位** | 注册 / 改密 |
| Magic link 有效期 | **30 分钟** | `MAGIC_LINK_TTL_MINUTES` |
| Magic link 重发冷却 | **60 秒** | 前后端一致 |
| 登录会话有效期 | **30 天** | `AUTH_SESSION_TTL_DAYS` |

---

## 语言 / 学习

| 项目 | 数值 | 说明 |
|------|------|------|
| 「正在学习」可选语言 | **9 种** | 中 / 英 / 西 / 法 / 日 / 韩 / 德 / 阿 / 俄 |
| 「正在学习」最少保留 | **1 种** | 不能删到 0 |
| Onboarding 预置文章展示 | **3 篇** | 按难度排序取前 3 |
| 本地最近打开文章 | **50 篇** | `pageStateManager` |

---

## 词汇 / 语法 API（列表查询）

| 项目 | 数值 | 说明 |
|------|------|------|
| 词汇列表单次返回 | **默认 100，最大 1,000** | `skip` + `limit` 分页 |
| 翻译服务单次文本 | **500 字符** | 超出会智能截断（`translationService`） |

---

## 其他 UI 限制

| 项目 | 数值 |
|------|------|
| 聊天面板最大宽度 | 600px（可拖拽，有最小宽度） |
| Vocab notation 调试日志 | 400 行 |

---

## 环境变量可覆盖项

```env
NEW_USER_SIGNUP_POINTS=80          # 新用户赠送积分
MAGIC_LINK_TTL_MINUTES=30          # 登录链接有效期
MAGIC_LINK_RESEND_COOLDOWN_SECONDS=60
AUTH_SESSION_TTL_DAYS=30
```

---

## 代码常量速查

| 常量 | 值 | 文件 |
|------|-----|------|
| `MAX_ARTICLE_LENGTH` | 12000 | `frontend/my-web-ui/backend/main.py` |
| `MAX_SEGMENT_CHARS` | 2000 | 同上 |
| `MAX_ARTICLES_PER_USER` | 50 | 同上 |
| `MAX_CHAT_QUESTION_LENGTH` | 300 | 同上 |
| `MAX_CHAT_SELECTION_LENGTH` | 500 | 同上 |
| `MAX_CHAT_KNOWLEDGE_ITEMS` | 3 | 同上 |
| `MAX_CHAT_TOKENS_PER_HOUR` | 30000 | 同上 |
| `MAX_UPLOAD_TOTAL_CHARS` | 30000 | `frontend/.../UploadInterface.jsx` |
| `NEW_USER_SIGNUP_CREDITS` | 80 | `frontend/.../creditsUtils.js` |
| `INSUFFICIENT_CREDITS_THRESHOLD` | 1000 | 同上 |
| `CREDITS_PER_TOKEN_UNIT` | 10000 | 同上 |

---

## 常见误解

1. **长文上传：** 单次 API 限 12,000 字；走前端分段流程时，总长最多 **30,000** 字、每段 **2,000** 字。
2. **词汇上限：** 无「每篇文章最多 N 个生词」限制；单次 AI 问答最多新增 **3** 个知识点。
3. **文章数量：** 每用户最多 **50** 篇（含处理中与已完成），与语言无关。
