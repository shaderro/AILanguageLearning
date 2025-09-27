from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import requests
import uuid
from datetime import datetime

# 导入自定义模块
from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response
import os
import sys

# 添加backend路径到sys.path
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 导入预处理模块
try:
    from backend.preprocessing.article_processor import process_article, save_structured_data
    print("✅ 使用简单文章处理器 (无AI依赖)")
except ImportError as e:
    print(f"Warning: Could not import article_processor: {e}")
    process_article = None
    save_structured_data = None

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

def _iter_article_dirs():
    """扫描形如 text_<id> 的目录。"""
    base = _ensure_result_dir()
    try:
        for fname in os.listdir(base):
            full_path = os.path.join(base, fname)
            if os.path.isdir(full_path) and fname.startswith("text_"):
                yield full_path
    except FileNotFoundError:
        return

def _load_article_summary_from_dir(dir_path: str):
    """从 text_<id> 目录组装文章摘要信息。"""
    try:
        # original_text.json 提供 text_id 与 text_title
        original_path = os.path.join(dir_path, "original_text.json")
        sentences_path = os.path.join(dir_path, "sentences.json")
        tokens_path = os.path.join(dir_path, "tokens.json")

        if not os.path.exists(original_path):
            return None

        original = _load_json_file(original_path)
        text_id = int(original.get("text_id", 0))
        title = original.get("text_title", "")

        total_sentences = 0
        if os.path.exists(sentences_path):
            try:
                s = _load_json_file(sentences_path)
                total_sentences = len(s) if isinstance(s, list) else 0
            except Exception:
                total_sentences = 0

        total_tokens = 0
        if os.path.exists(tokens_path):
            try:
                t = _load_json_file(tokens_path)
                total_tokens = len(t) if isinstance(t, list) else 0
            except Exception:
                total_tokens = 0

        return {
            "text_id": text_id,
            "text_title": title,
            "total_sentences": total_sentences,
            "total_tokens": total_tokens,
            # 使用目录名作为时间信息占位；也可将创建时间作为 created_at
            "created_at": None,
            "dir": os.path.basename(dir_path),
        }
    except Exception as e:
        print(f"Error summarizing dir {dir_path}: {e}")
        return None

def _load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _collect_articles_summary():
    """同时兼容历史 *_processed_*.json 文件与新结构 text_<id>/ 目录。"""
    summaries = []

    # 1) 兼容历史单文件结构
    for path in _iter_processed_files():
        try:
            data = _load_json_file(path)
            text_id = int(data.get("text_id", 0))
            title = data.get("text_title", "")
            total_sentences = data.get("total_sentences", 0)
            total_tokens = data.get("total_tokens", 0)

            filename = os.path.basename(path)
            timestamp = _parse_timestamp_from_filename(filename)

            summaries.append({
                "text_id": text_id,
                "text_title": title,
                "total_sentences": total_sentences,
                "total_tokens": total_tokens,
                "created_at": timestamp,
                "filename": filename,
            })
        except Exception as e:
            print(f"Error processing {path}: {e}")
            continue

    # 2) 新目录结构
    for d in _iter_article_dirs():
        summary = _load_article_summary_from_dir(d)
        if summary is not None:
            summaries.append(summary)

    return summaries

def _find_article_dir_by_id(article_id: int):
    """根据文章ID查找对应的 text_<id> 目录。"""
    target_dir_name = f"text_{article_id}"
    for d in _iter_article_dirs():
        if os.path.basename(d) == target_dir_name:
            return d
        # 兜底：读取 original_text.json 校验 id
        try:
            original_path = os.path.join(d, "original_text.json")
            if os.path.exists(original_path):
                data = _load_json_file(original_path)
                if int(data.get("text_id", -1)) == article_id:
                    return d
        except Exception:
            continue
    return None

def _load_article_detail_from_dir(article_id: int):
    """从目录加载文章详情，组装成统一的数据结构。"""
    d = _find_article_dir_by_id(article_id)
    if not d:
        return None

    original_path = os.path.join(d, "original_text.json")
    sentences_path = os.path.join(d, "sentences.json")
    tokens_path = os.path.join(d, "tokens.json")

    try:
        original = _load_json_file(original_path) if os.path.exists(original_path) else {}
        sentences = _load_json_file(sentences_path) if os.path.exists(sentences_path) else []
        tokens = _load_json_file(tokens_path) if os.path.exists(tokens_path) else []

        detail = {
            "text_id": int(original.get("text_id", article_id)),
            "text_title": original.get("text_title", "Article"),
            "sentences": sentences if isinstance(sentences, list) else [],
            "total_sentences": len(sentences) if isinstance(sentences, list) else 0,
            "total_tokens": len(tokens) if isinstance(tokens, list) else 0,
        }
        return detail
    except Exception as e:
        print(f"Error loading detail from dir {d}: {e}")
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
    """获取文章列表摘要（兼容 *_processed_*.json 与 text_<id>/ 结构）"""
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
        # 先尝试目录结构
        data = _load_article_detail_from_dir(article_id)
        if data is None:
            # 兼容历史单文件
            for path in _iter_processed_files():
                try:
                    fdata = _load_json_file(path)
                    if int(fdata.get("text_id", -1)) == article_id:
                        data = fdata
                        break
                except Exception:
                    continue

        if data is None:
            return create_error_response(f"文章不存在: {article_id}")

        data = _mark_tokens_selectable(data)

        return create_success_response(
            data=data,
            message=f"成功获取文章详情: {data.get('text_title', '')}"
        )
    except Exception as e:
        return create_error_response(f"获取文章详情失败: {str(e)}")

# 新增：文件上传处理API
@app.post("/api/upload/file", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form("Untitled Article")
):
    """上传文件并进行预处理"""
    try:
        # 读取文件内容
        content = await file.read()
        
        # 根据文件类型处理内容
        if file.filename.endswith('.txt') or file.filename.endswith('.md'):
            text_content = content.decode('utf-8')
        elif file.filename.endswith('.pdf'):
            # TODO: 添加PDF处理
            return create_error_response("PDF处理功能暂未实现")
        else:
            return create_error_response(f"不支持的文件格式: {file.filename}")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理文章: {title}")
            result = process_article(text_content, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"文件上传并处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"文件上传处理失败: {str(e)}")

# 新增：URL内容抓取API
@app.post("/api/upload/url", response_model=ApiResponse)
async def upload_url(
    url: str = Form(...),
    title: str = Form("URL Article")
):
    """从URL抓取内容并进行预处理"""
    try:
        # 抓取URL内容
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 简单提取文本内容（这里可以集成更复杂的HTML解析）
        text_content = response.text
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理URL文章: {title}")
            result = process_article(text_content, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "url": url,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"URL内容抓取并处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"URL内容抓取失败: {str(e)}")

# 新增：文字输入处理API
@app.post("/api/upload/text", response_model=ApiResponse)
async def upload_text(
    text: str = Form(...),
    title: str = Form("Text Article")
):
    """直接处理文字内容"""
    try:
        if not text.strip():
            return create_error_response("文字内容不能为空")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 开始处理文字内容: {title}")
            result = process_article(text, article_id, title)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens']
                },
                message=f"文字内容处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        return create_error_response(f"文字内容处理失败: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
