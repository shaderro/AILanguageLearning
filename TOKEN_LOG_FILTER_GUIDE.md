# Token 使用日志过滤指南

## 🎯 日志格式

Token 使用日志的标准格式：
```
💰 [Token Usage] user_id=1 | model=deepseek-chat | prompt_tokens=123 | completion_tokens=45 | total_tokens=168 | balance_after=999832
```

---

## 📋 过滤方法

### 方法 1: PowerShell - Select-String（推荐）

#### 实时过滤（后端运行时）

如果后端直接输出到控制台，可以这样过滤：

```powershell
# 方式 A: 使用管道（如果后端支持）
.\start_backend.ps1 | Select-String -Pattern "Token Usage|💰"

# 方式 B: 使用过滤脚本
.\start_backend.ps1 | .\filter_token_logs.ps1
```

#### 从日志文件过滤

如果后端日志输出到文件：

```powershell
# 读取日志文件并过滤
Get-Content backend.log | Select-String -Pattern "Token Usage|💰"

# 或者使用过滤脚本
.\filter_token_logs.ps1 -LogFile backend.log

# 实时监控日志文件（类似 tail -f）
Get-Content backend.log -Wait | Select-String -Pattern "Token Usage|💰"
```

#### 更精确的过滤

```powershell
# 只显示 token 使用日志
Get-Content backend.log | Select-String -Pattern "💰 \[Token Usage\]"

# 显示特定用户的 token 使用
Get-Content backend.log | Select-String -Pattern "💰 \[Token Usage\].*user_id=1"

# 显示 token 使用并高亮关键信息
Get-Content backend.log | Select-String -Pattern "💰 \[Token Usage\]" | 
    ForEach-Object { 
        Write-Host $_.Line -ForegroundColor Green
    }
```

---

### 方法 2: CMD - findstr

#### 从日志文件过滤

```cmd
REM 基本过滤
findstr /C:"Token Usage" backend.log
findstr /C:"💰" backend.log

REM 组合过滤（包含 Token Usage 或 💰）
findstr /C:"Token Usage" /C:"💰" backend.log

REM 不区分大小写
findstr /I /C:"token usage" backend.log
```

#### 实时过滤（如果后端输出到文件）

```cmd
REM 使用 PowerShell 的实时监控
powershell -Command "Get-Content backend.log -Wait | Select-String -Pattern 'Token Usage'"
```

---

### 方法 3: 使用 grep（如果已安装 Git Bash 或 WSL）

```bash
# 从文件过滤
grep "Token Usage" backend.log
grep "💰" backend.log

# 实时监控（类似 tail -f）
tail -f backend.log | grep "Token Usage"

# 高亮显示
grep --color=always "Token Usage" backend.log
```

---

### 方法 4: 使用 Python 脚本（跨平台）

创建一个简单的过滤脚本：

```python
# filter_token_logs.py
import sys
import re

pattern = re.compile(r'💰.*Token Usage|Token Usage')

for line in sys.stdin:
    if pattern.search(line):
        print(line, end='')
```

使用方法：
```powershell
# 从文件过滤
Get-Content backend.log | python filter_token_logs.py

# 实时过滤
.\start_backend.ps1 | python filter_token_logs.py
```

---

## 🔍 高级过滤示例

### 1. 统计 token 使用总量

```powershell
# 提取 total_tokens 并求和
Get-Content backend.log | 
    Select-String -Pattern "total_tokens=(\d+)" | 
    ForEach-Object { 
        if ($_.Line -match 'total_tokens=(\d+)') {
            [int]$matches[1]
        }
    } | 
    Measure-Object -Sum | 
    Select-Object -ExpandProperty Sum
```

### 2. 按用户分组统计

