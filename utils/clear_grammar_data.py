import os
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(REPO_ROOT, 'backend', 'data', 'current')

GRAMMAR_FILE = os.path.join(DATA_DIR, 'grammar.json')
GRAMMAR_NOTATIONS_DIR = os.path.join(DATA_DIR, 'grammar_notations')


def _safe_write_json(path: str, data) -> bool:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 写入失败: {path}: {e}")
        return False


def clear_grammar_rules() -> bool:
    print(f"🧹 清空 Grammar 规则文件: {GRAMMAR_FILE}")
    return _safe_write_json(GRAMMAR_FILE, [])


def clear_grammar_notations() -> bool:
    ok = True
    if not os.path.exists(GRAMMAR_NOTATIONS_DIR):
        print(f"ℹ️ 目录不存在，跳过: {GRAMMAR_NOTATIONS_DIR}")
        return True
    for name in os.listdir(GRAMMAR_NOTATIONS_DIR):
        if not name.endswith('.json'):
            continue
        path = os.path.join(GRAMMAR_NOTATIONS_DIR, name)
        print(f"🧹 清空 Grammar 标注文件: {path}")
        ok = _safe_write_json(path, []) and ok
    return ok


def main():
    print("\n===== 清理 Grammar 数据（mock）=====")
    ok1 = clear_grammar_rules()
    ok2 = clear_grammar_notations()
    if ok1 and ok2:
        print("✅ 已清空 grammar 规则与标注数据。")
        print("⚠️ 如已启动 mock server(8000)，无需重启；前端刷新即可。")
    else:
        print("❌ 清理过程中出现错误，请检查上面的日志。")


if __name__ == '__main__':
    main()


