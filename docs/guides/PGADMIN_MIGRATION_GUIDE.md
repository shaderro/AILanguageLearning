# pgAdmin PostgreSQL 数据库迁移指南

## 📋 概述

本指南将帮助您使用 pgAdmin 将线上 PostgreSQL 数据库迁移到新的数据结构。

## 🎯 迁移目标

### 1. grammar_rules 表新增字段
- `display_name` (VARCHAR(255), nullable)
- `canonical_category` (VARCHAR(255), nullable)
- `canonical_subtype` (VARCHAR(255), nullable)
- `canonical_function` (VARCHAR(255), nullable)
- `canonical_key` (VARCHAR(255), nullable)

### 2. sentences 表新增字段
- `paragraph_id` (INTEGER, nullable)
- `is_new_paragraph` (BOOLEAN, default FALSE, nullable)

### 3. grammar_notations 表唯一约束更新
- **旧约束**: `UNIQUE(user_id, text_id, sentence_id)`
- **新约束**: `UNIQUE(user_id, text_id, sentence_id, grammar_id)`
- **目的**: 允许同一句子有多个不同的语法知识点（只要 grammar_id 不同）

## ⚠️ 迁移前准备

### 1. 备份数据库

**在 pgAdmin 中执行备份：**

1. 右键点击数据库 → **Backup...**
2. 设置备份选项：
   - **Filename**: `backup_before_migration_YYYYMMDD.dump`
   - **Format**: `Custom` 或 `Plain`
   - **Encoding**: `UTF8`
3. 点击 **Backup** 按钮
4. 等待备份完成

**或使用命令行：**

```bash
pg_dump -h your_host -U your_user -d your_database -F c -f backup_before_migration.dump
```

### 2. 确认数据库连接

- 确保可以正常连接到生产数据库
- 确认有足够的权限执行 ALTER TABLE 操作
- 建议在维护窗口期间执行

## 📝 执行迁移步骤

### 方法1：使用 pgAdmin Query Tool（推荐）

1. **打开 pgAdmin**
   - 连接到您的 PostgreSQL 服务器
   - 展开数据库树，找到目标数据库

2. **打开 Query Tool**
   - 右键点击数据库 → **Query Tool**
   - 或点击工具栏的 **Query Tool** 图标

3. **打开迁移脚本**
   - 在 Query Tool 中，点击 **Open File** 按钮（📁）
   - 选择迁移脚本文件：
     - `scripts/sql/migrate_postgresql_schema.sql` - 用于 grammar_rules 和 sentences 表字段迁移
     - `scripts/sql/migrate_postgresql_grammar_notation_pgadmin.sql` - **用于 grammar_notations 表唯一约束迁移（推荐）**

4. **检查脚本内容**
   - 确认脚本中的表名和字段名正确
   - 确认没有硬编码的数据库名称

5. **执行脚本**
   - 点击 **Execute** 按钮（▶️）或按 `F5`
   - 等待执行完成

6. **查看执行结果**
   - 在 **Messages** 标签页查看执行日志
   - 确认所有字段都已成功添加
   - 检查是否有错误或警告

### 方法2：使用 psql 命令行

```bash
# 连接到数据库
psql -h your_host -U your_user -d your_database

# 执行迁移脚本
\i scripts/sql/migrate_postgresql_schema.sql

# 或直接执行
psql -h your_host -U your_user -d your_database -f scripts/sql/migrate_postgresql_schema.sql
```

### 方法3：执行 grammar_notations 表唯一约束迁移

**重要：** 此迁移允许同一句子有多个不同的语法知识点。

1. **打开迁移脚本**
   - 在 Query Tool 中打开 `scripts/sql/migrate_postgresql_grammar_notation_pgadmin.sql`

2. **检查数据**
   - 执行前检查是否有重复数据：
   ```sql
   -- 检查是否有违反新约束的数据
   SELECT user_id, text_id, sentence_id, grammar_id, COUNT(*) as count
   FROM grammar_notations
   WHERE grammar_id IS NOT NULL
   GROUP BY user_id, text_id, sentence_id, grammar_id
   HAVING COUNT(*) > 1;
   ```
   - 如果返回结果，需要先清理重复数据

3. **执行迁移**
   - 点击 **Execute** 按钮（▶️）或按 `F5`
   - 脚本会自动：
     - 检查当前约束状态
     - 删除旧约束（如果不包含 grammar_id）
     - 创建新约束（包含 grammar_id）
     - 验证迁移结果

4. **查看执行结果**
   - 在 **Messages** 标签页查看详细日志
   - 确认看到 "✅ 迁移成功！" 消息
   - 检查约束定义是否正确

## ✅ 验证迁移结果

### 1. 检查 grammar_rules 表结构

在 Query Tool 中执行：

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'grammar_rules'
  AND column_name IN ('display_name', 'canonical_category', 'canonical_subtype', 'canonical_function', 'canonical_key')
ORDER BY column_name;
```

**预期结果：** 应该返回 5 行，每行对应一个新字段。

### 2. 检查 sentences 表结构

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'sentences'
  AND column_name IN ('paragraph_id', 'is_new_paragraph')
ORDER BY column_name;
```

**预期结果：** 应该返回 2 行。

### 3. 检查数据回填

```sql
-- 检查 display_name 回填情况
SELECT 
    COUNT(*) as total_rules,
    COUNT(display_name) as rules_with_display_name,
    COUNT(canonical_key) as rules_with_canonical_key
FROM grammar_rules;
```

