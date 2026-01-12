# 🔧 修复环境变量加载问题

## 问题原因

`python-dotenv` 没有正确安装，导致无法从 `.env` 文件读取环境变量。

## 解决方案

### 方法 1：手动安装 python-dotenv（推荐）

在 PowerShell 中运行：

```powershell
python -m pip install python-dotenv --user
```

或者：

```powershell
pip install python-dotenv
```

### 方法 2：检查 Python 环境

可能安装了多个 Python 版本，确保使用正确的 Python：

```powershell
# 检查当前使用的 Python
python --version
which python

# 检查 pip 对应的 Python
python -m pip --version
```

### 方法 3：临时解决方案（不推荐，仅用于测试）

如果暂时无法安装 `python-dotenv`，可以手动设置系统环境变量：

**Windows PowerShell：**
```powershell
$env:JWT_SECRET="your-secret-key-here"
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:ENV="development"
```

**注意**：这种方式只在当前 PowerShell 会话中有效，关闭后需要重新设置。

## 验证安装

安装完成后，运行：

```powershell
python -c "from dotenv import load_dotenv; print('✅ 安装成功')"
```

如果显示 "✅ 安装成功"，说明安装正确。

## 验证环境变量加载

运行验证脚本：

```powershell
python check_env_config.py
```

应该看到：
```
✅ JWT_SECRET: 已设置
✅ OPENAI_API_KEY: 已设置
✅ ENV: development
```

## 常见问题

### 1. 安装权限问题

如果遇到权限错误，使用 `--user` 参数：

```powershell
python -m pip install --user python-dotenv
```

### 2. 多个 Python 环境

如果项目使用虚拟环境，确保激活虚拟环境后再安装：

```powershell
# 激活虚拟环境（如果有）
.\venv\Scripts\Activate.ps1

# 然后安装
pip install python-dotenv
```

### 3. .env 文件格式问题

确保 `.env` 文件格式正确：
- 每行一个变量
- 格式：`KEY=value`（等号两边不要有空格，除非值需要空格）
- 不要有多余的空格或特殊字符
- 使用 UTF-8 编码

### 4. 路径问题

确保 `.env` 文件在项目根目录：
- 正确位置：`C:\Users\ranxi\AILanguageLearning\.env`
- 与 `backend` 文件夹同级

