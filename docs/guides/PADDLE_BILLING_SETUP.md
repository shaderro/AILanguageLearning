# Paddle Billing 接入指南

本文说明如何在 LinkText 中完成 Paddle Billing 沙盒/生产配置与联调。

## 架构概览

```
用户点击「Upgrade to Pro」
        ↓
前端 Paddle.js Checkout（customData.user_id）
        ↓
Paddle 处理支付
        ↓
POST /api/billing/webhooks/paddle（验签 + 入账）
        ↓
更新 users.plan / users.token_balance
        ↓
前端 checkout.completed → 刷新 /api/auth/me
```

**重要：** 积分只通过 webhook 入账，前端不能直接调用「加积分」接口。

## 1. Paddle Dashboard 配置

### 商品（Catalog）

只需创建一个 **Pro 月度订阅**（Subscription），与 `billingConstants.js` 中的 `PRO_MONTHLY_CREDITS`（默认 1000）对齐。

记录 Pro 订阅的 **Price ID**（`pri_01...`）。

### Webhook（Notifications）

1. Developer tools → **Notifications** → New destination  
2. URL：`https://<你的后端域名>/api/billing/webhooks/paddle`  
3. 订阅事件（至少）：
   - `transaction.completed`
   - `subscription.activated`
   - `subscription.canceled`
4. 保存后复制 **Webhook secret**（`pdl_ntfset_...`）

本地开发需公网 HTTPS（ngrok / Cloudflare Tunnel），例如：

```text
https://abc123.ngrok-free.app/api/billing/webhooks/paddle
```

## 2. 环境变量

### 项目根 `.env`（后端）

```env
PADDLE_API_KEY=pdl_sdbx_apikey_...
PADDLE_WEBHOOK_SECRET=pdl_ntfset_...
PADDLE_ENV=sandbox
PADDLE_PRICE_PRO=pri_01...
PRO_MONTHLY_CREDITS=1000
```

### `frontend/my-web-ui/.env`（前端）

```env
VITE_PADDLE_CLIENT_TOKEN=test_...
VITE_PADDLE_ENV=sandbox
VITE_PADDLE_PRICE_PRO=pri_01...
```

| 变量 | 说明 |
|------|------|
| `PADDLE_API_KEY` | 服务端 API Key（预留，当前 webhook 流程不必须） |
| `PADDLE_WEBHOOK_SECRET` | Webhook 验签密钥 |
| `VITE_PADDLE_CLIENT_TOKEN` | **Client-side token**，仅前端 Checkout |

配置完成后重启后端与 `yarn dev`。

## 3. 数据库迁移

```bash
python scripts/migrations/migrate_add_paddle_billing.py
```

或在 SQLite 开发环境下，启动 `frontend/my-web-ui/backend/main.py` 时会自动增量创建 `paddle_webhook_events` 表及 `users.paddle_*` 列。

## 4. 验证

1. 登录应用，打开「用量与账单」  
2. 点击 **Upgrade to Pro**  
3. 在 Paddle Sandbox 完成测试支付  
4. 查看后端日志：`[Paddle] webhook ...`  
5. 刷新后「剩余积分」应增加  

也可在 Paddle Dashboard → Notifications → **Send test event** 发送 `transaction.completed`（需在 payload 的 `custom_data` 中包含 `user_id`）。

## 5. 上线生产

1. Paddle 切换到 **Live** 环境，创建 Live 商品与 Price  
2. 更新 `.env` / Render / Vercel 为 Live 的 API Key、Webhook secret、Client token、Price ID  
3. 设置 `PADDLE_ENV=production`、`VITE_PADDLE_ENV=production`  
4. 在 Live Notifications 中配置生产 webhook URL  

## 6. 模拟支付

未配置 `PADDLE_WEBHOOK_SECRET` + Price ID 时，仍可使用 `/api/auth/billing/simulate-*` 与 UI 上的「(simulated)」按钮做本地 UX 测试。

一旦 Paddle 配置完整，模拟接口会返回 **403**，前端自动走真实 Checkout。

## 相关代码

| 文件 | 作用 |
|------|------|
| `backend/services/paddle_billing.py` | 验签、幂等、入账 |
| `backend/api/paddle_routes.py` | Webhook 路由 |
| `frontend/my-web-ui/src/services/paddleService.js` | Paddle.js Checkout |
| `frontend/my-web-ui/src/contexts/BillingContext.jsx` | 支付入口与刷新余额 |
