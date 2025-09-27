from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

# 导入自定义模块
from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response
import os
from datetime import datetime

# 计算 backend/data/current/articles 目录（相对本文件位置）
RESULT_DIR = os.path.abspath(
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
            total_sentences = data.get("total_sentences", 0)
            total_tokens = data.get("total_tokens", 0)
            
            # 从文件名提取时间戳
            filename = os.path.basename(path)
            timestamp = _parse_timestamp_from_filename(filename)
            
            summary = {
                "text_id": text_id,
                "text_title": title,
                "total_sentences": total_sentences,
                "total_tokens": total_tokens,
                "created_at": timestamp,
                "filename": filename
            }
            summaries.append(summary)
        except Exception as e:
            print(f"Error processing {path}: {e}")
            continue
    
    return summaries

def _find_article_file_by_id(article_id: int):
    """根据文章ID查找对应的文件路径"""
    for path in _iter_processed_files():
        try:
            data = _load_json_file(path)
            if data.get("text_id") == article_id:
                return path
        except Exception:
            continue
    return None

def _mark_tokens_selectable(data):
    """标记token的可选择性（只有text类型可选）"""
    if 'sentences' in data:
        for sentence in data['sentences']:
            if 'tokens' in sentence:
                for token in sentence['tokens']:
                    if isinstance(token, dict) and token.get('token_type') == 'text':
                        token['selectable'] = True
                    else:
                        token['selectable'] = False
    return data

# 创建FastAPI应用
app = FastAPI(title="AI Language Learning API", version="1.0.0")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "AI Language Learning API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/vocab", response_model=ApiResponse)
async def get_vocab_list():
    """获取词汇列表"""
    try:
        vocab_list = data_service.get_vocab_data()
        
        return create_success_response(
            data=[vocab.model_dump() for vocab in vocab_list],
            message=f"成功获取词汇列表，共 {len(vocab_list)} 条记录"
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇列表失败: {str(e)}")

@app.get("/api/vocab/{vocab_id}", response_model=ApiResponse)
async def get_vocab_detail(vocab_id: int):
    """获取词汇详情"""
    try:
        vocab_list = data_service.get_vocab_data()
        vocab = next((v for v in vocab_list if v.vocab_id == vocab_id), None)
        
        if not vocab:
            return create_error_response(f"词汇不存在: {vocab_id}")
        
        return create_success_response(
            data=vocab.model_dump(),
            message=f"成功获取词汇详情: {vocab.vocab_body}"
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
            message=f"成功获取语法规则列表，共 {len(grammar_list)} 条记录"
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
    """获取文章列表摘要（从 backend/data/current/articles 目录扫描 processed JSON）"""
    try:
        summaries = _collect_articles_summary()
        return create_success_response(
            data=summaries,
            message=f"成功获取文章列表，共 {len(summaries)} 篇"
        )
    except Exception as e:
        return create_error_response(f"获取文章列表失败: {str(e)}")

@app.get("/api/articles/{article_id}", response_model=ApiResponse)
async def get_article_detail(article_id: int):
    """获取单篇文章详情，并标记 token 的可选择性（只有 text 类型可选）"""
    try:
        path = _find_article_file_by_id(article_id)
        if not path:
            return create_error_response(f"文章不存在: {article_id}")

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