```powershell
Get-Content backend.log | 
    Select-String -Pattern "💰 \[Token Usage\].*user_id=(\d+).*total_tokens=(\d+)" | 
    ForEach-Object {
        if ($_.Line -match 'user_id=(\d+).*total_tokens=(\d+)') {
            [PSCustomObject]@{
                UserId = $matches[1]
                Tokens = [int]$matches[2]
            }
        }
    } | 
    Group-Object UserId | 
    ForEach-Object {
        $total = ($_.Group | Measure-Object -Property Tokens -Sum).Sum
        Write-Host "用户 $($_.Name): 累计使用 $total tokens"
    }
```

### 3. 显示最近 N 条 token 使用记录

```powershell
Get-Content backend.log | 
    Select-String -Pattern "💰 \[Token Usage\]" | 
    Select-Object -Last 10
```

### 4. 导出到 CSV

```powershell
Get-Content backend.log | 
    Select-String -Pattern "💰 \[Token Usage\].*user_id=(\d+).*total_tokens=(\d+)" | 
    ForEach-Object {
        if ($_.Line -match 'user_id=(\d+).*total_tokens=(\d+)') {
            [PSCustomObject]@{
                UserId = $matches[1]
                TotalTokens = [int]$matches[2]
                Timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
    } | 
    Export-Csv -Path token_usage.csv -NoTypeInformation
```

---

## 🚀 快速命令参考

### PowerShell 一行命令

```powershell
# 基本过滤
Get-Content backend.log | Select-String "Token Usage"

# 实时监控
Get-Content backend.log -Wait | Select-String "Token Usage"

# 只显示 token 数量
Get-Content backend.log | Select-String "total_tokens=\d+"

# 统计出现次数
(Get-Content backend.log | Select-String "Token Usage").Count
```

### CMD 一行命令

```cmd
REM 基本过滤
findstr "Token Usage" backend.log

REM 实时监控（需要 PowerShell）
powershell -Command "Get-Content backend.log -Wait | Select-String 'Token Usage'"
```

---

## 💡 实用技巧

### 1. 将后端日志同时输出到文件和控制台

修改后端启动脚本，添加日志重定向：

```powershell
# 在 start_backend.ps1 中
python -m uvicorn main:app --reload 2>&1 | Tee-Object -FilePath backend.log
```

然后可以：
- 在控制台实时查看所有日志
- 同时保存到 `backend.log` 文件
- 用另一个终端过滤文件

### 2. 使用多个终端

**终端 1**: 运行后端（正常输出）
```powershell
.\start_backend.ps1
```

**终端 2**: 实时过滤日志文件
```powershell
Get-Content backend.log -Wait | Select-String "Token Usage"
```

### 3. 创建别名（PowerShell）

在 PowerShell 配置文件中添加：

```powershell
# 添加到 $PROFILE
function Filter-TokenLogs {
    param([string]$File = "backend.log")
    Get-Content $File -Wait | Select-String "Token Usage"
}

Set-Alias -Name ftoken -Value Filter-TokenLogs
```

然后就可以直接使用：
```powershell
ftoken
ftoken backend.log
```

---

## 📊 示例输出

过滤后的日志示例：

```
💰 [Token Usage] user_id=1 | model=deepseek-chat | prompt_tokens=123 | completion_tokens=45 | total_tokens=168 | balance_after=999832
💰 [Token Usage] user_id=1 | model=deepseek-chat | prompt_tokens=98 | completion_tokens=32 | total_tokens=130 | balance_after=999702
💰 [Token Usage] user_id=2 | model=deepseek-chat | prompt_tokens=156 | completion_tokens=67 | total_tokens=223 | balance_after=999477
```

---

## 🎯 推荐工作流

1. **启动后端时同时保存日志**：
   ```powershell
   .\start_backend.ps1 | Tee-Object -FilePath backend.log
   ```

2. **在另一个终端实时过滤**：
   ```powershell
   Get-Content backend.log -Wait | Select-String "Token Usage"
   ```

3. **需要时查看历史统计**：
   ```powershell
   Get-Content backend.log | Select-String "Token Usage" | Select-Object -Last 20
   ```