**预期结果：** 
- `total_rules`: 总记录数
- `rules_with_display_name`: 应该等于 `total_rules`（已回填）
- `rules_with_canonical_key`: 可能为 0（新数据会逐步填充）

### 4. 检查数据完整性

```sql
-- 检查是否有数据损坏
SELECT COUNT(*) FROM grammar_rules WHERE rule_name IS NULL;
SELECT COUNT(*) FROM sentences WHERE sentence_body IS NULL;
```

**预期结果：** 两个查询都应该返回 0。

### 5. 检查 grammar_notations 表唯一约束

```sql
-- 检查唯一约束是否包含 grammar_id
SELECT 
    conname AS constraint_name,
    pg_get_constraintdef(oid) AS constraint_definition,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM pg_attribute a
            WHERE a.attrelid = c.conrelid
            AND a.attnum = ANY(c.conkey)
            AND a.attname = 'grammar_id'
        ) THEN '✅ 包含 grammar_id'
        ELSE '❌ 不包含 grammar_id'
    END AS status
FROM pg_constraint c
WHERE conrelid = 'grammar_notations'::regclass
AND contype = 'u'
ORDER BY conname;
```

**预期结果：** 
- 应该返回至少一行
- `status` 列应该显示 `✅ 包含 grammar_id`
- `constraint_definition` 应该包含 `(user_id, text_id, sentence_id, grammar_id)`

## 🔄 回滚方案

如果迁移出现问题，可以回滚：

### 1. 删除新添加的字段

```sql
BEGIN;

-- 删除 grammar_rules 表的新字段
ALTER TABLE grammar_rules DROP COLUMN IF EXISTS display_name;
ALTER TABLE grammar_rules DROP COLUMN IF EXISTS canonical_category;
ALTER TABLE grammar_rules DROP COLUMN IF EXISTS canonical_subtype;
ALTER TABLE grammar_rules DROP COLUMN IF EXISTS canonical_function;
ALTER TABLE grammar_rules DROP COLUMN IF EXISTS canonical_key;

-- 删除 sentences 表的新字段
ALTER TABLE sentences DROP COLUMN IF EXISTS paragraph_id;
ALTER TABLE sentences DROP COLUMN IF EXISTS is_new_paragraph;

COMMIT;
```

### 2. 恢复备份

如果删除字段无法解决问题，恢复备份：

1. 在 pgAdmin 中：右键点击数据库 → **Restore...**
2. 选择备份文件
3. 点击 **Restore**

或使用命令行：

```bash
pg_restore -h your_host -U your_user -d your_database backup_before_migration.dump
```

## 🐛 常见问题

### 问题1：字段已存在错误

**错误信息：** `column "display_name" already exists`

**解决方案：** 
- 脚本已包含检查逻辑，会自动跳过已存在的字段
- 这是正常情况，不影响迁移

### 问题2：权限不足

**错误信息：** `permission denied for table grammar_rules`

**解决方案：**
- 确认当前用户有 ALTER TABLE 权限
- 联系数据库管理员授予权限

### 问题3：表不存在

**错误信息：** `relation "grammar_rules" does not exist`

**解决方案：**
- 确认表名正确
- 确认在正确的数据库中执行
- 检查 schema 名称（默认是 `public`）

### 问题4：事务冲突

**错误信息：** `could not obtain lock on table`

**解决方案：**
- 等待其他操作完成
- 在维护窗口期间执行
- 检查是否有长时间运行的事务

### 问题5：唯一约束冲突（grammar_notations 迁移）

**错误信息：** `duplicate key value violates unique constraint`

**解决方案：**
- 检查是否有重复数据：`SELECT user_id, text_id, sentence_id, grammar_id, COUNT(*) FROM grammar_notations GROUP BY user_id, text_id, sentence_id, grammar_id HAVING COUNT(*) > 1;`
- 如果有重复数据，需要先清理重复记录
- 确保 `grammar_id` 字段不为 NULL（如果为 NULL，需要先处理）

## 📊 迁移后检查清单

- [ ] 备份已创建
- [ ] 迁移脚本执行成功
- [ ] grammar_rules 表新增 5 个字段
- [ ] sentences 表新增 2 个字段
- [ ] **grammar_notations 表唯一约束已更新（包含 grammar_id）**
- [ ] display_name 已回填
- [ ] 数据完整性检查通过
- [ ] 应用程序测试通过

## 🔗 相关文件

- `scripts/sql/migrate_postgresql_schema.sql` - PostgreSQL 迁移脚本（grammar_rules 和 sentences 表）
- `scripts/sql/migrate_postgresql_grammar_notation_pgadmin.sql` - **GrammarNotation 唯一约束迁移脚本（推荐使用）**
- `scripts/sql/migrate_postgresql_grammar_notation_constraint.sql` - GrammarNotation 唯一约束迁移脚本（旧版本）
- `migrate_grammar_rules.py` - SQLite 迁移脚本（参考）
- `migrate_sentences_add_paragraph_columns.py` - 段落字段迁移脚本（参考）

## 📞 支持

如果遇到问题，请：
1. 检查错误日志
2. 查看 pgAdmin 的 Messages 标签页
3. 参考本文档的常见问题部分
4. 联系开发团队

---

**最后更新：** 2025年1月

