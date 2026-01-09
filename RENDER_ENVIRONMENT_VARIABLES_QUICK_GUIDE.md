# Render 环境变量设置 - 快速查找指南

## 🎯 目标：找到环境变量设置入口

---

## 方法 1️⃣：在创建服务时设置（推荐，最简单）

### 步骤：

1. 登录 Render: https://dashboard.render.com

2. 点击 **New +** → **Web Service**

3. 连接 Git 仓库后，填写服务配置表单

4. **向下滚动页面**，找到表单底部

5. 看到 **"Environment Variables"** 区域

6. 点击 **"Add Environment Variable"** 按钮

7. 输入：
   - **Key**: `DATABASE_URL`
   - **Value**: 粘贴数据库连接字符串

8. 继续添加其他变量（ENV, JWT_SECRET 等）

9. 最后点击 **"Create Web Service"**

✅ **优点**: 一次完成，不需要后续再找设置

---

## 方法 2️⃣：在已创建的服务中设置

### 导航路径：

```
Render 仪表板
  └── 点击服务名称（左侧服务列表或主页）
      └── 服务详情页顶部标签
          └── 点击 "Settings" 标签 ⭐
              └── 向下滚动
                  └── 找到 "Environment Variables" 部分
                      └── 点击 "Add Environment Variable"
```

### 详细步骤：

#### 步骤 1: 进入服务页面

1. 在 Render 仪表板主页，您会看到服务列表
2. 点击您要配置的服务名称（蓝色链接）
3. 进入服务详情页面

#### 步骤 2: 找到 Settings 标签

在服务详情页面顶部，您会看到多个标签页：

```
[Logs]  [Events]  [Metrics]  [Settings] ⭐ 点击这个
```

**如果没有看到 Settings 标签**：
- 可能是页面正在加载，等待几秒
- 刷新页面（F5 或 Ctrl+R）
- 检查浏览器是否阻止了某些内容

#### 步骤 3: 在 Settings 页面找到环境变量

1. 点击 **Settings** 标签后
2. 页面会显示服务配置信息
3. **向下滚动**（很重要！环境变量通常在页面下方）
4. 找到 **"Environment Variables"** 标题
5. 下面应该有一个表格或列表，显示现有的环境变量
6. 如果没有变量，会显示 "No environment variables" 或类似提示

#### 步骤 4: 添加环境变量

1. 找到 **"Add Environment Variable"** 或 **"+ Add"** 按钮
2. 点击按钮，会弹出输入框
3. 输入：
   - **Key**（键）: `DATABASE_URL`
   - **Value**（值）: `postgresql://user:pass@host:5432/dbname`
4. 点击 **"Save"** 或 **"Add"**
5. 重复步骤添加其他变量

---

## 方法 3️⃣：使用数据库链接功能（最简单！）

如果您已经创建了 PostgreSQL 数据库和 Web Service：

### 步骤：

1. **进入 PostgreSQL 数据库页面**：
   - 在 Render 仪表板，点击您的数据库名称
   - 进入数据库详情页

2. **找到 "Connections" 部分**：
   - 在数据库详情页中，向下滚动
   - 找到 **"Connections"** 或 **"Linked Services"** 部分

3. **链接到 Web Service**：
   - 点击 **"Link"** 或 **"Connect"** 按钮
   - 选择您创建的 Web Service
   - 确认链接

4. **完成！**：
   - Render 会自动将数据库连接信息注入为 `DATABASE_URL` 环境变量
   - 不需要手动复制粘贴！

✅ **这是最推荐的方法**，因为它自动完成配置，避免复制错误

---

## 方法 4️⃣：使用 Render CLI（命令行）

如果您熟悉命令行：

### 安装 CLI：

```bash
# 使用 npm
npm install -g render-cli

# 或使用 Homebrew (Mac)
brew install render

# 或下载二进制文件
# https://github.com/renderinc/cli
```

### 使用 CLI 设置环境变量：

```bash
# 登录
render login

# 设置环境变量
render env set DATABASE_URL "postgresql://user:pass@host:5432/dbname" --service your-service-name

# 查看所有环境变量
render env ls --service your-service-name
```

---

## 🔍 如果还是找不到怎么办？

### 检查清单：

- [ ] 您已经创建了 Web Service（环境变量只能在服务中设置）
- [ ] 您已经登录了正确的 Render 账户
- [ ] 浏览器页面已完全加载（等待几秒或刷新）
- [ ] 您有该服务的编辑权限（如果是团队项目）

### 尝试这些方法：

1. **刷新页面**：按 F5 或 Ctrl+R

2. **清除浏览器缓存**：Ctrl+Shift+Delete

3. **使用不同的浏览器**：Chrome、Firefox、Edge

4. **检查 URL**：
   - 确保您在正确的服务页面
   - URL 应该类似：`https://dashboard.render.com/web/[service-name]`

5. **查看 Render 文档**：
   - https://render.com/docs/environment-variables
   - 可能有界面更新

6. **联系 Render 支持**：
   - 在 Render 仪表板右下角有 "Help" 或 "Support" 按钮

---

## 📸 界面元素识别

### 您应该看到的界面元素：

#### 创建服务时的界面：
```
[服务配置表单...]
┌─────────────────────────────────┐
│ Environment Variables            │
│                                  │
│ [Add Environment Variable] 按钮  │
│                                  │
│ Key: [输入框]                    │
│ Value: [输入框]                  │
└─────────────────────────────────┘
```

#### Settings 页面的界面：
```
[服务信息...]
┌─────────────────────────────────┐
│ Environment Variables            │
│                                  │
│ Key              Value           │
│ DATABASE_URL     postgresql://...│
│                                  │
│ [+ Add] 按钮                     │
└─────────────────────────────────┘
```

---

## ✅ 验证环境变量是否设置成功

设置完成后，可以通过以下方式验证：

1. **查看服务日志**：
   - 进入服务页面 → **Logs** 标签
   - 查看应用启动日志，应该能看到数据库连接信息（不显示密码）

2. **在代码中打印**（临时测试）：
   ```python
   import os
   print("DATABASE_URL exists:", bool(os.getenv('DATABASE_URL')))
   # 注意：不要打印完整的 DATABASE_URL，包含密码！
   ```

3. **测试数据库连接**：
   - 访问您的 API 端点
   - 查看是否能正常连接数据库

---

## 🎯 推荐流程总结

**最简单的方式（按顺序尝试）：**

1. ✅ **首先尝试方法 3**：使用数据库链接功能（最简单）
2. ✅ **其次方法 1**：在创建服务时添加（如果还没创建）
3. ✅ **最后方法 2**：在 Settings 标签中手动添加

如果这些都不行，使用方法 4（CLI）或联系 Render 支持。

---

**需要帮助？** 查看完整文档：`POSTGRESQL_CLOUD_DEPLOYMENT.md`
