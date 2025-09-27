from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

# 导入自定义模�?from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response
import os
from datetime import datetime

# 计算 real_data_raw/result 目录（相对本文件位置�?RESULT_DIR = os.path.abspath(
os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend", "data", "current", "articles")
)

def _ensure_result_dir() -> str:
    os.makedirs(RESULT_DIR, exist_ok=True)
    return RESULT_DIR

def _parse_timestamp_from_filename(name: str) -> str:
    # 形如: hp1_processed_20250916_123831.json
    try:
        ts = name.rsplit("_", 2)[-2:]  # [YYYYMMDD, HHMMSS.json]
        ts_s = ts[0] + "_" + ts[1].replace(".json", "")
        # 返回 ISO-ish 格式
        dt = datetime.strptime(ts_s, "%Y%m%d_%H%M%S")
        return dt.isoformat()
    except Exception:
        return ""

def _iter_processed_files():
    base = _ensure_result_dir()
    try:
        for fname in os.listdir(base):
            if fname.endswith(".json") and "_processed_" in fname:
                yield os.path.join(base, fname)
    except FileNotFoundError:
        return

def _load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _collect_articles_summary():
    summaries = []
    for path in _iter_processed_files():
        try:
            data = _load_json_file(path)
            text_id = int(data.get("text_id", 0))
            title = data.get("text_title", "")
            total_sentences = int(data.get("total_sentences", len(data.get("sentences", []) or [])))
            total_tokens = int(data.get("total_tokens", 0))

            # 统计可选择 token（仅 text 类型�?            selectable = 0
            for s in data.get("sentences", []) or []:
                for t in s.get("tokens", []) or []:
                    if t.get("token_type") == "text":
                        selectable += 1

            summaries.append({
                "text_id": text_id,
                "text_title": title,
                "total_sentences": total_sentences,
                "total_tokens": total_tokens,
                "text_tokens": selectable,
                "created_at": _parse_timestamp_from_filename(os.path.basename(path)),
                "filename": os.path.basename(path),
            })
        except Exception:
            # 忽略损坏文件
            continue

    # �?text_id、created_at 排序（降序）
    summaries.sort(key=lambda x: (x.get("text_id", 0), x.get("created_at", "")), reverse=True)
    return summaries

def _find_article_file_by_id(article_id: int) -> Optional[str]:
    # 优先找匹�?text_id 的最�?processed 文件
    candidates = []
    for path in _iter_processed_files():
        try:
            data = _load_json_file(path)
            if int(data.get("text_id", -1)) == int(article_id):
                candidates.append((path, _parse_timestamp_from_filename(os.path.basename(path))))
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[0][0]

def _mark_tokens_selectable(data: dict) -> dict:
    # 深拷贝不强求，这里就地添加字段（FastAPI 会复制返回）
    total_selectable = 0
    for s in data.get("sentences", []) or []:
        selectable_count = 0
        for t in s.get("tokens", []) or []:
            is_text = (t.get("token_type") == "text")
            t["selectable"] = bool(is_text)
            t["is_selected"] = False
            if is_text:
                selectable_count += 1
        s["selectable_token_count"] = selectable_count
        total_selectable += selectable_count
    data["selectable_tokens"] = total_selectable
    return data

