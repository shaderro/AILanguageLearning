# Scripts

项目根目录下的运维、迁移、检查脚本，按用途分类。**请在项目根目录执行**（脚本会自动 `chdir` 到根目录）。

## 目录结构

| 目录 | 用途 | 示例 |
|------|------|------|
| `admin/` | 数据管理、种子数据、用户操作 | `generate_invite_codes.py`, `seed_preset_articles.py` |
| `migrations/` | 数据库 schema 迁移（Python） | `migrate_add_token_logs_table.py` |
| `sql/` | SQL 迁移与查询脚本 | `migrate_postgresql_schema.sql` |
| `checks/` | 环境检查、验证、测试脚本 | `check_env_config.py`, `test_token_usage_system.py` |
| `tools/` | 数据处理工具 | `split_to_preset_sentences.py` |
| `tests/` | 独立测试脚本 | `chinese_segment/segment_test.py` |

## 常用命令

```powershell
# 环境检查
python scripts/checks/check_env_config.py

# 邀请码
python scripts/admin/generate_invite_codes.py
python scripts/admin/list_invite_codes.py

# 数据库迁移
python scripts/migrations/migrate_add_token_logs_table.py

# 预置文章
python scripts/admin/seed_preset_articles.py --user-id 2
python scripts/admin/sync_preset_articles.py
```

## 启动脚本（保留在根目录）

以下脚本仍在项目根目录，便于日常开发：

- `start_backend.ps1` / `start_frontend.ps1` / `start_app.ps1`
- `kill_port_8000.ps1` / `check_ports.ps1`

## 文档

详细指南见 `docs/guides/`。
