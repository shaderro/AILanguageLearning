# Render PostgreSQL 数据库连接指南

## 问题：无法从本地连接到 Render PostgreSQL

### 错误信息
```
could not translate host name "dpg-d5gb82muk2gs739e4in0-a" to address: Name or service not known
```

### 原因
Render PostgreSQL 服务提供两种连接字符串：
1. **Internal Database URL**：只能从 Render 服务内部访问（主机名通常是 `dpg-xxx-a`）
2. **External Connection String**：可以从外部（本地开发环境）访问（主机名通常是 `dpg-xxx-a.oregon-postgres.render.com`）

如果使用内部 URL，本地环境无法解析主机名。

## 解决方案

### 方法1：使用外部连接字符串（推荐）

1. **登录 Render Dashboard**
   - 访问 https://dashboard.render.com/
   - 登录你的账户

2. **进入 PostgreSQL 服务**
   - 在 Dashboard 中找到你的 PostgreSQL 服务
   - 点击进入服务详情页

3. **获取外部连接字符串**
   - 在服务详情页找到 **"Connections"** 标签页
   - 找到 **"External Connection String"** 或 **"Connection Pooling"** 部分
   - 复制外部连接字符串（格式类似：`postgresql://user:password@dpg-xxx-a.oregon-postgres.render.com:5432/database`）

4. **设置环境变量**
   ```powershell
   # PowerShell
   $env:DATABASE_URL="postgresql://user:password@dpg-xxx-a.oregon-postgres.render.com:5432/database"
   ```

5. **运行诊断脚本**
   ```powershell
   python backend\diagnose_chat_history_sync.py --env production
   ```

### 方法2：使用 Render CLI 数据库代理

如果外部连接字符串不可用，可以使用 Render CLI 的数据库代理功能：

1. **安装 Render CLI**
   ```bash
   # Windows (使用 Chocolatey)
   choco install render

   # 或使用 npm
   npm install -g render-cli

   # 或从 GitHub 下载
   # https://github.com/renderinc/cli/releases
   ```

2. **登录 Render CLI**
   ```bash
   render login
   ```

3. **启动数据库代理**
   ```bash
   # 找到你的数据库服务名称（在 Render Dashboard 中）
   render db:proxy <database-service-name>
   ```

   代理启动后会显示本地连接字符串，例如：
   ```
   Proxying database to localhost:5432
   Connection string: postgresql://user:password@localhost:5432/database
   ```

4. **使用代理后的连接字符串**
   ```powershell
   $env:DATABASE_URL="postgresql://user:password@localhost:5432/database"
   python backend\diagnose_chat_history_sync.py --env production
   ```

### 方法3：检查防火墙和网络

如果仍然无法连接：

1. **检查防火墙设置**
   - 确保允许出站连接到 PostgreSQL 端口（通常是 5432）

2. **检查网络连接**
   ```powershell
   # 测试 DNS 解析
   nslookup dpg-xxx-a.oregon-postgres.render.com

   # 测试端口连接
   Test-NetConnection -ComputerName dpg-xxx-a.oregon-postgres.render.com -Port 5432
   ```

3. **检查 Render 服务状态**
   - 在 Render Dashboard 中确认 PostgreSQL 服务正在运行
   - 检查是否有任何服务限制或 IP 白名单设置

## 如何区分内部和外部 URL

### 内部 URL（无法从本地访问）
```
postgresql://user:password@dpg-d5gb82muk2gs739e4in0-a:5432/database
```
- 主机名：`dpg-xxx-a`（没有域名后缀）
- 只能从 Render 服务内部访问

### 外部 URL（可以从本地访问）
```
postgresql://user:password@dpg-d5gb82muk2gs739e4in0-a.oregon-postgres.render.com:5432/database
```
- 主机名：`dpg-xxx-a.oregon-postgres.render.com`（有完整域名）
- 可以从外部（本地开发环境）访问

## 安全提示

⚠️ **重要安全注意事项：**

1. **不要将 DATABASE_URL 提交到 Git**
   - 使用环境变量临时设置
   - 不要将连接字符串写入代码或配置文件

2. **使用后立即清除**
   ```powershell
   # 清除环境变量
   Remove-Item Env:\DATABASE_URL
   ```

3. **限制访问权限**
   - 在 Render Dashboard 中检查数据库的访问控制设置
   - 考虑使用 IP 白名单（如果可用）

## 验证连接

运行诊断脚本验证连接：

```powershell
python backend\diagnose_chat_history_sync.py --env production
```

如果连接成功，你会看到：
```
[OK] 数据库连接成功
数据库类型: PostgreSQL
```