app = FastAPI(
    title="语言学习 API", 
    description="词汇和语法学�?API，支持统一响应格式",
    version="1.0.0"
)

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[" *\,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],  # React/Vite 开发与预览服务�?    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiResponse)
async def root():
    """根路径，返回 API 状态信�?""
    return create_success_response(
        data={
            "message": "语言学习 API 正在运行�?,
            "version": "1.0.0",
            "endpoints": {
                "health": "/api/health",
                "word": "/api/word",
                "vocab": "/api/vocab",
                "grammar": "/api/grammar",
                "docs": "/docs"
            }
        },
        message="API 服务正常"
    )


@app.get("/api/health", response_model=ApiResponse)
async def health_check():
    """健康检�?""
    return create_success_response(
        data={
            "status": "healthy",
            "timestamp": "2024-08-28T16:00:00Z"
        },
        message="服务健康"
    )


@app.get("/api/word", response_model=ApiResponse)
async def get_word_info(text: str = Query(..., description="要查询的单词")):
    """按词查询"""
    try:
        word = text.lower().strip()
        vocab_list = data_service.get_vocab_data()
        
        # 查找匹配的词�?        for vocab in vocab_list:
            if vocab.vocab_body.lower() == word:
                data = {
                    "word": vocab.vocab_body,
                    "definition": vocab.explanation,
                    "examples": vocab.examples,
                    "source": vocab.source,
                    "is_starred": vocab.is_starred
                }
                return create_success_response(
                    data=data,
                    message=f"找到词汇: {vocab.vocab_body}"
                )
        
        # 未找到单�?        return create_error_response(f"未找到单�? {word}")
        
    except Exception as e:
        return create_error_response(f"查询单词失败: {str(e)}")


@app.get("/api/grammar/{rule_id}", response_model=ApiResponse)
async def get_grammar_by_id(rule_id: int):
    """按规则ID查询"""
    try:
        grammar = data_service.get_grammar_by_id(rule_id)
        
        if grammar is None:
            return create_error_response(f"未找�?ID �?{rule_id} 的语法规�?)
        
        data = {
            "rule_id": grammar.rule_id,
            "rule_name": grammar.rule_name,
            "rule_summary": grammar.rule_summary,
            "examples": grammar.examples,
            "source": grammar.source,
            "is_starred": grammar.is_starred
        }
        
        return create_success_response(
            data=data,
            message=f"成功获取语法规则: {grammar.rule_name}"
        )
        
    except Exception as e:
        return create_error_response(f"获取语法规则失败: {str(e)}")


@app.get("/api/vocab", response_model=ApiResponse)
async def get_vocab_list():
    """获取词汇列表"""
    try:
        vocab_list = data_service.get_vocab_data()
        
        return create_success_response(
            data=[vocab.model_dump() for vocab in vocab_list],
            message=f"成功获取词汇列表，共 {len(vocab_list)} 条记�?
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇列表失败: {str(e)}")


@app.get("/api/vocab/{vocab_id}", response_model=ApiResponse)
async def get_vocab_by_id(vocab_id: int):
    """根据 ID 获取单个词汇详情"""
    try:
        vocab = data_service.get_vocab_by_id(vocab_id)
        
        if vocab is None:
            return create_error_response(f"未找�?ID �?{vocab_id} 的词�?)
        
        return create_success_response(
            data=vocab.model_dump(),
            message=f"成功获取词汇: {vocab.vocab_body}"
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇详情失败: {str(e)}")


@app.get("/api/grammar", response_model=ApiResponse)
async def get_grammar_list():
    """获取语法规则列表"""
    try:
        grammar_list = data_service.get_grammar_data()
        
        return create_success_response(
            data=[grammar.model_dump() for grammar in grammar_list],
            message=f"成功获取语法规则列表，共 {len(grammar_list)} 条记�?
        )
        
    except Exception as e:
        return create_error_response(f"获取语法规则列表失败: {str(e)}")


@app.get("/api/stats", response_model=ApiResponse)
async def get_stats():
    """获取数据统计信息"""
    try:
        vocab_list = data_service.get_vocab_data()
        grammar_list = data_service.get_grammar_data()
        
        stats = {
            "vocab": {
                "total": len(vocab_list),
                "starred": len([v for v in vocab_list if v.is_starred])
            },
            "grammar": {
                "total": len(grammar_list),
                "starred": len([g for g in grammar_list if g.is_starred])
            }
        }
        
        return create_success_response(
            data=stats,
            message="成功获取统计数据"
        )
        
    except Exception as e:
        return create_error_response(f"获取统计数据失败: {str(e)}")


@app.get("/api/articles", response_model=ApiResponse)
async def list_articles():
    """获取文章列表摘要（从 real_data_raw/result 目录扫描 processed JSON�?""
    try:
        summaries = _collect_articles_summary()
        return create_success_response(
            data=summaries,
            message=f"成功获取文章列表，共 {len(summaries)} �?
        )
    except Exception as e:
        return create_error_response(f"获取文章列表失败: {str(e)}")


@app.get("/api/articles/{article_id}", response_model=ApiResponse)
async def get_article_detail(article_id: int):
    """获取单篇文章详情，并标记 token 的可选择性（�?text 类型可选）"""
    try:
        path = _find_article_file_by_id(article_id)
        if not path:
            return create_error_response(f"文章不存�? {article_id}")

        data = _load_json_file(path)
        data = _mark_tokens_selectable(data)

        return create_success_response(
            data=data,
            message=f"成功获取文章详情: {data.get('text_title', '')}"
        )
    except Exception as e:
        return create_error_response(f"获取文章详情失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 
