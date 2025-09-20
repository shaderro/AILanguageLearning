#  语言学习应用 - 浏览器运行指南

**项目**: React + FastAPI 语言学习应用  
**创建日期**: 2025年1月  
**技术栈**: React 19 + Vite + TailwindCSS + FastAPI

##  系统要求

在开始之前，请确保你的系统已安装：

- **Node.js** (推荐版本 16+)
- **Python 3** (推荐版本 3.8+)
- **npm** (通常随 Node.js 一起安装)
- **pip** (Python 包管理器)

##  快速启动方法

### 方法一：一键启动脚本（推荐）

1. **打开终端/命令行**
2. **进入项目目录**：
   `ash
   cd frontend/my-web-ui
   `
3. **运行启动脚本**：
   `ash
   ./start-demo.sh
   `
4. **按照脚本提示操作**

### 方法二：手动启动（分步操作）

#### 第一步：启动后端服务

1. **打开终端/命令行**
2. **进入后端目录**：
   `ash
   cd frontend/my-web-ui/backend
   `
3. **安装Python依赖**：
   `ash
   pip install -r requirements.txt
   `
4. **启动后端服务**：
   `ash
   python main.py
   `

**成功标志**：看到类似以下输出
`
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
`

#### 第二步：启动前端服务

1. **打开新的终端窗口**
2. **进入前端目录**：
   `ash
   cd frontend/my-web-ui
   `
3. **安装前端依赖**：
   `ash
   npm install
   `
4. **启动开发服务器**：
   `ash
   npm run dev
   `

**成功标志**：看到类似以下输出
`
  VITE v7.1.2  ready in 1234 ms

    Local:   http://localhost:5173/
    Network: use --host to expose
`

##  访问应用

启动成功后，在浏览器中访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端应用** | http://localhost:5173 | 主要的用户界面 |
| **后端API** | http://localhost:8000 | API服务 |
| **API文档** | http://localhost:8000/docs | 交互式API文档 |

##  应用功能

### 1. 单词学习模块
- 单词卡片展示
- 交互式复习功能
- 学习进度统计

### 2. 语法学习模块
- 语法规则学习
- 详细语法说明
- 例句展示

### 3. 文章阅读模块
- 文章阅读器
- AI聊天助手
- 词汇解释功能
- 文件上传功能

### 4. 数据统计
- 学习进度跟踪
- 收藏功能
- 统计数据展示

##  常用命令

### 前端命令
`ash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 代码检查
npm run lint
`

### 后端命令
`ash
# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py

# 或者使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
`

##  常见问题解决

### 1. 端口被占用
如果遇到端口冲突，可以：

**修改前端端口**：
`ash
npm run dev -- --port 3000
`

**修改后端端口**：
编辑 ackend/main.py 文件，修改最后一行：
`python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为8001或其他端口
`

### 2. 依赖安装失败

**Python依赖问题**：
`ash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 或者升级pip
python -m pip install --upgrade pip
`

**Node.js依赖问题**：
`ash
# 清除缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install
`

### 3. 跨域问题
如果遇到CORS错误，检查 ackend/main.py 中的CORS配置：
`python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
`

### 4. 服务无法启动
- 确保Python和Node.js版本符合要求
- 检查防火墙设置
- 确保端口未被其他程序占用

##  项目结构

`
frontend/my-web-ui/
 src/                    # 前端源码
    modules/           # 功能模块
       word-demo/     # 单词学习
       grammar-demo/  # 语法学习
       article/       # 文章阅读
       shared/        # 共享组件
    hooks/             # React Hooks
    services/          # API服务
    App.jsx           # 主应用
 backend/               # 后端服务
    main.py           # 主程序
    models.py         # 数据模型
    services.py       # 业务逻辑
    requirements.txt  # Python依赖
 package.json          # 前端依赖
 start-demo.sh         # 启动脚本
`

##  开发模式

### 热重载
- 前端：修改代码后自动刷新浏览器
- 后端：使用 --reload 参数自动重启服务

### 调试
- 前端：使用浏览器开发者工具
- 后端：查看终端输出的日志信息

##  注意事项

1. **同时运行**：前端和后端需要同时运行才能正常工作
2. **网络连接**：确保网络连接正常，某些依赖可能需要从网络下载
3. **权限问题**：在某些系统上可能需要管理员权限来安装依赖
4. **版本兼容**：建议使用推荐的Node.js和Python版本

##  停止服务

要停止服务，在对应的终端窗口中按 Ctrl + C（Windows/Linux）或 Cmd + C（Mac）。

##  获取帮助

如果遇到问题：
1. 检查终端输出的错误信息
2. 查看浏览器控制台的错误信息
3. 确认所有依赖都已正确安装
4. 检查端口是否被占用

---

**最后更新**: 2025年1月  
**版本**: 1.0.0  
**状态**: 可用
