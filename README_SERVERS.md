# 服务器快速参考

## 🎯 一句话总结

**你有2个server.py，90%的时候应该用根目录的（端口8001）！**

---

## 📁 两个服务器

### ⭐ 主后端API - `server.py`

```
位置：项目根目录
端口：8001
用途：真实后端API + 数据库
启动：cd C:\Users\Mayn\AILanguageLearning-main && python server.py
文档：http://localhost:8001/docs
```

### 🔴 Mock服务器 - `server_frontend_mock.py`

```
位置：frontend\my-web-ui\backend\
端口：8000
用途：前端开发Mock数据
启动：cd frontend\my-web-ui\backend && python server_frontend_mock.py
```

---

## ✅ 快速启动（查看详细日志）

```powershell
# 1. 切换目录
cd C:\Users\Mayn\AILanguageLearning-main

# 2. 启动服务器（保持窗口可见）
python server.py

# 3. 浏览器访问
http://localhost:8001/api/v2/vocab-verbose/1

# 4. 立即切回PowerShell窗口查看日志！
```

---

## 🔍 检查

```powershell
# 看到8001 = ✅ 正确
# 看到8000 = ❌ 目录错了，回到根目录
```

---

## 📚 详细文档

- `WHICH_SERVER_TO_USE.md` - 完整对比
- `PORT_EXPLAINED.md` - 端口科普
- `SERVERS_MANAGEMENT.md` - 管理指南

