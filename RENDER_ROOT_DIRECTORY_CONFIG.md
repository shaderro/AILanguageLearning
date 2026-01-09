# Render Root Directory 配置指南

## 🎯 问题：Root Directory 应该填什么？

根据您的项目结构，**Root Directory 应该留空（或填写 `.`）**，表示使用仓库根目录。

---

## 📁 项目结构分析

您的项目是一个 **monorepo**（单仓库多服务），结构如下：

```
AILanguageLearning-main/          ← 仓库根目录（Root Directory）
├── requirements.txt              ← Python 依赖（在根目录）
├── database_system/              ← 数据库系统（在根目录）
│   ├── database_manager.py
│   └── business_logic/
├── backend/                      ← 后端代码（在根目录）
│   ├── data_managers/
│   ├── assistants/
│   └── preprocessing/
└── frontend/
    └── my-web-ui/
        └── backend/
            └── main.py           ← FastAPI 入口文件 ⭐
```

---

## ✅ 为什么 Root Directory 应该留空？

### 原因 1: `requirements.txt` 在根目录

Render 的 Build Command 需要找到 `requirements.txt`：
```bash
pip install -r requirements.txt
```

如果 Root Directory 不是根目录，这个命令会失败。

### 原因 2: `main.py` 依赖根目录的模块

查看 `frontend/my-web-ui/backend/main.py` 的代码：

```python
# main.py 会自动切换到项目根目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
os.chdir(REPO_ROOT)  # 切换到根目录
```

并且导入根目录的模块：
```python
from database_system.database_manager import DatabaseManager
from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager
```

### 原因 3: 数据库系统在根目录

`database_system/` 目录在根目录，应用需要访问它。

---

## 🔧 Render 配置示例

### 配置 1: Root Directory 留空（推荐）

```
Root Directory:  [留空]  ← 表示使用仓库根目录

Build Command:   pip install -r requirements.txt
Start Command:   uvicorn frontend.my-web-ui.backend.main:app --host 0.0.0.0 --port $PORT
```

**优点**:
- ✅ 简单直接
- ✅ `requirements.txt` 可以被找到
- ✅ 所有模块路径正确
- ✅ 符合 `main.py` 的路径切换逻辑

### 配置 2: Root Directory 填写 `.`（等价于留空）

```
Root Directory:  .

Build Command:   pip install -r requirements.txt
Start Command:   uvicorn frontend.my-web-ui.backend.main:app --host 0.0.0.0 --port $PORT
```

**说明**: `.` 表示当前目录，对于仓库根目录来说，等同于留空。

---

## ❌ 不推荐的配置

### 错误配置 1: 设置为 `frontend/my-web-ui/backend`

```
Root Directory:  frontend/my-web-ui/backend  ❌

问题:
- ❌ Build Command 找不到 `requirements.txt`（在根目录）
- ❌ 无法导入 `database_system` 模块
- ❌ 无法导入 `backend` 模块
```

### 错误配置 2: 设置为 `frontend/my-web-ui`

```
Root Directory:  frontend/my-web-ui  ❌

问题:
- ❌ Build Command 找不到 `requirements.txt`（在根目录）
- ❌ 无法导入 `database_system` 模块（在根目录）
- ❌ 无法导入 `backend` 模块（在根目录）
```

---

## 📝 完整的 Render 配置清单

### 基本设置

| 配置项 | 值 |
|--------|-----|
| **Name** | `language-learning-api` |
| **Root Directory** | `[留空]` 或 `.` |
| **Region** | 选择与数据库相同的区域 |
| **Branch** | `main` 或 `master` |
| **Runtime** | `Python 3` |

### 构建和启动命令

| 配置项 | 值 |
|--------|-----|
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn frontend.my-web-ui.backend.main:app --host 0.0.0.0 --port $PORT` |

### 环境变量

```
DATABASE_URL=postgresql://user:password@host:5432/dbname
ENV=production
JWT_SECRET=your_jwt_secret
OPENAI_API_KEY=sk-your-openai-key
```

---

## 🔍 验证配置是否正确

部署后，检查日志确认：

### 1. Build Command 是否成功

日志中应该看到：
```
Installing requirements from requirements.txt
Successfully installed fastapi uvicorn sqlalchemy ...
```

如果看到错误：
```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

**解决方案**: Root Directory 必须设置为根目录（留空）。

### 2. 应用是否成功启动

日志中应该看到：
```
INFO:     Uvicorn running on http://0.0.0.0:PORT
INFO:     Application startup complete.
```

如果看到导入错误：
```
ModuleNotFoundError: No module named 'database_system'
```

**解决方案**: 
- 确保 Root Directory 是根目录
- 确保 `main.py` 的路径切换逻辑正确

### 3. 数据库连接是否成功

查看日志是否有数据库连接信息（不显示密码）：
```
[OK] 工作目录已切换: ... -> /opt/render/project/src
Database connection successful
```

---

## 🎯 快速检查清单

- [ ] Root Directory 留空（或填写 `.`）
- [ ] Build Command 使用 `pip install -r requirements.txt`
- [ ] Start Command 使用完整路径：`frontend.my-web-ui.backend.main:app`
- [ ] 环境变量 `DATABASE_URL` 已设置
- [ ] 所有依赖的模块都在根目录可访问范围内

---

## 💡 提示

### 如果您的项目结构不同

如果您的 FastAPI 入口文件在根目录（例如 `main.py` 或 `app.py` 在根目录），则：

```
Root Directory:  [留空]
Start Command:   uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 如果是纯后端项目（没有 frontend 目录）

如果后端代码独立部署，结构如下：
```
backend/
├── main.py
├── requirements.txt
└── ...
```

则：
```
Root Directory:  [留空]  （如果仓库根就是 backend）
Start Command:   uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 📚 参考

- [Render 官方文档 - Root Directory](https://render.com/docs/configure-root-directory)
- 您的项目结构: `AILanguageLearning-main/`
- FastAPI 入口: `frontend/my-web-ui/backend/main.py`

---

**总结**: 对于您的项目，**Root Directory 应该留空**，Render 会自动使用仓库根目录。
