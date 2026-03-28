# Preset Articles Guide

## 1. 作用

`preset articles` 是系统内置的预置阅读文章。

它们不是前端“上传文章”按钮上传进去的，而是通过后端的 JSON 文件 + seed 脚本导入数据库。

## 2. 当前支持语言

当前 preset seed 已支持以下 9 种语言代码：

- `zh`：中文
- `en`：英文
- `de`：德文
- `es`：西班牙语
- `fr`：法语
- `ja`：日语
- `ko`：韩语
- `ar`：阿拉伯语
- `ru`：俄语

## 3. 目录位置

预置文章文件统一放在：

`backend/data/presets/articles/<language_code>/`

例如：

- `backend/data/presets/articles/de/`
- `backend/data/presets/articles/en/`
- `backend/data/presets/articles/zh/`
- `backend/data/presets/articles/es/`

推荐每篇文章一个 JSON 文件。

## 4. JSON 格式

最简单的格式如下：

```json
{
  "preset_id": "de_b1_fahrrad",
  "language_code": "de",
  "title": "Fahrrad",
  "difficulty": "intermediate",
  "sentences": [
    "Ein Fahrrad ist ein Verkehrsmittel, das viele Menschen jeden Tag benutzen.",
    "Es ist praktisch, um kurze Strecken in der Stadt zurückzulegen.",
    "Außerdem ist Radfahren gesund und umweltfreundlich."
  ]
}
```

字段说明：

- `preset_id`：预置文章唯一标识，建议全局唯一
- `language_code`：语言代码，例如 `de`
- `title`：文章标题
- `difficulty`：文章难度，当前常见值为 `beginner` / `intermediate` / `advanced`
- `sentences`：句子数组

`sentences` 也支持对象格式，可为每句单独写难度：

```json
{
  "preset_id": "de_b1_fahrrad",
  "language_code": "de",
  "title": "Fahrrad",
  "difficulty": "intermediate",
  "sentences": [
    {
      "sentence": "Ein Fahrrad ist ein Verkehrsmittel, das viele Menschen jeden Tag benutzen.",
      "difficulty": "intermediate"
    },
    {
      "sentence": "Es ist praktisch, um kurze Strecken in der Stadt zurückzulegen.",
      "difficulty": "intermediate"
    }
  ]
}
```

## 5. 导入方式

### 给单个用户导入

在项目根目录执行：

```bash
python seed_preset_articles.py --user-id 你的用户ID --languages de
```

例如：

```bash
python seed_preset_articles.py --user-id 2 --languages de
```

如果要一次导入多个语言：

```bash
python seed_preset_articles.py --user-id 2 --languages de,fr,es
```

### 给所有用户导入

```bash
python seed_preset_articles_for_all.py --languages de
```

例如一次导入多种语言：

```bash
python seed_preset_articles_for_all.py --languages de,en,zh
```

如果不传 `--languages`，会按当前支持语言全部导入。

## 6. 导入逻辑说明

- seed 脚本会扫描 `backend/data/presets/articles` 下的 JSON 文件
- 导入时会按 `language_code` 过滤
- 若同一用户下已存在同标题文章，则会跳过，避免重复导入
- 句子导入后会自动尝试生成 token / word token
- 非空内容语言会按对应语言进入后续阅读流程

## 7. 与“普通上传文章”的区别

普通上传文章：

- 走前端上传入口
- 由用户手动上传全文
- 不属于 preset seed

preset articles：

- 由开发者在仓库内添加 JSON
- 通过 seed 脚本批量导入数据库
- 适合做系统默认示例文章

## 8. 注意事项

- 推荐只保留语言子目录中的文件，不建议把相同 JSON 同时放在根目录和子目录
- `preset_id` 建议保持唯一，避免后续维护混乱
- `title` 不要和同一用户已有预置文章重复，否则 seed 时会被跳过
- 文章内容建议按句切分后写入 `sentences`
- 如果要新增更多语言，需同步检查 `backend/data_managers/preset_articles.py`

## 9. 相关代码位置

- `backend/data_managers/preset_articles.py`
- `seed_preset_articles.py`
- `seed_preset_articles_for_all.py`

