# Token 使用日志过滤脚本
# 使用方法：
#   1. 如果后端输出到控制台，直接运行此脚本，然后启动后端
#   2. 或者将后端日志重定向到文件，然后用此脚本过滤文件

param(
    [string]$LogFile = $null
)

# 如果提供了日志文件，从文件读取；否则从管道读取
if ($LogFile) {
    Get-Content $LogFile | Select-String -Pattern "Token Usage|💰.*Token"
} else {
    # 从标准输入读取（用于管道）
    $input | Select-String -Pattern "Token Usage|💰.*Token"
}
