# Backend 后端功能模块

这个目录包含了语言学习应用的所有后端功能，已经过清理，移除了不必要的测试和文档文件。

## 目录结构

- **assistants/**: AI助手模块
  - 主助手和子助手实现
  - 对话历史管理
  - 语法和词汇分析助手

- **data_managers/**: 数据管理模块
  - 数据类定义
  - 对话记录管理
  - 语法规则管理
  - 词汇管理
  - 原始文本管理

- **preprocessing/**: 数据预处理模块
  - 文章处理器
  - 句子处理器
  - 词汇处理器
  - 难度评估

- **data/**: 数据存储
  - current/: 当前数据文件
  - backup/: 备份数据（legacy, versions）
  - article/: 文章数据

## 主要文件

- `main.py`: 主程序入口（演示程序）
- `integrated_language_system.py`: 集成语言系统（完整功能）
- `README.md`: 本说明文件

## 运行方式

### 运行演示程序
```bash
cd backend
python3 main.py
```

### 运行集成系统
```bash
cd backend
python3 -c "
import sys; sys.path.append('.')
from integrated_language_system import IntegratedLanguageSystem
system = IntegratedLanguageSystem()
print('集成系统初始化完成')
"
```

### 使用虚拟环境
```bash
# 激活虚拟环境
source venv/bin/activate

# 进入backend目录
cd backend

# 运行程序
python3 main.py
```

## 清理说明

已删除的不必要文件：
- ✅ 测试文件（test_*.py）
- ✅ 示例文件（example_*.py）
- ✅ 功能文档（*_features.md）
- ✅ 报告文档（*_report.md）
- ✅ Python缓存（__pycache__/）
- ✅ 系统文件（.DS_Store）
- ✅ 测试数据（data/backup/test/）

## 注意事项

1. **Python路径**: 需要在backend目录下运行，或者将backend目录添加到Python路径
2. **依赖包**: 需要安装requirements.txt中的所有依赖包
3. **虚拟环境**: 建议使用虚拟环境来避免包冲突
4. **数据文件**: 主程序需要数据文件才能完全运行
