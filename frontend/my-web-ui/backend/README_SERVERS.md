# Backend服务器说明

## 📁 文件说明

### server_frontend_mock.py (原server.py)

**端口：** 8000  
**用途：** 前端独立开发时的Mock API服务器  
**特点：**
- 不需要真实数据库
- 提供模拟数据
- 用于前端快速开发和原型设计
- 包含完整的SessionState和数据管理模拟

**启动方式：**
```powershell
cd frontend\my-web-ui\backend
python server_frontend_mock.py
```

**访问：**
```
http://localhost:8000
```

**使用场景：**
- 前端开发者独立工作，不想启动完整后端
- 快速原型和UI开发
- 不需要真实数据的功能测试

---

## ⚠️ 注意

### 真实后端API服务器在项目根目录！

**文件：** `C:\Users\Mayn\AILanguageLearning-main\server.py`  
**端口：** 8001  
**用途：** 生产和真实开发用的后端API  

**启动方式：**
```powershell
# 在项目根目录
cd C:\Users\Mayn\AILanguageLearning-main
python server.py
```

---

## 🔄 两个服务器的关系

```
前端开发模式（使用Mock数据）
┌─────────────────┐
│  Frontend UI    │
│  (port 5173)    │
└────────┬────────┘
         │ API调用
         ↓
┌─────────────────┐
│  Mock API       │
│  (port 8000)    │ ← server_frontend_mock.py
│  返回假数据      │
└─────────────────┘


生产模式（使用真实数据库）
┌─────────────────┐
│  Frontend UI    │
│  (port 5173)    │
└────────┬────────┘
         │ API调用
         ↓
┌─────────────────┐
│  Real API       │
│  (port 8001)    │ ← ../../server.py (根目录)
└────────┬────────┘
         │ 查询
         ↓
┌─────────────────┐
│  Database       │
│  (SQLite)       │
└─────────────────┘
```

---

## 📚 相关文档

- `YOUR_PROJECT_PORTS.md` - 端口使用说明
- `PORT_EXPLAINED.md` - 端口概念详解
- `CORRECT_SERVER_START.md` - 正确启动方法

