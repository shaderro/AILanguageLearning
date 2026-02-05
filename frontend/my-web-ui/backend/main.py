from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends, Header
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import json
import requests
import uuid
from datetime import datetime, timedelta

# 首先设置路径
import os
import sys

# Windows 控制台默认可能是 GBK，遇到 emoji 等字符会触发 UnicodeEncodeError。
# 这里尽量把 stdout/stderr 统一为 UTF-8，避免服务启动/运行时崩溃。
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')

# 添加路径到 sys.path
for p in [REPO_ROOT, BACKEND_DIR, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# 切换工作目录到项目根目录，确保数据库路径正确
original_cwd = os.getcwd()
os.chdir(REPO_ROOT)
print(f"[OK] 工作目录已切换: {original_cwd} -> {REPO_ROOT}")

# 导入自定义模块（现在使用绝对路径导入）
sys.path.insert(0, CURRENT_DIR)
from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response

# 导入预处理模块
try:
    from backend.preprocessing.article_processor import process_article, save_structured_data
    from backend.preprocessing.html_extractor import extract_main_text_from_url
    from backend.preprocessing.pdf_extractor import extract_text_from_pdf_bytes
    print("[OK] 使用简单文章处理器 (无AI依赖)")
except ImportError as e:
    print(f"Warning: Could not import article_processor: {e}")
    process_article = None
    save_structured_data = None
    extract_main_text_from_url = None
    extract_text_from_pdf_bytes = None

# 导入 asked tokens manager
from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager

# 导入环境配置
try:
    from backend.config import ENV
except ImportError:
    import os
    ENV = os.getenv("ENV", "development")

# 文章长度限制（字符数）
MAX_ARTICLE_LENGTH = 5000

# 导入新的标注API路由
try:
    from backend.api.notation_routes import router as notation_router
    print("[OK] 加载新的标注API路由模块成功")
except ImportError as e:
    import traceback
    print(f"❌ [ERROR] 无法导入 notation_routes: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    notation_router = None
except Exception as e:
    import traceback
    print(f"❌ [ERROR] 导入 notation_routes 时发生其他错误: {e}")
    print("详细错误信息:")
    traceback.print_exc()
    notation_router = None

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

def _convert_tokens_from_payload(tokens_payload):
    """将前端传入的 token 列表转换为 Token 数据类"""
    if not tokens_payload:
        return tuple()
    converted = []
    for token in tokens_payload:
        if isinstance(token, NewToken):
            converted.append(token)
        elif isinstance(token, dict):
            token_data = {field: token.get(field) for field in NewToken.__dataclass_fields__.keys()}
            token_data['token_body'] = token.get('token_body', '')
            token_data['token_type'] = token.get('token_type', 'text')
            converted.append(NewToken(**token_data))
        else:
            converted.append(token)
    return tuple(converted)

def _convert_word_tokens_from_payload(word_tokens_payload):
    """将前端传入的 word token 列表转换为 WordToken 数据类"""
    if not word_tokens_payload:
        return None
    converted = []
    for word_token in word_tokens_payload:
        if isinstance(word_token, WordToken):
            converted.append(word_token)
        elif isinstance(word_token, dict):
            converted.append(
                WordToken(
                    word_token_id=word_token.get('word_token_id'),
                    token_ids=tuple(word_token.get('token_ids', [])),
                    word_body=word_token.get('word_body', ''),
                    pos_tag=word_token.get('pos_tag'),
                    lemma=word_token.get('lemma'),
                    linked_vocab_id=word_token.get('linked_vocab_id'),
                )
            )
    return tuple(converted) if converted else None

def _derive_language_context(sentence_data: dict):
    language = sentence_data.get('language')
    language_code = sentence_data.get('language_code')
    is_non_whitespace = sentence_data.get('is_non_whitespace')
    if not language_code and language:
        try:
            language_code = lc_get_language_code(language)
        except Exception:
            language_code = None
    if is_non_whitespace is None and language_code:
        try:
            is_non_whitespace = lc_is_non_whitespace_language(language_code)
        except Exception:
            is_non_whitespace = None
    return language, language_code, is_non_whitespace

# 创建FastAPI应用
app = FastAPI(title="AI Language Learning API", version="1.0.0")

# ==================== 全局校验错误处理（422） =====================
# 生产环境登录 / 其他接口出现 422 时，记录更详细的日志，并返回可读字符串，避免前端直接渲染复杂对象崩溃
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    try:
        body = await request.body()
    except Exception:
        body = b""
    
    print("❌ [ValidationError] 请求路径:", request.url.path)
    print("❌ [ValidationError] 原始请求体:", body.decode("utf-8", errors="ignore"))
    print("❌ [ValidationError] 详细错误:", exc.errors())

    # 将 pydantic 错误数组压缩成一行字符串，方便前端展示
    messages = []
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []))
        msg = err.get("msg", "")
        if loc or msg:
            messages.append(f"{loc}: {msg}" if loc else msg)
    message = " | ".join(messages) if messages else "请求参数校验失败"

    return JSONResponse(
        status_code=422,
        content={"detail": message},
    )

# ==================== CORS 配置 =====================
# MVP 阶段：允许所有来源（方便开发和测试）
# 后续生产环境：应收紧为指定域名列表，提高安全性
#
# 推荐的生产环境配置（取消注释并修改）：
# ALLOWED_ORIGINS = [
#     "https://your-frontend-domain.vercel.app",  # Vercel 生产环境
#     "https://your-frontend-domain.com",            # 自定义域名（如果有）
#     "http://localhost:5173",                       # 本地开发（可选）
#     "http://127.0.0.1:5173",                      # 本地开发（可选）
# ]
# 
# 然后修改下面的 allow_origins=ALLOWED_ORIGINS

# MVP 阶段：允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP 阶段：允许所有来源（Vercel 前端可正常访问）
    allow_credentials=True,  # 允许携带认证信息（Cookie、Authorization header）
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # 允许的 HTTP 方法
    allow_headers=["*"],  # 允许所有请求头（包括 Authorization、Content-Type 等）
)

# ==================== Rate Limit 中间件 ====================
# ⚠️ 安全：限制 API 调用频率，防止滥用（特别是 AI 接口）
try:
    from backend.middleware.rate_limit import rate_limit_middleware
    app.middleware("http")(rate_limit_middleware)
    print("[OK] Rate limit 中间件已启用")
    print("   - /api/chat: 每个用户每分钟最多 20 次请求")
    print("   - 其他接口: 每个用户每分钟最多 100 次请求")
except ImportError as e:
    print(f"[WARN] Rate limit 中间件加载失败: {e}")

# ==================== 数据库初始化（应用启动时）====================
@app.on_event("startup")
async def startup_event():
    """应用启动时自动初始化数据库表结构"""
    try:
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import Base
        from backend.config import ENV
        
        print("\n" + "="*60)
        print("🔧 初始化数据库表结构...")
        print("="*60)
        
        # 获取数据库管理器
        db_manager = DatabaseManager(ENV)
        engine = db_manager.get_engine()
        
        # 检查是否是 PostgreSQL
        database_url = db_manager.database_url
        is_postgres = (database_url.startswith('postgresql://') or 
                      database_url.startswith('postgresql+psycopg2://') or
                      database_url.startswith('postgres://'))
        
        if is_postgres:
            print("📊 检测到 PostgreSQL 数据库")
            # 检查表是否已存在
            from sqlalchemy import inspect
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()
            
            if existing_tables:
                print(f"✅ 数据库表已存在 ({len(existing_tables)} 个表)")
                for table in sorted(existing_tables):
                    print(f"   - {table}")
            else:
                print("📋 创建数据库表结构...")
                Base.metadata.create_all(engine)
                print("✅ 数据库表创建完成")
                
                # 显示创建的表
                inspector = inspect(engine)
                new_tables = inspector.get_table_names()
                print(f"✅ 共创建 {len(new_tables)} 个表:")
                for table in sorted(new_tables):
                    columns = inspector.get_columns(table)
                    print(f"   - {table} ({len(columns)} 列)")
        else:
            print("📊 检测到 SQLite 数据库")
            # SQLite: 确保表结构存在
            Base.metadata.create_all(engine)
            print("✅ SQLite 数据库表已初始化")
        
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"⚠️ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        print("⚠️ 应用将继续启动，但数据库功能可能不可用")

# 添加请求日志中间件（用于调试）
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"📥 [Request] {request.method} {request.url.path}")
    # 🔧 修复：只在需要时读取请求体，并且正确处理异常
    try:
        # 如果是 POST 请求，尝试记录请求体大小（但不影响后续处理）
        if request.method == "POST":
            # 使用 stream 方式读取，避免消耗请求体
            body_bytes = b""
            async for chunk in request.stream():
                body_bytes += chunk
            if body_bytes:
                print(f"📦 [Request] Body size: {len(body_bytes)} bytes")
                # 🔧 修复：将 body 放回，使用正确的 ASGI receive 格式
                async def receive():
                    return {"type": "http.request", "body": body_bytes, "more_body": False}
                request._receive = receive
    except Exception as e:
        # 🔧 如果读取请求体失败，记录但不影响后续处理
        print(f"⚠️ [Request] 读取请求体失败: {e}")
    
    try:
        response = await call_next(request)
        print(f"📤 [Response] {request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as e:
        # 🔧 捕获并记录异常，然后重新抛出
        print(f"❌ [Request] 处理请求时发生异常: {e}")
        raise

# 注册新的标注API路由
if notation_router:
    try:
        app.include_router(notation_router)
        print("[OK] 注册新的标注API路由: /api/v2/notations")
    except Exception as e:
        import traceback
        print(f"❌ [ERROR] 注册 notation_router 时发生错误: {e}")
        print("详细错误信息:")
        traceback.print_exc()
else:
    print("⚠️ [WARNING] notation_router 为 None，未注册标注API路由")

# 注册认证API路由
try:
    from backend.api.auth_routes import router as auth_router, get_current_user
    from database_system.business_logic.models import User
    app.include_router(auth_router)
    print("[OK] 注册认证API路由: /api/auth")
except ImportError as e:
    print(f"Warning: Could not import auth_routes: {e}")
    # 如果导入失败，提供一个占位函数
    def get_current_user():
        raise HTTPException(status_code=500, detail="认证系统未加载")
    User = None

# 注册邀请码 / Token API 路由
try:
    from backend.api.invite_routes import router as invite_router
    app.include_router(invite_router)
    print("[OK] 注册邀请码API路由: /api/invite")
except ImportError as e:
    print(f"Warning: Could not import invite_routes: {e}")

# 注册文章API路由
try:
    from backend.api.text_routes import router as text_router
    app.include_router(text_router)
    print("[OK] 注册文章API路由: /api/v2/texts")
except ImportError as e:
    print(f"Warning: Could not import text_routes: {e}")

# 注册词汇API路由
try:
    from backend.api.vocab_routes import router as vocab_router
    app.include_router(vocab_router)
    print("[OK] 注册词汇API路由: /api/v2/vocab")
except ImportError as e:
    print(f"Warning: Could not import vocab_routes: {e}")

# 注册语法API路由
try:
    from backend.api.grammar_routes import router as grammar_router
    app.include_router(grammar_router)
    print("[OK] 注册语法API路由: /api/v2/grammar")
except ImportError as e:
    print(f"Warning: Could not import grammar_routes: {e}")

# 注册聊天历史API路由
try:
    from backend.api.chat_history_routes import router as chat_history_router
    app.include_router(chat_history_router)
    print("[OK] 注册聊天历史API路由: /api/chat/history")
except ImportError as e:
    print(f"Warning: Could not import chat_history_routes: {e}")

@app.get("/")
async def root():
    return {"message": "AI Language Learning API"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/debug/db-info")
async def debug_db_info():
    """调试端点：显示数据库连接信息"""
    from database_system.database_manager import DatabaseManager
    import sqlite3
    import os
    
    db_manager = DatabaseManager(ENV)
    engine = db_manager.get_engine()
    db_url = str(engine.url)
    
    # 提取文件路径
    db_path = db_url.replace('sqlite:///', '')
    if db_path.startswith('/') and ':' in db_path:
        db_path = db_path[1:]
    
    # 获取绝对路径
    abs_path = os.path.abspath(db_path)
    
    info = {
        "db_url": db_url,
        "db_path": db_path,
        "abs_path": abs_path,
        "cwd": os.getcwd(),
        "exists": os.path.exists(db_path),
        "tables": []
    }
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        info["tables"] = tables
        info["file_size"] = os.path.getsize(db_path)
        conn.close()
    
    return info

@app.get("/api/db-test")
async def db_test():
    """数据库连接测试接口"""
    from database_system.database_manager import DatabaseManager
    from sqlalchemy import text
    
    db_manager = DatabaseManager(ENV)
    session = db_manager.get_session()
    try:
        result = session.execute(text("SELECT 1")).fetchone()
        return {"db_ok": True, "result": result[0]}
    finally:
        session.close()

# ==================== Session Management API ====================
# 这些API原本在server_frontend_mock.py中，现在添加到主服务器以支持前端功能

# 初始化全局 SessionState（使用完整的 SessionState 类）
from backend.assistants.chat_info.session_state import SessionState
from backend.assistants.chat_info.selected_token import SelectedToken
from backend.data_managers.data_classes_new import (
    Sentence as NewSentence,
    Token as NewToken,
    WordToken,
)
from backend.preprocessing.language_classification import (
    get_language_code as lc_get_language_code,
    is_non_whitespace_language as lc_is_non_whitespace_language,
)

session_state = SessionState()
print("[OK] SessionState singleton initialized")

# 初始化全局 DataController
from backend.data_managers import data_controller

# 数据文件路径
DATA_DIR = os.path.join(BACKEND_DIR, "data", "current")
GRAMMAR_PATH = os.path.join(DATA_DIR, "grammar.json")
VOCAB_PATH = os.path.join(DATA_DIR, "vocab.json")
TEXT_PATH = os.path.join(DATA_DIR, "original_texts.json")
DIALOGUE_RECORD_PATH = os.path.join(DATA_DIR, "dialogue_record.json")
DIALOGUE_HISTORY_PATH = os.path.join(DATA_DIR, "dialogue_history.json")

global_dc = data_controller.DataController(max_turns=100)
print("✅ Global DataController created")

# 🔧 临时存储：用于存储后台任务创建的新知识点，供前端轮询获取
# 格式: {(user_id, text_id): {'vocab_to_add': [...], 'grammar_to_add': [...], 'timestamp': ...}}
pending_knowledge_points = {}

# 加载数据
try:
    global_dc.load_data(
        grammar_path=GRAMMAR_PATH,
        vocab_path=VOCAB_PATH,
        text_path=TEXT_PATH,
        dialogue_record_path=DIALOGUE_RECORD_PATH,
        dialogue_history_path=DIALOGUE_HISTORY_PATH
    )
    print("✅ Global data loaded successfully")
    print(f"  - Grammar rules: {len(global_dc.grammar_manager.grammar_bundles)}")
    print(f"  - Vocab items: {len(global_dc.vocab_manager.vocab_bundles)}")
    print(f"  - Texts: {len(global_dc.text_manager.original_texts)}")
except Exception as e:
    print(f"⚠️ Global data loading failed: {e}")
    print("⚠️ Continuing with empty data")

# 将处理后的文章数据导入到数据库
def import_article_to_database(result: dict, article_id: int, user_id, language: str = None, title: str = None):
    """
    将处理后的文章数据导入到数据库或返回游客数据
    
    参数:
        result: process_article返回的结果字典，包含sentences和tokens
        article_id: 文章ID
        user_id: 用户ID（整数表示正式用户，字符串表示游客）
        language: 语言（中文、英文、德文），可选
    
    返回:
        如果是正式用户: True/False（成功/失败）
        如果是游客: 字典，包含文章数据，格式: {"is_guest": True, "article_data": {...}}
    """
    # 判断是游客还是正式用户
    is_guest = isinstance(user_id, str) and user_id.startswith('guest_')
    
    if is_guest:
        # 游客模式：返回文章数据，由前端保存到 localStorage
        print(f"👤 [Import] 游客模式，返回文章数据供前端保存 (guest_id: {user_id}, language: {language})")
        
        # 优先使用传入的title，如果没有则使用result中的
        final_title = title or result.get('text_title', 'Untitled Article')
        article_data = {
            "article_id": article_id,
            "title": final_title,
            "language": language,
            "total_sentences": result.get('total_sentences', 0),
            "total_tokens": result.get('total_tokens', 0),
            "sentences": result.get('sentences', []),
            "tokens": []  # tokens 包含在 sentences 中，不需要单独存储
        }
        
        return {"is_guest": True, "article_data": article_data}
    
    # 正式用户模式：保存到数据库
    try:
        # 验证用户是否存在
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import User
        
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        
        try:
            # 验证用户是否存在
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                print(f"❌ [Import] 用户 {user_id} 不存在")
                return False
            
            from backend.data_managers import OriginalTextManagerDB
            from database_system.business_logic.crud import TokenCRUD
            from database_system.business_logic.models import TokenType, WordToken
            from sqlalchemy import func
            
            text_manager = OriginalTextManagerDB(session)
            token_crud = TokenCRUD(session)
            
            # 1. 创建或更新文章（使用指定的article_id）
            # 文章记录应该已经在上传时创建（状态为"processing"），这里需要更新状态为"completed"
            from database_system.business_logic.models import OriginalText
            text_model = session.query(OriginalText).filter(
                OriginalText.text_id == article_id,
                OriginalText.user_id == user_id
            ).first()
            
            if text_model:
                # 更新文章信息（优先使用传入的title，如果没有则使用result中的，最后才使用现有的）
                # 这样可以确保用户输入的标题不会被覆盖
                if title:
                    text_model.text_title = title
                elif result.get('text_title'):
                    text_model.text_title = result.get('text_title')
                # 如果都没有，保持现有的标题
                text_model.language = language or text_model.language
                text_model.processing_status = 'completed'  # 更新状态为"已完成"
                session.commit()  # 确保状态更新被提交
                print(f"✅ [Import] 更新文章状态为已完成: {text_model.text_title} (ID: {article_id}, User: {user_id}, Language: {language})")
            else:
                # 如果文章记录不存在（可能是旧数据），创建新记录
                # 优先使用传入的title
                final_title = title or result.get('text_title', 'Untitled Article')
                text_model = OriginalText(
                    text_id=article_id,
                    text_title=final_title,
                    user_id=user_id,
                    language=language,
                    processing_status='completed'
                )
                session.add(text_model)
                session.flush()  # 刷新以获取ID
                print(f"✅ [Import] 创建文章: {text_model.text_title} (ID: {article_id}, User: {user_id}, Language: {language})")
            
            # 2. 导入句子和tokens
            sentences = result.get('sentences', [])
            print(f"🔍 [Import] 预处理结果检查: sentences数量={len(sentences)}")
            if sentences:
                first_sentence = sentences[0]
                print(f"🔍 [Import] 第一个句子检查: sentence_id={first_sentence.get('sentence_id')}, 有tokens={bool(first_sentence.get('tokens'))}, 有word_tokens={bool(first_sentence.get('word_tokens'))}")
                if first_sentence.get('word_tokens'):
                    print(f"🔍 [Import] 第一个句子的word_tokens数量: {len(first_sentence.get('word_tokens', []))}")
                    if len(first_sentence.get('word_tokens', [])) > 0:
                        print(f"🔍 [Import] 第一个word_token示例: {first_sentence.get('word_tokens')[0]}")
            
            # 🔧 修复：查询数据库中当前最大的 word_token_id，确保新分配的 ID 全局唯一
            from database_system.business_logic.models import WordToken
            max_word_token_id = session.query(func.max(WordToken.word_token_id)).scalar() or 0
            print(f"🔍 [Import] 数据库中当前最大 word_token_id: {max_word_token_id}")
            next_word_token_id = max_word_token_id + 1
            
            # 创建 word_token_id 映射表：预处理生成的 ID -> 新的全局唯一 ID
            word_token_id_mapping = {}
            
            total_sentences = 0
            total_tokens = 0
            total_word_tokens = 0
            
            for sentence_data in sentences:
                sentence_id = sentence_data.get('sentence_id', total_sentences + 1)
                sentence_body = sentence_data.get('sentence_body', '')
                
                # 检查句子是否已存在
                existing_sentence = text_manager.get_sentence(article_id, sentence_id)
                if existing_sentence:
                    print(f"⚠️ [Import] 句子 {article_id}:{sentence_id} 已存在，跳过")
                    continue
                
                # 获取段落信息
                paragraph_id = sentence_data.get('paragraph_id')
                is_new_paragraph = sentence_data.get('is_new_paragraph', False)
                
                # 创建句子
                sentence = text_manager.add_sentence_to_text(
                    text_id=article_id,
                    sentence_text=sentence_body,
                    difficulty_level=None,
                    paragraph_id=paragraph_id,
                    is_new_paragraph=is_new_paragraph
                )
                total_sentences += 1
                
                # 3. 先导入 word_tokens（仅用于非空格语言），确保在创建 tokens 时可以引用
                word_tokens = sentence_data.get('word_tokens', [])
                print(f"🔍 [Import] 句子 {sentence_id} 的 word_tokens: {len(word_tokens) if word_tokens else 0} 个")
                for word_token_data in word_tokens:
                    old_word_token_id = word_token_data.get('word_token_id')  # 预处理生成的 ID（可能从 1 开始）
                    word_body = word_token_data.get('word_body', '')
                    token_ids = word_token_data.get('token_ids', [])
                    
                    if not old_word_token_id or not word_body or not token_ids:
                        print(f"⚠️ [Import] 跳过无效的 word_token: word_token_id={old_word_token_id}, word_body={word_body}, token_ids={token_ids}")
                        continue
                    
                    # 🔧 修复：分配新的全局唯一 word_token_id
                    if old_word_token_id not in word_token_id_mapping:
                        new_word_token_id = next_word_token_id
                        word_token_id_mapping[old_word_token_id] = new_word_token_id
                        next_word_token_id += 1
                    else:
                        new_word_token_id = word_token_id_mapping[old_word_token_id]
                    
                    # 创建 word_token（使用新的全局唯一 ID）
                    try:
                        word_token = WordToken(
                            word_token_id=new_word_token_id,
                            text_id=article_id,
                            sentence_id=sentence_id,
                            word_body=word_body,
                            token_ids=token_ids,  # JSON 类型，直接传递列表
                            pos_tag=word_token_data.get('pos_tag'),
                            lemma=word_token_data.get('lemma'),
                            linked_vocab_id=word_token_data.get('linked_vocab_id')
                        )
                        session.add(word_token)
                        total_word_tokens += 1
                        print(f"✅ [Import] 创建 word_token: old_id={old_word_token_id} -> new_id={new_word_token_id}, word_body={word_body}, token_ids={token_ids}")
                    except Exception as wt_e:
                        print(f"❌ [Import] 创建 word_token 失败: {wt_e}")
                        import traceback
                        traceback.print_exc()
                
                # 4. 导入tokens（在 word_tokens 之后，以便可以引用 word_token_id）
                tokens = sentence_data.get('tokens', [])
                tokens_count = len(tokens)
                if tokens_count > 0:
                    print(f"📝 [Import] 开始导入句子 {sentence_id} 的 {tokens_count} 个tokens...")
                
                for idx, token_data in enumerate(tokens):
                    token_body = token_data.get('token_body', token_data.get('text', ''))
                    token_type_str = token_data.get('token_type', 'TEXT')
                    
                    # 转换为TokenType枚举名称（数据库期望枚举名称，如 'TEXT', 'PUNCTUATION', 'SPACE'）
                    try:
                        token_type_str_upper = token_type_str.upper()
                        if token_type_str_upper == 'TEXT':
                            token_type_name = 'TEXT'
                        elif token_type_str_upper == 'PUNCTUATION':
                            token_type_name = 'PUNCTUATION'
                        elif token_type_str_upper == 'SPACE':
                            token_type_name = 'SPACE'
                        else:
                            token_type_name = 'TEXT'  # 默认
                    except:
                        token_type_name = 'TEXT'
                    
                    sentence_token_id = token_data.get('sentence_token_id', token_data.get('token_id'))
                    old_word_token_id = token_data.get('word_token_id')  # 🔧 获取预处理生成的 word_token_id
                    
                    # 🔧 修复：将预处理生成的 word_token_id 映射到新的全局唯一 ID
                    new_word_token_id = None
                    if old_word_token_id is not None:
                        new_word_token_id = word_token_id_mapping.get(old_word_token_id)
                        if new_word_token_id is None:
                            print(f"⚠️ [Import] token 引用的 word_token_id={old_word_token_id} 未找到映射，跳过 word_token_id 引用")
                    
                    # 创建token（传递枚举名称字符串，数据库期望枚举名称）
                    token_crud.create(
                        text_id=article_id,
                        sentence_id=sentence_id,
                        token_body=token_body,
                        token_type=token_type_name,  # 传递枚举名称字符串（'TEXT', 'PUNCTUATION', 'SPACE'）
                        sentence_token_id=sentence_token_id,
                        pos_tag=token_data.get('pos_tag'),
                        lemma=token_data.get('lemma'),
                        word_token_id=new_word_token_id  # 🔧 使用映射后的全局唯一 word_token_id
                    )
                    total_tokens += 1
                    
                    # 🔧 添加更频繁的进度日志（每 1000 个 tokens 或每 10 个句子打印一次）
                    if total_tokens % 1000 == 0:
                        print(f"📊 [Import] 进度: {total_sentences} 个句子，{total_tokens} 个tokens，{total_word_tokens} 个word_tokens...")
                        # 🔧 每 1000 个 tokens 执行一次 flush，减少内存使用并提高性能
                        session.flush()
                    elif total_sentences % 10 == 0 and idx == 0:  # 每 10 个句子的第一个 token 时打印
                        print(f"📊 [Import] 进度: {total_sentences} 个句子，{total_tokens} 个tokens，{total_word_tokens} 个word_tokens...")
                        session.flush()  # 每 10 个句子也 flush 一次
                
                # 每完成一个句子，如果句子有很多 tokens，打印完成信息
                if tokens_count > 100:
                    print(f"✅ [Import] 句子 {sentence_id} 完成: {tokens_count} 个tokens")
            
            # 🔧 在提交前打印最终统计
            print(f"💾 [Import] 准备提交到数据库: {total_sentences} 个句子，{total_tokens} 个tokens，{total_word_tokens} 个word_tokens...")
            import time
            commit_start = time.time()
            session.commit()
            commit_elapsed = (time.time() - commit_start) * 1000
            print(f"✅ [Import] 数据库提交完成，耗时: {commit_elapsed:.2f}ms")
            print(f"✅ [Import] 导入完成: {total_sentences} 个句子，{total_tokens} 个tokens，{total_word_tokens} 个word_tokens (User: {user_id}, Language: {language})")
            return True
            
        except Exception as e:
            session.rollback()
            # 导入失败时，更新状态为"failed"
            try:
                from database_system.business_logic.models import OriginalText
                text_model = session.query(OriginalText).filter(
                    OriginalText.text_id == article_id,
                    OriginalText.user_id == user_id
                ).first()
                if text_model:
                    text_model.processing_status = 'failed'
                    session.commit()
                    print(f"⚠️ [Import] 导入失败，已更新文章状态为失败: {article_id}")
            except Exception as update_error:
                session.rollback()
                print(f"⚠️ [Import] 更新文章状态失败: {update_error}")
            raise e
        finally:
            session.close()
        
    except Exception as e:
        print(f"❌ [Import] 导入文章到数据库失败: {e}")
        import traceback
        traceback.print_exc()
        # 如果是在外层异常，尝试更新状态
        try:
            from database_system.database_manager import DatabaseManager
            from database_system.business_logic.models import OriginalText
            db_manager = DatabaseManager(ENV)
            session = db_manager.get_session()
            try:
                text_model = session.query(OriginalText).filter(
                    OriginalText.text_id == article_id,
                    OriginalText.user_id == user_id
                ).first()
                if text_model:
                    text_model.processing_status = 'failed'
                    session.commit()
                    print(f"⚠️ [Import] 导入失败，已更新文章状态为失败: {article_id}")
            except Exception as update_error:
                session.rollback()
                print(f"⚠️ [Import] 更新文章状态失败: {update_error}")
            finally:
                session.close()
        except Exception as session_error:
            print(f"⚠️ [Import] 无法获取数据库会话: {session_error}")
        return False

# 异步保存数据的辅助函数
def save_data_async(dc, grammar_path, vocab_path, text_path, dialogue_record_path, dialogue_history_path):
    """后台异步保存数据"""
    try:
        print("\n💾 [Background] ========== 开始异步保存数据 ==========")
        dc.save_data(
            grammar_path=grammar_path,
            vocab_path=vocab_path,
            text_path=text_path,
            dialogue_record_path=dialogue_record_path,
            dialogue_history_path=dialogue_history_path
        )
        print("✅ [Background] 数据保存成功")
    except Exception as e:
        print(f"❌ [Background] 数据保存失败: {e}")
        import traceback
        print(traceback.format_exc())

@app.post("/api/session/set_sentence")
async def set_session_sentence(payload: dict):
    """设置当前句子上下文"""
    try:
        print(f"[Session] Setting session sentence")
        sentence_data = payload.get('sentence', payload)
        tokens_payload = sentence_data.get('tokens', [])
        word_tokens_payload = sentence_data.get('word_tokens')
        sentence = NewSentence(
            text_id=sentence_data['text_id'],
            sentence_id=sentence_data['sentence_id'],
            sentence_body=sentence_data['sentence_body'],
            sentence_difficulty_level=sentence_data.get('sentence_difficulty_level'),
            tokens=_convert_tokens_from_payload(tokens_payload),
            word_tokens=_convert_word_tokens_from_payload(word_tokens_payload)
        )
        session_state.set_current_sentence(sentence)
        language, language_code, is_non_whitespace = _derive_language_context(sentence_data)
        session_state.set_language_context(language, language_code, is_non_whitespace)
        return {"success": True, "message": "Sentence context set"}
    except Exception as e:
        print(f"[Session] Error setting sentence: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/session/select_token")
async def set_session_selected_token(payload: dict):
    """设置选中的token"""
    try:
        print(f"[Session] Setting selected token")
        token_data = payload.get('token', {})
        selected_token = SelectedToken(
            token_indices=token_data.get('token_indices', [-1]),
            token_text=token_data.get('token_text', ''),
            sentence_body=session_state.current_sentence.sentence_body if session_state.current_sentence else '',
            sentence_id=session_state.current_sentence.sentence_id if session_state.current_sentence else 0,
            text_id=session_state.current_sentence.text_id if session_state.current_sentence else 0
        )
        session_state.set_current_selected_token(selected_token)
        return {"success": True, "message": "Token context set"}
    except Exception as e:
        print(f"[Session] Error setting token: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/session/update_context")
async def update_session_context(payload: dict):
    """一次性更新会话上下文（批量更新）"""
    try:
        print(f"[SessionState] 批量更新上下文...")
        updated_fields = []
        
        # 更新 current_input
        if 'current_input' in payload:
            session_state.set_current_input(payload['current_input'])
            updated_fields.append('current_input')
        
        # 更新句子
        if 'sentence' in payload:
            sentence_data = payload['sentence']
            print(f"🔍 [SessionState] 设置句子上下文:")
            print(f"  - text_id: {sentence_data.get('text_id')} (type: {type(sentence_data.get('text_id'))})")
            print(f"  - sentence_id: {sentence_data.get('sentence_id')}")
            print(f"  - sentence_body: {sentence_data.get('sentence_body', '')[:50]}...")
            
            tokens_payload = sentence_data.get('tokens', [])
            word_tokens_payload = sentence_data.get('word_tokens')
            current_sentence = NewSentence(
                text_id=sentence_data['text_id'],
                sentence_id=sentence_data['sentence_id'],
                sentence_body=sentence_data['sentence_body'],
                sentence_difficulty_level=sentence_data.get('sentence_difficulty_level'),
                tokens=_convert_tokens_from_payload(tokens_payload),
                word_tokens=_convert_word_tokens_from_payload(word_tokens_payload)
            )
            session_state.set_current_sentence(current_sentence)
            language, language_code, is_non_whitespace = _derive_language_context(sentence_data)
            session_state.set_language_context(language, language_code, is_non_whitespace)
            updated_fields.append('sentence')
        
        # 更新 token
        if 'token' in payload:
            token_data = payload['token']
            
            # 🔧 如果 token_data 为 None，明确清除 token 选择
            if token_data is None:
                print("[SessionState] 清除 token 选择（token = null）")
                session_state.set_current_selected_token(None)
                updated_fields.append('token (cleared)')
            elif session_state.current_sentence:
                # token_data 不为 None，设置新的 token
                current_sentence = session_state.current_sentence
                if 'multiple_tokens' in token_data:
                    # 多个token
                    token_indices = token_data.get('token_indices', [])
                    token_text = token_data.get('token_text', '')
                    selected_token = SelectedToken(
                        token_indices=token_indices,
                        token_text=token_text,
                        sentence_body=current_sentence.sentence_body,
                        sentence_id=current_sentence.sentence_id,
                        text_id=current_sentence.text_id
                    )
                else:
                    # 单个token
                    sentence_token_id = token_data.get('sentence_token_id')
                    token_indices = [sentence_token_id] if sentence_token_id is not None else [-1]
                    selected_token = SelectedToken(
                        token_indices=token_indices,
                        token_text=token_data.get('token_body', current_sentence.sentence_body),
                        sentence_body=current_sentence.sentence_body,
                        sentence_id=current_sentence.sentence_id,
                        text_id=current_sentence.text_id
                    )
                session_state.set_current_selected_token(selected_token)
                updated_fields.append('token')
        
        return {
            'success': True,
            'message': 'Session context updated',
            'updated_fields': updated_fields
        }
    except Exception as e:
        import traceback
        print(f"[SessionState] Error updating context: {e}")
        print(f"[SessionState] Traceback:\n{traceback.format_exc()}")
        return {'success': False, 'error': str(e)}

@app.post("/api/session/reset")
async def reset_session_state(payload: dict):
    """重置会话状态"""
    try:
        print(f"[Session] Resetting session state")
        session_state.reset()
        return {"success": True, "message": "Session state reset"}
    except Exception as e:
        print(f"[Session] Error resetting session: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/admin/sync-to-db")
async def trigger_sync_to_db():
    """手动触发 JSON 数据同步到数据库"""
    try:
        print("🔄 [Admin] Manual sync triggered")
        _sync_to_database()
        return {"success": True, "message": "Data synced to database"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _sync_to_database(user_id: int = None):
    """同步 JSON 数据到数据库
    
    参数:
        user_id: 当前用户ID，用于关联新创建的数据
    """
    try:
        from database_system.database_manager import DatabaseManager
        from backend.data_managers import GrammarRuleManagerDB, VocabManagerDB
        
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        
        try:
            from backend.data_managers import OriginalTextManagerDB
            grammar_db_mgr = GrammarRuleManagerDB(session)
            vocab_db_mgr = VocabManagerDB(session)
            text_db_mgr = OriginalTextManagerDB(session)
            
            # 🔧 修复：不再同步所有内存中的文章，因为：
            # 1. global_dc.text_manager.original_texts 包含所有用户的数据（没有用户隔离）
            # 2. 文章应该通过文章上传API处理，而不是在这里同步
            # 3. 如果需要在同步vocab/grammar时确保文章存在，应该在创建example时检查
            print("📄 [Sync] 跳过文章同步（文章应通过上传API处理，且global_dc包含所有用户数据）")
            
            # 🔧 可选：如果需要，可以同步当前操作相关的文章
            # 从 session_state 获取当前文章ID
            current_text_id = None
            if hasattr(session_state, 'current_sentence') and session_state.current_sentence:
                current_text_id = getattr(session_state.current_sentence, 'text_id', None)
            
            if current_text_id and user_id:
                try:
                    # 检查当前文章是否存在于数据库中，且属于当前用户
                    from database_system.business_logic.models import OriginalText
                    text_model = session.query(OriginalText).filter(
                        OriginalText.text_id == current_text_id,
                        OriginalText.user_id == user_id
                    ).first()
                    if not text_model:
                        print(f"⚠️ [Sync] 当前文章 (ID: {current_text_id}) 在数据库中不存在或不属于用户 {user_id}")
                        print(f"  ℹ️  文章应通过文章上传API导入到数据库")
                    else:
                        print(f"✅ [Sync] 当前文章存在于数据库: {text_model.text_title} (ID: {current_text_id})")
                except Exception as e:
                    print(f"⚠️ [Sync] 检查当前文章时出错: {e}")
            
            # 同步 Grammar Rules（只同步本轮新增的）
            print(f"📚 [Sync] 同步本轮新增的 Grammar Rules (共{len(session_state.grammar_to_add)}个)...")
            synced_grammar = 0
            for grammar_item in session_state.grammar_to_add:
                rule_name = grammar_item.rule_name
                rule_explanation = grammar_item.rule_explanation
                
                # 🔧 修复：直接使用add_new_rule，它内部使用get_or_create逻辑（按user_id和rule_name检查）
                # 如果已存在（属于当前用户），会返回现有记录；如果不存在或属于其他用户，会创建新记录
                # 注意：这里没有language，因为在main_assistant中已经创建时传递了language
                # 但为了保持一致性，我们仍然调用add_new_rule（它会在已存在时跳过）
                # 实际上，在main_assistant中已经创建了，这里可能不需要再次创建
                # 但为了确保数据同步，我们仍然调用（get_or_create会处理已存在的情况）
                try:
                    new_rule = grammar_db_mgr.add_new_rule(
                        name=rule_name,
                        explanation=rule_explanation or '',
                        source='qa',  # 🔧 修复：使用'qa'而不是'auto'，与main_assistant保持一致
                        user_id=user_id,
                        language=None  # 🔧 注意：这里没有language，因为在main_assistant中已经创建时传递了
                    )
                    # 🔧 检查是新建还是已存在（通过检查数据库模型）
                    from database_system.business_logic.models import GrammarRule
                    grammar_model = session.query(GrammarRule).filter(
                        GrammarRule.rule_id == new_rule.rule_id
                    ).first()
                    if grammar_model:
                        # 检查创建时间是否很近（1秒内），如果是，可能是新创建的
                        import datetime
                        time_diff = (datetime.datetime.now() - grammar_model.created_at).total_seconds()
                        if time_diff < 2:
                            print(f"✅ [Sync] 新增 grammar rule: {rule_name} (ID: {new_rule.rule_id})")
                            synced_grammar += 1
                        else:
                            print(f"📝 [Sync] Grammar rule已存在（当前用户）: {rule_name} (ID: {new_rule.rule_id})")
                    
                    # 同步本轮的grammar notation（如果有）
                    for notation in session_state.created_grammar_notations:
                        # 只同步与当前rule相关的notation（通过grammar_id匹配）
                        # 注意：此时新rule刚创建，需要在assistant中先记录rule_id
                        pass  # TODO: 需要从assistant中传递grammar_id映射
                except Exception as e:
                    print(f"⚠️ [Sync] 同步 grammar rule 时出错: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 🔧 修复：vocab 和 grammar 已经在 main_assistant.add_new_to_data() 中使用数据库管理器创建了
            # 所以这里不需要再同步，因为：
            # 1. vocab 和 grammar 已经在数据库中（通过数据库管理器直接创建）
            # 2. examples 也在 main_assistant 中创建了（通过 data_controller.add_vocab_example）
            # 3. global_dc.vocab_manager.vocab_bundles 中没有数据（因为使用的是数据库管理器，不是 global_dc）
            # 
            # 如果需要在 _sync_to_database 中同步 examples，应该直接从数据库查找 vocab，而不是从 global_dc 查找
            # 但实际上 examples 已经在 main_assistant 中创建了，所以这里不需要再同步
            
            # 同步 Vocab Expressions（只同步本轮新增的）
            print(f"📖 [Sync] 同步本轮新增的 Vocab Expressions (共{len(session_state.vocab_to_add)}个)...")
            print(f"  ℹ️  注意：vocab 已在 main_assistant 中使用数据库管理器创建，这里只同步 examples（如果需要）")
            synced_vocab = 0
            
            # 从session_state获取本轮新增的vocab
            for vocab_item in session_state.vocab_to_add:
                vocab_body = vocab_item.vocab
                
                # 🔧 修复：直接从数据库查找 vocab（因为已经在 main_assistant 中创建了）
                try:
                    # 从数据库查找 vocab（按 user_id 和 vocab_body）
                    from database_system.business_logic.models import VocabExpression
                    vocab_model = session.query(VocabExpression).filter(
                        VocabExpression.vocab_body == vocab_body,
                        VocabExpression.user_id == user_id
                    ).first()
                    
                    if not vocab_model:
                        print(f"⚠️ [Sync] 在数据库中找不到vocab: {vocab_body} (user_id={user_id})")
                        print(f"  ℹ️  可能 vocab 在 main_assistant 中创建失败，或还未创建")
                        continue
                    
                    vocab_id = vocab_model.vocab_id
                    print(f"✅ [Sync] 找到vocab: {vocab_body} (ID: {vocab_id})")
                    
                    # 🔧 检查 examples 是否需要同步
                    # 实际上，examples 已经在 main_assistant 中创建了（通过 data_controller.add_vocab_example）
                    # 但 data_controller 使用的是文件系统管理器，所以 examples 可能不在数据库中
                    # 让我们检查一下数据库中是否已有 examples
                    from database_system.business_logic.models import VocabExpressionExample
                    existing_examples_count = session.query(VocabExpressionExample).filter(
                        VocabExpressionExample.vocab_id == vocab_id
                    ).count()
                    
                    # 🔧 尝试从 global_dc 获取 examples（如果存在）
                    # 注意：由于使用的是数据库管理器，global_dc 中可能没有数据
                    examples = []
                    bundle = None
                    for vid, vb in global_dc.vocab_manager.vocab_bundles.items():
                        if getattr(vb, 'vocab_body', None) == vocab_body:
                            bundle = vb
                            break
                    
                    if bundle:
                        examples = getattr(bundle, 'examples', None) or getattr(bundle, 'example', [])
                        print(f"  🔍 [Sync] 从内存中找到 {len(examples)} 个 examples")
                    else:
                        print(f"  ℹ️  [Sync] 在内存中找不到vocab bundle，examples 可能已在 main_assistant 中同步到数据库")
                        print(f"  🔍 [Sync] 数据库中已有 {existing_examples_count} 个 examples")
                        # examples 已经在数据库中，不需要再同步
                        continue
                    
                    # 🔧 同步 examples（如果内存中有，但数据库中还没有）
                    if examples and existing_examples_count == 0:
                        print(f"🔍 [Sync] 同步 Vocab {vocab_body} 的 {len(examples)} 个 examples 到数据库...")
                        added_examples = 0
                        skipped_examples = 0
                        for ex in examples:
                            try:
                                # 调试：打印example的完整信息
                                print(f"  🔍 [Debug] Example详情: text_id={ex.text_id}, sentence_id={ex.sentence_id}, type={type(ex.text_id)}")
                                
                                # 先检查text_id是否存在且属于当前用户
                                from database_system.business_logic.models import OriginalText
                                text_model = session.query(OriginalText).filter(
                                    OriginalText.text_id == ex.text_id,
                                    OriginalText.user_id == user_id
                                ).first()
                                if not text_model:
                                    print(f"  ⚠️ 跳过 example (text_id={ex.text_id} 不存在或不属于用户 {user_id}): sentence_id={ex.sentence_id}")
                                    skipped_examples += 1
                                    continue
                                
                                vocab_db_mgr.add_vocab_example(
                                    vocab_id=vocab_id,
                                    text_id=ex.text_id,
                                    sentence_id=ex.sentence_id,
                                    context_explanation=getattr(ex, 'context_explanation', ''),
                                    token_indices=getattr(ex, 'token_indices', [])
                                )
                                print(f"  ✅ 添加 example: text_id={ex.text_id}, sentence_id={ex.sentence_id}")
                                added_examples += 1
                            except Exception as ex_err:
                                print(f"  ❌ Example 添加失败: {ex_err}")
                                skipped_examples += 1
                        
                        if skipped_examples > 0:
                            print(f"  ⚠️ {skipped_examples} 个 examples 被跳过（text_id不存在或其他错误）")
                        if added_examples > 0:
                            print(f"  ✅ {added_examples} 个 examples 已同步到数据库")
                    else:
                        print(f"  ℹ️  Examples 已在数据库中或内存中不存在，跳过同步")
                        
                except Exception as e:
                    print(f"⚠️ [Sync] 处理 vocab {vocab_body} 时出错: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            session.commit()
            print(f"✅ [Sync] 数据库同步完成: {synced_grammar} grammar rules, {synced_vocab} vocab expressions")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [Sync] 数据库同步失败: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/chat")
async def chat_with_assistant(
    payload: dict, 
    background_tasks: BackgroundTasks, 
    authorization: Optional[str] = Header(None)
):
    """聊天功能（完整 MainAssistant 集成）"""
    import traceback
    try:
        import time
        request_id = int(time.time() * 1000) % 10000
        # 🔧 记录本轮请求的开始时间（用于后续汇总 token 使用）
        request_start_time = datetime.utcnow()
        
        # 🔧 支持可选认证：如果有 token 则使用认证用户，否则使用默认用户
        user_id = 2  # 默认用户 ID
        if authorization and authorization.startswith("Bearer "):
            try:
                token = authorization.replace("Bearer ", "")
                from backend.utils.auth import decode_access_token
                payload_data = decode_access_token(token)
                if payload_data and "sub" in payload_data:
                    user_id = int(payload_data["sub"])
                    print(f"✅ [Chat #{request_id}] 使用认证用户: {user_id}")
            except Exception as e:
                print(f"⚠️ [Chat #{request_id}] Token 解析失败，使用默认用户: {e}")
        else:
            print(f"ℹ️ [Chat #{request_id}] 未提供认证 token，使用默认用户: {user_id}")
        
        # 🔧 从 payload 获取 UI 语言（用于控制 AI 输出语言）
        ui_language = payload.get('ui_language', '中文')  # 默认为中文
        print("\n" + "="*80)
        print(f"💬 [Chat #{request_id}] ========== Chat endpoint called ==========")
        print(f"📥 [Chat #{request_id}] Payload: {payload}")
        print(f"👤 [Chat #{request_id}] User ID: {user_id}")
        print(f"🌐 [Chat #{request_id}] UI Language: {ui_language}")
        print("="*80)
        
        # 从 session_state 获取上下文信息
        current_sentence = session_state.current_sentence
        current_selected_token = session_state.current_selected_token
        current_input = session_state.current_input
        
        print(f"📋 [Chat #{request_id}] Session State Info:")
        print(f"  - current_input: {current_input}")
        print(f"  - current_sentence text_id: {current_sentence.text_id if current_sentence else 'None'}")
        print(f"  - current_sentence sentence_id: {current_sentence.sentence_id if current_sentence else 'None'}")
        print(f"  - current_sentence: {current_sentence.sentence_body[:50] if current_sentence else 'None'}...")
        print(f"  - current_selected_token: {current_selected_token}")
        if current_selected_token:
            print(f"    - token_text: {current_selected_token.token_text}")
            print(f"    - token_indices: {current_selected_token.token_indices if hasattr(current_selected_token, 'token_indices') else 'N/A'}")
        
        # 验证必要的参数
        if not current_sentence:
            return {
                'success': False,
                'error': 'No sentence context in session state. Please select a sentence first.'
            }
        
        if not current_input:
            current_input = payload.get('user_question', '')
            if not current_input:
                return {
                    'success': False,
                    'error': 'No user question provided'
                }
            session_state.set_current_input(current_input)
        
        # 准备 selected_text
        selected_text = None
        if current_selected_token and current_selected_token.token_text:
            if hasattr(current_selected_token, 'token_indices') and current_selected_token.token_indices == [-1]:
                selected_text = None
            elif current_selected_token.token_text.strip() == current_sentence.sentence_body.strip():
                selected_text = None
            else:
                selected_text = current_selected_token.token_text
        
        # 为本次请求创建一个独立的 SessionState 副本，避免并发请求互相干扰
        from backend.assistants.chat_info.session_state import SessionState as _SessionState
        local_state = _SessionState()
        # 拷贝当前上下文（句子、选中的 token、输入、用户）
        local_state.set_current_sentence(current_sentence)
        if current_selected_token:
            local_state.set_current_selected_token(current_selected_token)
        local_state.set_current_input(current_input)
        local_state.user_id = user_id
        print("🧹 [Chat] 使用独立的 SessionState 副本处理本轮请求")

        # 🔧 获取数据库 session（用于 token 记录和扣减以及检查token是否不足）
        from database_system.database_manager import DatabaseManager
        try:
            from backend.config import ENV
            environment = ENV
        except ImportError:
            import os
            environment = os.getenv("ENV", "development")
        db_manager = DatabaseManager(environment)
        db_session = db_manager.get_session()
        
        # 🔧 检查token是否不足（只在当前没有main assistant流程时判断）
        # 如果main assistant流程已触发，在使用过程中积分不足，仍然完成当前的AI流程
        try:
            from database_system.business_logic.models import User
            user = db_session.query(User).filter(User.user_id == user_id).first()
            if user:
                # 非admin用户且token不足1000（积分不足0.1）
                if user.role != 'admin' and (user.token_balance is None or user.token_balance < 1000):
                    db_session.close()
                    return {
                        'success': False,
                        'error': '积分不足',
                        'ai_response': None
                    }
        except Exception as e:
            print(f"⚠️ [Chat #{request_id}] 检查token不足时出错: {e}")
            # 如果检查失败，继续执行（避免影响正常流程）
        
        # 创建 MainAssistant 实例（绑定本轮独立的 session_state）
        from backend.assistants.main_assistant import MainAssistant
        main_assistant = MainAssistant(
            data_controller_instance=global_dc,
            session_state_instance=local_state
        )
        # 🔧 设置 user_id 和 session（用于 token 记录）
        main_assistant.set_user_context(user_id=user_id, session=db_session)
        
        print(f"🚀 [Chat] 调用 MainAssistant...")
        
        # 🔧 先快速生成主回答，立即返回给前端
        effective_sentence_body = selected_text if selected_text else current_sentence.sentence_body
        print("🚀 [Chat] 生成主回答...")
        try:
            ai_response = main_assistant.answer_question_function(
                quoted_sentence=current_sentence,
                user_question=current_input,
                sentence_body=effective_sentence_body
            )
        finally:
            # 确保 session 被正确关闭
            db_session.close()
        print("✅ [Chat] 主回答就绪，立即返回给前端")
        
        # 🔧 先立即返回主回答，然后在后台处理 grammar/vocab 和创建 notations
        # 这样主回答能立即显示，toast 通过后台任务完成后返回的数据显示
        
        # 保存主回答，立即返回
        initial_response = {
            'success': True,
            'data': {
                'ai_response': ai_response,
                'grammar_summaries': [],
                'vocab_summaries': [],
                'grammar_to_add': [],
                'vocab_to_add': [],
                'created_grammar_notations': [],
                'created_vocab_notations': []
            }
        }
        
        # 🔧 后台执行 grammar/vocab 处理和创建 notations
        def _run_grammar_vocab_background():
            import traceback
            from backend.assistants import main_assistant as _ma_mod
            prev_disable_grammar = getattr(_ma_mod, 'DISABLE_GRAMMAR_FEATURES', True)
            # 🔧 为后台任务创建新的数据库 session（用于 token 记录）
            from database_system.database_manager import DatabaseManager
            try:
                from backend.config import ENV
                environment = ENV
            except ImportError:
                import os
                environment = os.getenv("ENV", "development")
            bg_db_manager = DatabaseManager(environment)
            bg_db_session = bg_db_manager.get_session()
            try:
                print("🧠 [Background] 执行 handle_grammar_vocab_function...")
                _ma_mod.DISABLE_GRAMMAR_FEATURES = False
                # 🔧 为后台任务设置 user_id 和 session（用于 token 记录）
                main_assistant.set_user_context(user_id=user_id, session=bg_db_session)
                # 🔧 同步 UI 语言到 main_assistant（用于控制所有子助手输出语言）
                main_assistant.ui_language = ui_language
                print(f"🌐 [Background] 设置 UI 语言到 main_assistant: {ui_language}")
                main_assistant.handle_grammar_vocab_function(
                    quoted_sentence=current_sentence,
                    user_question=current_input,
                    ai_response=ai_response,
                    effective_sentence_body=effective_sentence_body
                )
                
                # 🔧 调用 add_new_to_data() 以创建新词汇和 notations
                print("🧠 [Background] 执行 add_new_to_data()...")
                # 🔧 关键修复：在调用 add_new_to_data() 之前，先保存 vocab_to_add 和 grammar_to_add
                # 因为 add_new_to_data() 可能会清空这些列表
                vocab_to_add_backup = list(local_state.vocab_to_add) if local_state.vocab_to_add else []
                grammar_to_add_backup = list(local_state.grammar_to_add) if local_state.grammar_to_add else []
                print(f"🔍 [Background] 备份 vocab_to_add: {len(vocab_to_add_backup)} 个, grammar_to_add: {len(grammar_to_add_backup)} 个")

                main_assistant.add_new_to_data()
                print("✅ [Background] add_new_to_data() 完成")
                
                # 🔧 关键修复：在后台任务完成后，存储新创建的 vocab_to_add 和 grammar_to_add
                # 供前端轮询获取并显示 toast
                # 🔧 使用备份的数据，因为 add_new_to_data() 可能会清空这些列表
                grammar_to_add_list = []
                vocab_to_add_list = []
                
                if grammar_to_add_backup:
                    print(f"🔍 [Background] 从备份恢复 grammar_to_add: {len(grammar_to_add_backup)} 个")
                    for g in grammar_to_add_backup:
                        grammar_to_add_list.append({'name': g.rule_name, 'explanation': g.rule_explanation})
                
                if vocab_to_add_backup:
                    print(f"🔍 [Background] 从备份恢复 vocab_to_add: {len(vocab_to_add_backup)} 个词汇")
                    for v in vocab_to_add_backup:
                        vocab_body = getattr(v, 'vocab', None)
                        vocab_id = None
                        
                        # 从数据库查询新创建的词汇
                        try:
                            from database_system.database_manager import DatabaseManager
                            from database_system.business_logic.models import VocabExpression
                            db_manager = DatabaseManager(ENV)
                            session = db_manager.get_session()
                            try:
                                vocab_model = session.query(VocabExpression).filter(
                                    VocabExpression.vocab_body == vocab_body,
                                    VocabExpression.user_id == user_id
                                ).order_by(VocabExpression.vocab_id.desc()).first()
                                if vocab_model:
                                    vocab_id = vocab_model.vocab_id
                                    print(f"✅ [Background] 从数据库找到 vocab_id={vocab_id} for vocab='{vocab_body}'")
                            finally:
                                session.close()
                        except Exception as db_err:
                            print(f"⚠️ [Background] 从数据库查询 vocab_id 失败: {db_err}")
                        
                        if vocab_id:
                            vocab_to_add_list.append({'vocab': vocab_body, 'vocab_id': vocab_id})
                            print(f"✅ [Background] 添加 vocab_to_add: vocab='{vocab_body}', vocab_id={vocab_id}")
                        else:
                            vocab_to_add_list.append({'vocab': vocab_body, 'vocab_id': None})
                
                # 存储到临时存储中，供前端轮询获取
                print(f"🔍 [Background] 检查是否需要存储知识点: grammar={len(grammar_to_add_list)}, vocab={len(vocab_to_add_list)}")
                if grammar_to_add_list or vocab_to_add_list:
                    print(f"🔍 [Background] 有知识点需要存储，检查 current_sentence...")
                    print(f"🔍 [Background] current_sentence 类型: {type(current_sentence)}")
                    print(f"🔍 [Background] current_sentence 是否有 text_id 属性: {hasattr(current_sentence, 'text_id')}")
                    text_id = current_sentence.text_id if hasattr(current_sentence, 'text_id') else None
                    print(f"🔍 [Background] 提取的 text_id: {text_id} (type={type(text_id) if text_id else 'None'})")
                    if text_id:
                        # 🔧 确保 text_id 是整数类型（与前端一致）
                        text_id = int(text_id) if text_id else None
                        print(f"🔍 [Background] 转换后的 text_id: {text_id} (type={type(text_id) if text_id else 'None'})")
                        if text_id:
                            key = (user_id, text_id)
                            pending_knowledge_points[key] = {
                                'grammar_to_add': grammar_to_add_list,
                                'vocab_to_add': vocab_to_add_list,
                                'timestamp': datetime.now().isoformat()
                            }
                            print(f"✅ [Background] 存储新知识点到临时存储: user_id={user_id}, text_id={text_id} (type={type(text_id).__name__}), grammar={len(grammar_to_add_list)}, vocab={len(vocab_to_add_list)}")
                            print(f"🔍 [Background] 临时存储的 key: {key}, 当前所有 keys: {list(pending_knowledge_points.keys())}")
                        else:
                            print(f"⚠️ [Background] text_id 转换失败，无法存储新知识点")
                    else:
                        print(f"⚠️ [Background] text_id 不存在，无法存储新知识点")
                        print(f"🔍 [Background] current_sentence 详细信息: {current_sentence}")
                else:
                    print(f"⚠️ [Background] 没有知识点需要存储（grammar_to_add_list 和 vocab_to_add_list 都为空）")
                
                # 同步到数据库
                print("💾 [Background] 同步数据到数据库...")
                _sync_to_database(user_id=user_id)
                
                # 保存到 JSON 文件（保持兼容）
                save_data_async(
                    dc=global_dc,
                    grammar_path=GRAMMAR_PATH,
                    vocab_path=VOCAB_PATH,
                    text_path=TEXT_PATH,
                    dialogue_record_path=DIALOGUE_RECORD_PATH,
                    dialogue_history_path=DIALOGUE_HISTORY_PATH
                )
                print("✅ [Background] 数据持久化完成")
                
                # 🔧 汇总并显示本轮全部 token 使用量（详细版本）
                try:
                    from database_system.business_logic.models import TokenLog
                    from sqlalchemy import func
                    # 查询从请求开始时间到现在的所有 token_logs
                    # 使用一个时间窗口（请求开始时间往前推3秒，确保包含主回答的 token 记录）
                    # 因为主回答的 token 记录可能在后台任务开始之前就已经写入
                    time_window_start = request_start_time - timedelta(seconds=3)
                    time_window_end = datetime.utcnow() + timedelta(seconds=1)  # 加1秒确保包含刚刚写入的记录
                    
                    # 1. 获取总体统计
                    token_summary = (
                        bg_db_session.query(
                            func.count(TokenLog.id).label('call_count'),
                            func.sum(TokenLog.total_tokens).label('total_tokens'),
                            func.sum(TokenLog.prompt_tokens).label('total_prompt_tokens'),
                            func.sum(TokenLog.completion_tokens).label('total_completion_tokens')
                        )
                        .filter(
                            TokenLog.user_id == user_id,
                            TokenLog.created_at >= time_window_start,
                            TokenLog.created_at <= time_window_end
                        )
                        .first()
                    )
                    
                    # 2. 获取按 assistant 分组的详细统计
                    assistant_stats = (
                        bg_db_session.query(
                            TokenLog.assistant_name,
                            func.count(TokenLog.id).label('call_count'),
                            func.sum(TokenLog.total_tokens).label('total_tokens'),
                            func.sum(TokenLog.prompt_tokens).label('total_prompt_tokens'),
                            func.sum(TokenLog.completion_tokens).label('total_completion_tokens')
                        )
                        .filter(
                            TokenLog.user_id == user_id,
                            TokenLog.created_at >= time_window_start,
                            TokenLog.created_at <= time_window_end
                        )
                        .group_by(TokenLog.assistant_name)
                        .order_by(TokenLog.assistant_name)
                        .all()
                    )
                    
                    # 3. 获取所有调用的详细列表（按时间排序）
                    all_calls = (
                        bg_db_session.query(TokenLog)
                        .filter(
                            TokenLog.user_id == user_id,
                            TokenLog.created_at >= time_window_start,
                            TokenLog.created_at <= time_window_end
                        )
                        .order_by(TokenLog.created_at)
                        .all()
                    )
                    
                    if token_summary and token_summary.total_tokens:
                        call_count = token_summary.call_count or 0
                        total_tokens = int(token_summary.total_tokens) if token_summary.total_tokens else 0
                        total_prompt = int(token_summary.total_prompt_tokens) if token_summary.total_prompt_tokens else 0
                        total_completion = int(token_summary.total_completion_tokens) if token_summary.total_completion_tokens else 0
                        
                        # 获取最终余额
                        from database_system.business_logic.models import User
                        final_user = bg_db_session.query(User).filter(User.user_id == user_id).first()
                        final_balance = final_user.token_balance if final_user else 0
                        
                        print("\n" + "="*80)
                        print(f"📊 [Token Summary] 本轮 Chat API 调用 Token 使用汇总")
                        print("="*80)
                        print(f"  👤 用户 ID: {user_id}")
                        print(f"  🔢 总 API 调用次数: {call_count}")
                        print(f"  📝 总 Prompt Tokens: {total_prompt:,}")
                        print(f"  ✍️  总 Completion Tokens: {total_completion:,}")
                        print(f"  💰 总 Token 使用量: {total_tokens:,}")
                        print(f"  💵 最终余额: {final_balance:,}")
                        print("="*80)
                        
                        # 按 Assistant 分组统计
                        if assistant_stats:
                            print(f"\n📋 按 SubAssistant 分组统计:")
                            print("-" * 80)
                            for assistant_name, a_call_count, a_total, a_prompt, a_completion in assistant_stats:
                                a_total_int = int(a_total) if a_total else 0
                                a_prompt_int = int(a_prompt) if a_prompt else 0
                                a_completion_int = int(a_completion) if a_completion else 0
                                assistant_display = assistant_name or "Unknown"
                                print(f"  • {assistant_display}:")
                                print(f"     调用次数: {a_call_count}")
                                print(f"     Prompt: {a_prompt_int:,} | Completion: {a_completion_int:,} | 总计: {a_total_int:,}")
                        
                        # 详细调用列表
                        if all_calls:
                            print(f"\n📝 详细调用记录（按时间顺序）:")
                            print("-" * 80)
                            for idx, call in enumerate(all_calls, 1):
                                assistant_display = call.assistant_name or "Unknown"
                                call_time = call.created_at.strftime("%H:%M:%S.%f")[:-3] if call.created_at else "N/A"
                                print(f"  {idx}. [{call_time}] {assistant_display}")
                                print(f"     Prompt: {call.prompt_tokens:,} | Completion: {call.completion_tokens:,} | 总计: {call.total_tokens:,}")
                        
                        print("="*80 + "\n")
                    else:
                        print("⚠️ [Token Summary] 未找到本轮 token 使用记录")
                except Exception as summary_error:
                    print(f"⚠️ [Token Summary] 汇总 token 使用量时出错: {summary_error}")
                    import traceback
                    traceback.print_exc()
            except Exception as bg_e:
                print(f"❌ [Background] 后台流程失败: {bg_e}")
                traceback.print_exc()
            finally:
                try:
                    _ma_mod.DISABLE_GRAMMAR_FEATURES = prev_disable_grammar
                except Exception:
                    pass
                # 🔧 确保后台任务的 session 被正确关闭
                try:
                    bg_db_session.close()
                except Exception as e:
                    print(f"⚠️ [Background] 关闭 session 时出错: {e}")
        
        # 启动后台任务
        background_tasks.add_task(_run_grammar_vocab_background)
        
        # 🔧 立即返回主回答，不等待后续流程
        print(f"📋 [Chat] 立即返回主回答给前端（后续流程在后台执行）")
        
        return initial_response
    except Exception as e:
        print(f"❌ [Chat] Error: {e}")
        print(traceback.format_exc())
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        }

@app.get("/api/chat/pending-knowledge")
async def get_pending_knowledge(
    user_id: int = Query(..., description="用户ID"),
    text_id: int = Query(..., description="文章ID"),
    authorization: Optional[str] = Header(None)
):
    """
    获取后台任务创建的新知识点（vocab_to_add 和 grammar_to_add）
    供前端轮询获取并显示 toast
    """
    try:
        # 🔧 确保 text_id 是整数类型（与存储时一致）
        text_id = int(text_id) if text_id else None
        if not text_id:
            print(f"⚠️ [PendingKnowledge] text_id 无效: {text_id}")
            return {
                'success': True,
                'data': {
                    'grammar_to_add': [],
                    'vocab_to_add': []
                }
            }
        
        key = (user_id, text_id)
        print(f"🔍 [PendingKnowledge] ========== 查询新知识点 ==========")
        print(f"🔍 [PendingKnowledge] 查找 key: {key}")
        print(f"🔍 [PendingKnowledge] key 类型: {type(key)}")
        print(f"🔍 [PendingKnowledge] 当前所有 keys: {list(pending_knowledge_points.keys())}")
        print(f"🔍 [PendingKnowledge] 当前所有 keys 的类型: {[type(k) for k in pending_knowledge_points.keys()]}")
        print(f"🔍 [PendingKnowledge] pending_knowledge_points 总数量: {len(pending_knowledge_points)}")
        
        if key in pending_knowledge_points:
            data = pending_knowledge_points[key]
            print(f"✅ [PendingKnowledge] 找到数据: grammar={len(data.get('grammar_to_add', []))}, vocab={len(data.get('vocab_to_add', []))}")
            print(f"✅ [PendingKnowledge] grammar_to_add 详情: {data.get('grammar_to_add', [])}")
            print(f"✅ [PendingKnowledge] vocab_to_add 详情: {data.get('vocab_to_add', [])}")
            # 返回后删除，避免重复获取
            del pending_knowledge_points[key]
            print(f"✅ [PendingKnowledge] 返回新知识点: user_id={user_id}, text_id={text_id}, grammar={len(data['grammar_to_add'])}, vocab={len(data['vocab_to_add'])}")
            print(f"🔍 [PendingKnowledge] 删除后，剩余 keys: {list(pending_knowledge_points.keys())}")
            return {
                'success': True,
                'data': {
                    'grammar_to_add': data['grammar_to_add'],
                    'vocab_to_add': data['vocab_to_add']
                }
            }
        else:
            print(f"⚠️ [PendingKnowledge] key {key} 不存在于临时存储中")
            return {
                'success': True,
                'data': {
                    'grammar_to_add': [],
                    'vocab_to_add': []
                }
            }
    except Exception as e:
        print(f"❌ [PendingKnowledge] 获取新知识点失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

@app.get("/api/vocab-example-by-location")
async def get_vocab_example_by_location(
    text_id: int = Query(..., description="文章ID"),
    sentence_id: Optional[int] = Query(None, description="句子ID"),
    token_index: Optional[int] = Query(None, description="Token索引"),
    current_user: User = Depends(get_current_user),
):
    """按位置查找词汇例句"""
    try:
        print(f"🔍 [VocabExample] Searching by location: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}")
        
        # 🔧 修复：从数据库查询，而不是从 global_dc（文件系统管理器）查询
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import VocabExpressionExample, OriginalText
        from backend.adapters import VocabExampleAdapter
        
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        
        try:
            # ✅ 强制使用当前认证用户（确保数据隔离）
            user_id = int(current_user.user_id)
            
            # 🔧 先检查 text_id 是否属于当前用户（如果是登录用户）
            if user_id:
                text_model = session.query(OriginalText).filter(
                    OriginalText.text_id == text_id,
                    OriginalText.user_id == user_id
                ).first()
                if not text_model:
                    print(f"⚠️ [VocabExample] text_id={text_id} 不存在或不属于用户 {user_id}")
                    return {
                        'success': False,
                        'data': None,
                        'message': f'Text not found or access denied'
                    }
            
            # 🔧 查询匹配的 example
            # 1. 首先按 text_id 和 sentence_id 查找，并通过 vocab_id 关联到 VocabExpression 来过滤 user_id
            from database_system.business_logic.models import VocabExpression
            
            print(f"🔍 [VocabExample] Query params: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}, user_id={user_id}")
            
            query = session.query(VocabExpressionExample).join(
                VocabExpression,
                VocabExpressionExample.vocab_id == VocabExpression.vocab_id
            ).filter(
                VocabExpressionExample.text_id == text_id
            )
            
            # 🔧 如果有 user_id，只查询属于该用户的 vocab 的 example
            if user_id:
                query = query.filter(VocabExpression.user_id == user_id)
                print(f"🔍 [VocabExample] Filtering by user_id={user_id}")
            else:
                # 理论上不会发生（当前接口强制认证）
                print(f"⚠️ [VocabExample] No user_id provided (unexpected), refusing to query cross-user data")
                return {'success': False, 'data': None, 'message': 'Unauthorized'}
            
            if sentence_id is not None:
                query = query.filter(VocabExpressionExample.sentence_id == sentence_id)
                print(f"🔍 [VocabExample] Filtering by sentence_id={sentence_id}")
            
            examples = query.all()
            print(f"🔍 [VocabExample] Found {len(examples)} example(s) before token_index filtering (user_id={user_id})")
            
            # ✅ 不再跨用户回退查询（确保用户数据隔离）
            for ex in examples:
                vocab_model = session.query(VocabExpression).filter(VocabExpression.vocab_id == ex.vocab_id).first()
                print(f"  - Example: vocab_id={ex.vocab_id}, text_id={ex.text_id}, sentence_id={ex.sentence_id}, token_indices={ex.token_indices}, vocab_user_id={vocab_model.user_id if vocab_model else 'N/A'}")
            
            # 🔧 2. 如果有 token_index，进一步过滤（检查 token_indices 是否包含 token_index）
            # 🔧 修复：如果 token_indices 为空，说明 example 是为整个句子创建的，应该匹配任何 token_index
            # 🔧 修复：如果 token_index 不匹配，但 example 存在，也应该返回（因为 example 已经存在，说明这个句子和词汇有关联）
            if token_index is not None:
                matching_examples = []
                for ex in examples:
                    # token_indices 是 JSON 列，可能是列表或 None
                    token_indices = ex.token_indices if ex.token_indices else []
                    print(f"🔍 [VocabExample] Checking example: vocab_id={ex.vocab_id}, token_indices={token_indices}, looking for token_index={token_index}")
                    
                    # 🔧 如果 token_indices 为空，说明 example 是为整个句子创建的，应该匹配
                    if len(token_indices) == 0:
                        print(f"✅ [VocabExample] Match found (empty token_indices, sentence-level example): vocab_id={ex.vocab_id}")
                        matching_examples.append(ex)
                    elif token_index in token_indices:
                        matching_examples.append(ex)
                        print(f"✅ [VocabExample] Match found: vocab_id={ex.vocab_id}")
                    else:
                        # 🔧 修复：即使 token_index 不匹配，但如果 example 存在，也应该返回
                        # 因为 example 已经存在，说明这个句子和词汇有关联，只是可能使用了不同的 token_index
                        print(f"⚠️ [VocabExample] Token index mismatch, but example exists: token_index={token_index} not in token_indices={token_indices}, but returning example anyway")
                        matching_examples.append(ex)
                        print(f"✅ [VocabExample] Match found (despite token_index mismatch): vocab_id={ex.vocab_id}")
                examples = matching_examples
                print(f"🔍 [VocabExample] After token_index filtering: {len(examples)} example(s)")
            
            if examples:
                # 🔧 使用第一个匹配的 example
                example_model = examples[0]
                print(f"✅ [VocabExample] Found {len(examples)} example(s)")
                
                # 🔧 转换为 DTO，然后转换为字典
                example_dto = VocabExampleAdapter.model_to_dto(example_model)
                
                example_dict = {
                    'vocab_id': example_dto.vocab_id,
                    'text_id': example_dto.text_id,
                    'sentence_id': example_dto.sentence_id,
                    'context_explanation': example_dto.context_explanation,
                    'token_indices': example_dto.token_indices,
                    'token_index': token_index  # 添加 token_index 供前端使用
                }
                
                return {
                    'success': True,
                    'data': example_dict,
                    'message': f'Found vocab example'
                }
            else:
                print(f"❌ [VocabExample] No example found")
                return {
                    'success': False,
                    'data': None,
                    'message': f'No vocab example found'
                }
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [VocabExample] Error: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@app.get("/api/vocab", response_model=ApiResponse)
async def get_vocab_list(current_user: User = Depends(get_current_user)):
    """获取词汇列表（兼容端点：强制按当前用户过滤，避免数据泄露）"""
    try:
        from database_system.business_logic.models import VocabExpression
        from database_system.database_manager import DatabaseManager
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            vocabs = session.query(VocabExpression).filter(VocabExpression.user_id == current_user.user_id).all()
            data = [
                {
                    "vocab_id": v.vocab_id,
                    "user_id": v.user_id,
                    "vocab_body": v.vocab_body,
                    "explanation": v.explanation,
                    "language": v.language,
                    "source": getattr(v.source, "value", v.source),
                    "is_starred": v.is_starred,
                    "learn_status": getattr(v.learn_status, "value", v.learn_status),
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "updated_at": v.updated_at.isoformat() if v.updated_at else None,
                }
                for v in vocabs
            ]
        finally:
            session.close()
        
        return create_success_response(
            data=data,
            message=f"成功获取词汇列表（user_id={current_user.user_id}），共 {len(data)} 条记录"
        )
    except Exception as e:
        return create_error_response(f"获取词汇列表失败: {str(e)}")

@app.get("/api/vocab/{vocab_id}", response_model=ApiResponse)
async def get_vocab_detail(vocab_id: int, current_user: User = Depends(get_current_user)):
    """获取词汇详情（兼容端点：强制按当前用户过滤，避免数据泄露）"""
    try:
        from database_system.business_logic.models import VocabExpression
        from database_system.database_manager import DatabaseManager
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            vocab = session.query(VocabExpression).filter(
                VocabExpression.vocab_id == vocab_id,
                VocabExpression.user_id == current_user.user_id,
            ).first()
            if not vocab:
                return create_error_response(f"词汇不存在或无权限访问: {vocab_id}")
            data = {
                "vocab_id": vocab.vocab_id,
                "user_id": vocab.user_id,
                "vocab_body": vocab.vocab_body,
                "explanation": vocab.explanation,
                "language": vocab.language,
                "source": getattr(vocab.source, "value", vocab.source),
                "is_starred": vocab.is_starred,
                "learn_status": getattr(vocab.learn_status, "value", vocab.learn_status),
                "created_at": vocab.created_at.isoformat() if vocab.created_at else None,
                "updated_at": vocab.updated_at.isoformat() if vocab.updated_at else None,
            }
        finally:
            session.close()
        
        return create_success_response(
            data=data,
            message=f"成功获取词汇详情: {data.get('vocab_body')}"
        )
    except Exception as e:
        return create_error_response(f"获取词汇详情失败: {str(e)}")

@app.get("/api/grammar", response_model=ApiResponse)
async def get_grammar_list(current_user: User = Depends(get_current_user)):
    """获取语法规则列表（兼容端点：强制按当前用户过滤，避免数据泄露）"""
    try:
        from database_system.business_logic.models import GrammarRule
        from database_system.database_manager import DatabaseManager
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            rules = session.query(GrammarRule).filter(GrammarRule.user_id == current_user.user_id).all()
            data = [
                {
                    "rule_id": r.rule_id,
                    "user_id": r.user_id,
                    "rule_name": r.rule_name,
                    "rule_summary": r.rule_summary,
                    "language": r.language,
                    "source": getattr(r.source, "value", r.source),
                    "is_starred": r.is_starred,
                    "learn_status": getattr(r.learn_status, "value", r.learn_status),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
                for r in rules
            ]
        finally:
            session.close()
        
        return create_success_response(
            data=data,
            message=f"成功获取语法规则列表（user_id={current_user.user_id}），共 {len(data)} 条记录"
        )
    except Exception as e:
        return create_error_response(f"获取语法规则列表失败: {str(e)}")

@app.get("/api/grammar/{rule_id}", response_model=ApiResponse)
async def get_grammar_detail(rule_id: int, current_user: User = Depends(get_current_user)):
    """获取单个语法规则详情（兼容端点：重定向到 v2 API）"""
    try:
        from database_system.business_logic.models import GrammarRule, Sentence
        from database_system.database_manager import DatabaseManager
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            # 查询语法规则（确保属于当前用户）
            grammar_rule = session.query(GrammarRule).filter(
                GrammarRule.rule_id == rule_id,
                GrammarRule.user_id == current_user.user_id
            ).first()
            
            if not grammar_rule:
                raise HTTPException(status_code=404, detail=f"语法规则 ID {rule_id} 不存在或不属于当前用户")
            
            # 获取例句数据
            examples_data = []
            if grammar_rule.examples:
                for ex in grammar_rule.examples:
                    original_sentence = None
                    try:
                        if ex.text_id is not None and ex.sentence_id is not None:
                            sentence_obj = session.query(Sentence).filter(
                                Sentence.text_id == ex.text_id,
                                Sentence.sentence_id == ex.sentence_id
                            ).first()
                            if sentence_obj:
                                original_sentence = sentence_obj.sentence_body
                    except Exception as se:
                        print(f"⚠️ [GrammarAPI] 获取例句原句失败: text_id={ex.text_id}, sentence_id={ex.sentence_id}, error={se}")
                    
                    examples_data.append({
                        "rule_id": ex.rule_id,
                        "text_id": ex.text_id,
                        "sentence_id": ex.sentence_id,
                        "original_sentence": original_sentence,
                        "explanation_context": ex.explanation_context,
                    })
            
            data = {
                "rule_id": grammar_rule.rule_id,
                "rule_name": grammar_rule.rule_name,
                "rule_summary": grammar_rule.rule_summary,
                "name": grammar_rule.rule_name,  # 保留兼容性
                "explanation": grammar_rule.rule_summary,  # 保留兼容性
                "language": grammar_rule.language,
                "source": grammar_rule.source.value if hasattr(grammar_rule.source, 'value') else str(grammar_rule.source),
                "is_starred": grammar_rule.is_starred,
                "learn_status": grammar_rule.learn_status.value if hasattr(grammar_rule.learn_status, 'value') else (str(grammar_rule.learn_status) if grammar_rule.learn_status else "not_mastered"),
                "created_at": grammar_rule.created_at.isoformat() if grammar_rule.created_at else None,
                "updated_at": grammar_rule.updated_at.isoformat() if grammar_rule.updated_at else None,
                "examples": examples_data
            }
            
            return create_success_response(
                data=data,
                message=f"成功获取语法规则详情（rule_id={rule_id}）"
            )
        finally:
            session.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_error_response(f"获取语法规则详情失败: {str(e)}")

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
async def list_articles(current_user: User = Depends(get_current_user)):
    """
    获取文章列表摘要（已废弃，重定向到数据库版本）
    
    ⚠️ 此端点已废弃，现在从数据库查询，只返回属于当前用户的文章。
    建议前端直接使用 /api/v2/texts/ 端点。
    """
    try:
        print(f"⚠️ [API] /api/articles 被调用（用户 {current_user.user_id}），重定向到数据库查询")
        
        # 🔧 从数据库查询，确保用户隔离
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import OriginalText
        from backend.config import ENV
        
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        
        try:
            # 查询当前用户的所有文章
            texts = session.query(OriginalText).filter(
                OriginalText.user_id == current_user.user_id
            ).order_by(OriginalText.created_at.desc()).all()
            
            summaries = [
                {
                    "text_id": t.text_id,
                    "text_title": t.text_title,
                    "language": t.language,
                    "processing_status": t.processing_status,
                    "sentence_count": 0,  # 简化版本，不计算句子数
                    "total_sentences": 0
                }
                for t in texts
            ]
            
            print(f"✅ [API] 从数据库获取 {len(summaries)} 篇文章（用户 {current_user.user_id}）")
            return create_success_response(
                data=summaries,
                message=f"成功获取文章列表，共 {len(summaries)} 篇（仅当前用户）"
            )
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [API] 获取文章列表失败: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"获取文章列表失败: {str(e)}")

@app.get("/api/v2/texts/fallback")
async def get_texts_fallback():
    """文章列表回退接口（使用文件系统数据）"""
    try:
        summaries = _collect_articles_summary()
        return {
            "success": True,
            "data": {
                "texts": summaries,
                "count": len(summaries),
                "source": "filesystem"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/articles/{article_id}", response_model=ApiResponse)
async def get_article_detail(
    article_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    获取单篇文章详情（数据库版本，带用户隔离）
    
    ⚠️ 此接口已改为从数据库查询，只返回属于当前用户的文章。
    """
    try:
        print(f"🔍 [API] /api/articles/{article_id} 被调用 - user_id: {current_user.user_id}")
        
        # 🔧 从数据库查询，确保用户隔离
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import OriginalText
        from backend.config import ENV
        
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        
        try:
            # 查询文章，确保属于当前用户
            text_model = session.query(OriginalText).filter(
                OriginalText.text_id == article_id,
                OriginalText.user_id == current_user.user_id
            ).first()
            
            if not text_model:
                print(f"❌ [API] 文章 {article_id} 不存在或不属于用户 {current_user.user_id}")
                return create_error_response(
                    f"文章不存在或无权访问: {article_id}",
                    status_code=404
                )
            
            # 使用 v2 API 的数据格式
            from backend.data_managers import OriginalTextManagerDB
            from backend.adapters.text_adapter import SentenceAdapter
            from database_system.business_logic.models import Sentence as SentenceModel
            
            text_manager = OriginalTextManagerDB(session)
            text = text_manager.get_text_by_id(article_id, include_sentences=True)
            
            if not text:
                return create_error_response(f"文章不存在: {article_id}", status_code=404)

            # 转换为前端期望的格式
            # 🔧 注意：TextDTO 没有 processing_status 字段，需要从 text_model 获取
            # 🔧 注意：TextDTO 的句子字段是 text_by_sentence，不是 sentences
            text_sentences = getattr(text, 'text_by_sentence', None) or getattr(text, 'sentences', None) or []
            
            # 🔧 获取语言代码（用于 tokens 处理）
            from backend.preprocessing.language_classification import get_language_code, is_non_whitespace_language
            language_code = get_language_code(text.language) if text.language else None
            is_non_whitespace = is_non_whitespace_language(language_code) if language_code else None
            
            # 构建完整的句子数据（包含 tokens）
            sentences_data = []
            for s in text_sentences:
                # 获取句子的 tokens（如果 DTO 中有）
                sentence_tokens = getattr(s, 'tokens', None) or []
                word_tokens = getattr(s, 'word_tokens', None) or []
                
                # 构建 tokens 数组
                tokens = []
                if sentence_tokens:
                    # 从 DTO 的 tokens 构建
                    for t in sentence_tokens:
                        tokens.append({
                            "token_body": t.token_body,
                            "sentence_token_id": t.sentence_token_id,
                            "token_type": str(t.token_type).lower() if t.token_type else "text",
                            "difficulty_level": t.difficulty_level,
                            "global_token_id": getattr(t, "global_token_id", None),
                            "pos_tag": getattr(t, "pos_tag", None),
                            "lemma": getattr(t, "lemma", None),
                            "word_token_id": getattr(t, "word_token_id", None),
                            "selectable": True,
                        })
                else:
                    # Fallback: 按空格切分 sentence_body
                    words = (s.sentence_body or "").split()
                    tokens = [
                        {
                            "token_body": word,
                            "sentence_token_id": idx,
                            "token_type": "text",
                            "selectable": True,
                        }
                        for idx, word in enumerate(words)
                    ]
                
                # 构建 word_tokens 数组
                word_tokens_data = []
                if word_tokens:
                    for wt in word_tokens:
                        word_tokens_data.append({
                            "word_token_id": wt.word_token_id,
                            "word_body": wt.word_body,
                            "token_ids": list(wt.token_ids) if hasattr(wt.token_ids, '__iter__') else [],
                            "pos_tag": getattr(wt, "pos_tag", None),
                            "lemma": getattr(wt, "lemma", None),
                            "linked_vocab_id": getattr(wt, "linked_vocab_id", None),
                        })
                
                sentences_data.append({
                    "sentence_id": s.sentence_id,
                    "sentence_body": s.sentence_body,
                    "difficulty_level": getattr(s, 'sentence_difficulty_level', None) or getattr(s, 'difficulty_level', None),
                    "grammar_annotations": list(getattr(s, 'grammar_annotations', None) or []),
                    "vocab_annotations": list(getattr(s, 'vocab_annotations', None) or []),
                    "tokens": tokens,
                    "word_tokens": word_tokens_data,
                    "language": text.language,
                    "language_code": language_code,
                    "is_non_whitespace": is_non_whitespace,
                })
            
            data = {
                "text_id": text.text_id,
                "text_title": text.text_title,
                "language": text.language,
                "processing_status": getattr(text_model, 'processing_status', 'completed'),  # 从 text_model 获取
                "sentences": sentences_data
            }
            
            # 标记 token 的可选择性
            data = _mark_tokens_selectable(data)

            print(f"✅ [API] 成功获取文章 {article_id}（用户 {current_user.user_id}）")
            return create_success_response(
                data=data,
                message=f"成功获取文章详情: {text.text_title}"
            )
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [API] 获取文章详情失败: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"获取文章详情失败: {str(e)}")

# 新增：文件上传处理API
@app.post("/api/upload/file", response_model=ApiResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form("Untitled Article"),
    language: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并进行预处理（需要认证）
    
    - **file**: 上传的文件（支持 .txt, .md, .pdf 格式）
    - **title**: 文章标题（可选）
    - **language**: 语言（中文、英文、德文），必填
    
    需要认证：是
    """
    try:
        user_id = current_user.user_id
        print(f"📤 [Upload] 用户 {user_id} 上传文件: {file.filename}, 标题: {title}, 语言: {language}")
        
        # 验证语言参数
        if not language or language not in ['中文', '英文', '德文']:
            return create_error_response("语言参数无效，请选择：中文、英文、德文")
        
        # 读取文件内容
        content = await file.read()
        filename = (file.filename or "").lower()

        # 根据文件类型处理内容
        if filename.endswith(".txt") or filename.endswith(".md"):
            # 尽量不因编码问题失败
            text_content = content.decode("utf-8", errors="replace")
        elif filename.endswith(".pdf"):
            if not extract_text_from_pdf_bytes:
                return create_error_response("PDF 提取器未初始化（extract_text_from_pdf_bytes 不可用）")
            print("🔍 [Upload] 使用 PDF 提取器从文件提取正文...")
            text_content = extract_text_from_pdf_bytes(content) or ""
            if not text_content.strip():
                return create_error_response("无法从 PDF 提取正文内容（可能是扫描版/图片PDF）")
        else:
            return create_error_response(f"不支持的文件格式: {file.filename}")
        
        # 检查内容长度
        if len(text_content) > MAX_ARTICLE_LENGTH:
            print(f"⚠️ [Upload] 文件内容长度超出限制: {len(text_content)} > {MAX_ARTICLE_LENGTH}")
            return create_error_response(
                f"文章长度超出限制（{len(text_content)} 字符 > {MAX_ARTICLE_LENGTH} 字符）",
                data={
                    "error_code": "CONTENT_TOO_LONG",
                    "content_length": len(text_content),
                    "max_length": MAX_ARTICLE_LENGTH,
                    "original_content": text_content  # 返回原始内容供前端截取
                }
            )
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 先创建文章记录（状态为"processing"），这样用户可以在处理过程中看到文章
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import OriginalText
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            # 创建文章记录（状态为"processing"）
            text_model = OriginalText(
                text_id=article_id,
                text_title=title,
                user_id=user_id,
                language=language,
                processing_status='processing'
            )
            session.add(text_model)
            session.commit()
            print(f"✅ [Upload] 创建文章记录（处理中）: {title} (ID: {article_id})")
        except Exception as e:
            session.rollback()
            print(f"⚠️ [Upload] 创建文章记录失败: {e}")
        finally:
            session.close()
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 [Upload] 开始处理文章: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text_content, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库（会更新状态为"completed"）
            print(f"💾 [Upload] 开始导入文章到数据库...")
            import_success = import_article_to_database(result, article_id, user_id, language, title=title)
            if not import_success:
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
                # 如果导入失败，更新状态为"failed"
                session = db_manager.get_session()
                try:
                    text_model = session.query(OriginalText).filter(OriginalText.text_id == article_id).first()
                    if text_model:
                        text_model.processing_status = 'failed'
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"⚠️ [Upload] 更新文章状态失败: {e}")
                finally:
                    session.close()
            
            return create_success_response(
                data={
                    "article_id": article_id,
                    "title": title,
                    "language": language,
                    "total_sentences": result['total_sentences'],
                    "total_tokens": result['total_tokens'],
                    "user_id": user_id
                },
                message=f"文件上传并处理成功: {title}"
            )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        print(f"❌ [Upload] 文件上传处理失败: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"文件上传处理失败: {str(e)}")

# 新增：URL内容抓取API
@app.post("/api/upload/url", response_model=ApiResponse)
async def upload_url(
    url: str = Form(...),
    title: str = Form("URL Article"),
    language: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    从URL抓取内容并进行预处理（需要认证）
    
    - **url**: 要抓取的URL
    - **title**: 文章标题（可选）
    - **language**: 语言（中文、英文、德文），必填
    
    需要认证：是
    """
    try:
        user_id = current_user.user_id
        print(f"📤 [Upload] 用户 {user_id} 上传URL: {url}, 标题: {title}, 语言: {language}")
        
        # 验证语言参数
        if not language or language not in ['中文', '英文', '德文']:
            return create_error_response("语言参数无效，请选择：中文、英文、德文")
        
        # 🔧 使用 HTML 提取器从 URL 获取正文
        if extract_main_text_from_url:
            print(f"🔍 [Upload] 使用 HTML 提取器从 URL 提取正文...")
            text_content = extract_main_text_from_url(url)
            
            if not text_content or not text_content.strip():
                return create_error_response("无法从 URL 提取正文内容，请检查 URL 是否有效")
            
            print(f"✅ [Upload] HTML 提取成功，正文长度: {len(text_content)} 字符")
        else:
            # Fallback：简单抓取（不推荐，但作为备用）
            print(f"⚠️ [Upload] HTML 提取器未可用，使用简单抓取（不推荐）")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            text_content = response.text
        
        # 检查内容长度
        if len(text_content) > MAX_ARTICLE_LENGTH:
            print(f"⚠️ [Upload] 内容长度超出限制: {len(text_content)} > {MAX_ARTICLE_LENGTH}")
            return create_error_response(
                f"文章长度超出限制（{len(text_content)} 字符 > {MAX_ARTICLE_LENGTH} 字符）",
                data={
                    "error_code": "CONTENT_TOO_LONG",
                    "content_length": len(text_content),
                    "max_length": MAX_ARTICLE_LENGTH,
                    "original_content": text_content  # 返回原始内容供前端截取
                }
            )
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 先创建文章记录（状态为"processing"），这样用户可以在处理过程中看到文章
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import OriginalText
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            # 创建文章记录（状态为"processing"）
            text_model = OriginalText(
                text_id=article_id,
                text_title=title,
                user_id=user_id,
                language=language,
                processing_status='processing'
            )
            session.add(text_model)
            session.commit()
            print(f"✅ [Upload] 创建文章记录（处理中）: {title} (ID: {article_id})")
        except Exception as e:
            session.rollback()
            print(f"⚠️ [Upload] 创建文章记录失败: {e}")
        finally:
            session.close()
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 [Upload] 开始处理URL文章: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text_content, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库或返回游客数据（会更新状态为"completed"）
            print(f"💾 [Upload] 开始导入文章...")
            import_result = import_article_to_database(result, article_id, user_id, language, title=title)
            
            # 处理导入结果
            if isinstance(import_result, dict) and import_result.get('is_guest'):
                # 游客模式：返回文章数据，由前端保存到 localStorage
                print(f"👤 [Upload] 游客模式，返回文章数据供前端保存")
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "url": url,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id,
                        "is_guest": True,
                        "article_data": import_result.get('article_data')
                    },
                    message=f"URL内容抓取并处理成功: {title}（游客模式，请前端保存到本地）"
                )
            elif import_result is True:
                # 正式用户模式：已成功保存到数据库（状态已在import_article_to_database中更新为"completed"）
                print(f"✅ [Upload] 文章已成功导入数据库")
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "url": url,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id
                    },
                    message=f"URL内容抓取并处理成功: {title}"
                )
            else:
                # 导入失败，更新状态为"failed"
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
                session = db_manager.get_session()
                try:
                    text_model = session.query(OriginalText).filter(OriginalText.text_id == article_id).first()
                    if text_model:
                        text_model.processing_status = 'failed'
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"⚠️ [Upload] 更新文章状态失败: {e}")
                finally:
                    session.close()
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "url": url,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id,
                        "warning": "数据库导入失败，但文件已保存"
                    },
                    message=f"URL内容抓取并处理成功: {title}（数据库导入失败）"
                )
        else:
            # 预处理系统未初始化，更新状态为"failed"
            print(f"❌ [Upload] 预处理系统未初始化")
            session = db_manager.get_session()
            try:
                text_model = session.query(OriginalText).filter(OriginalText.text_id == article_id).first()
                if text_model:
                    text_model.processing_status = 'failed'
                    session.commit()
            except Exception as e:
                session.rollback()
                print(f"⚠️ [Upload] 更新文章状态失败: {e}")
            finally:
                session.close()
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        print(f"❌ [Upload] URL内容抓取失败: {e}")
        import traceback
        traceback.print_exc()
        # 发生异常时，更新状态为"failed"
        try:
            session = db_manager.get_session()
            try:
                text_model = session.query(OriginalText).filter(OriginalText.text_id == article_id).first()
                if text_model:
                    text_model.processing_status = 'failed'
                    session.commit()
            except Exception as update_error:
                session.rollback()
                print(f"⚠️ [Upload] 更新文章状态失败: {update_error}")
            finally:
                session.close()
        except Exception as session_error:
            print(f"⚠️ [Upload] 无法获取数据库会话: {session_error}")
        return create_error_response(f"URL内容抓取失败: {str(e)}")

# 新增：文字输入处理API
@app.post("/api/upload/text", response_model=ApiResponse)
async def upload_text(
    text: str = Form(...),
    title: str = Form("Text Article"),
    language: str = Form(...),
    skip_length_check: Optional[str] = Form(None),  # 是否跳过长度检查（用于截取后的内容）
    current_user: User = Depends(get_current_user)
):
    """
    直接处理文字内容（需要认证）
    
    - **text**: 文章文本内容
    - **title**: 文章标题（可选）
    - **language**: 语言（中文、英文、德文），必填
    
    需要认证：是
    """
    try:
        user_id = current_user.user_id
        print(f"📤 [Upload] 用户 {user_id} 上传文本, 标题: {title}, 语言: {language}")
        print(f"📏 [Upload] 接收到的文本长度: {len(text)} 字符")
        print(f"📏 [Upload] 文本前100字符: {text[:100]}")
        print(f"📏 [Upload] 文本后100字符: {text[-100:]}")
        
        # 验证语言参数
        if not language or language not in ['中文', '英文', '德文']:
            return create_error_response("语言参数无效，请选择：中文、英文、德文")
        
        if not text.strip():
            return create_error_response("文字内容不能为空")
        
        # 检查 skip_length_check 参数（FormData 传递的是字符串）
        should_skip_check = skip_length_check and skip_length_check.lower() in ('true', '1', 'yes')
        
        # 检查内容长度（如果 skip_length_check 为 True，则跳过检查）
        if not should_skip_check and len(text) > MAX_ARTICLE_LENGTH:
            print(f"⚠️ [Upload] 文本内容长度超出限制: {len(text)} > {MAX_ARTICLE_LENGTH}")
            return create_error_response(
                f"文章长度超出限制（{len(text)} 字符 > {MAX_ARTICLE_LENGTH} 字符）",
                data={
                    "error_code": "CONTENT_TOO_LONG",
                    "content_length": len(text),
                    "max_length": MAX_ARTICLE_LENGTH,
                    "original_content": text  # 返回原始内容供前端截取
                }
            )
        
        if should_skip_check:
            print(f"ℹ️ [Upload] 跳过长度检查（截取后的内容），实际长度: {len(text)} 字符")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 先创建文章记录（状态为"processing"），这样用户可以在处理过程中看到文章
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import OriginalText
        db_manager = DatabaseManager(ENV)
        session = db_manager.get_session()
        try:
            # 创建文章记录（状态为"processing"）
            text_model = OriginalText(
                text_id=article_id,
                text_title=title,
                user_id=user_id,
                language=language,
                processing_status='processing'
            )
            session.add(text_model)
            session.commit()
            print(f"✅ [Upload] 创建文章记录（处理中）: {title} (ID: {article_id})")
        except Exception as e:
            session.rollback()
            print(f"⚠️ [Upload] 创建文章记录失败: {e}")
        finally:
            session.close()
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 [Upload] 开始处理文字内容: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库或返回游客数据（会更新状态为"completed"）
            print(f"💾 [Upload] 开始导入文章...")
            import_result = import_article_to_database(result, article_id, user_id, language, title=title)
            
            # 处理导入结果
            if isinstance(import_result, dict) and import_result.get('is_guest'):
                # 游客模式：返回文章数据，由前端保存到 localStorage
                print(f"👤 [Upload] 游客模式，返回文章数据供前端保存")
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id,
                        "is_guest": True,
                        "article_data": import_result.get('article_data')
                    },
                    message=f"文字内容处理成功: {title}（游客模式，请前端保存到本地）"
                )
            elif import_result is True:
                # 正式用户模式：已成功保存到数据库
                print(f"✅ [Upload] 文章已成功导入数据库")
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id
                    },
                    message=f"文字内容处理成功: {title}"
                )
            else:
                # 导入失败，更新状态为"failed"
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
                session = db_manager.get_session()
                try:
                    text_model = session.query(OriginalText).filter(OriginalText.text_id == article_id).first()
                    if text_model:
                        text_model.processing_status = 'failed'
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"⚠️ [Upload] 更新文章状态失败: {e}")
                finally:
                    session.close()
                return create_success_response(
                    data={
                        "article_id": article_id,
                        "title": title,
                        "language": language,
                        "total_sentences": result['total_sentences'],
                        "total_tokens": result['total_tokens'],
                        "user_id": user_id,
                        "warning": "数据库导入失败，但文件已保存"
                    },
                    message=f"文字内容处理成功: {title}（数据库导入失败）"
                )
        else:
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        print(f"❌ [Upload] 文字内容处理失败: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"文字内容处理失败: {str(e)}")

# ==================== Asked Tokens API ====================

@app.get("/api/user/asked-tokens")
async def get_asked_tokens(
                          user_id: str = Query(..., description="用户ID（将被忽略，实际以当前登录用户为准）"), 
                          text_id: int = Query(..., description="文章ID"),
                          include_new_system: bool = Query(False, description="是否包含新系统数据"),
                          current_user: User = Depends(get_current_user)):
    """
    获取用户在指定文章下已提问的 token 键集合
    
    支持两种模式：
    1. 传统模式（include_new_system=False）：只返回旧系统数据
    2. 兼容模式（include_new_system=True）：合并新旧系统数据
    """
    try:
        # ✅ 强制使用当前认证用户，避免跨用户读取
        effective_user_id = str(current_user.user_id)
        if user_id != effective_user_id:
            print(f"⚠️ [AskedTokens] Ignoring user_id={user_id}, using current_user.user_id={effective_user_id}")
        print(f"[AskedTokens] Getting asked tokens for user={effective_user_id}, text_id={text_id}, include_new_system={include_new_system}")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        asked_tokens = manager.get_asked_tokens_for_article(effective_user_id, text_id)
        
        result_data = {
            "asked_tokens": list(asked_tokens),
            "count": len(asked_tokens),
            "source": "legacy_system"
        }
        
        # 如果请求包含新系统数据，合并结果
        if include_new_system:
            try:
                from data_managers.unified_notation_manager import get_unified_notation_manager
                unified_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=False)
                
                # 获取新系统的所有标注
                new_notations = unified_manager.get_notations("all", text_id, effective_user_id)
                
                # 合并数据（去重）
                all_notations = set(asked_tokens)
                all_notations.update(new_notations)
                
                result_data.update({
                    "asked_tokens": list(all_notations),
                    "count": len(all_notations),
                    "legacy_count": len(asked_tokens),
                    "new_system_count": len(new_notations),
                    "source": "merged_systems"
                })
                
                print(f"[AskedTokens] Merged data: {len(asked_tokens)} legacy + {len(new_notations)} new = {len(all_notations)} total")
                
            except Exception as e:
                print(f"[WARN] Failed to get new system data: {e}")
                # 继续使用旧系统数据
        
        print(f"[AskedTokens] Found {result_data['count']} total tokens")
        return create_success_response(
            data=result_data,
            message=f"成功获取已提问的 tokens，共 {result_data['count']} 个"
        )
    except Exception as e:
        print(f"[AskedTokens] Error getting asked tokens: {e}")
        return create_error_response(f"获取已提问 tokens 失败: {str(e)}")

@app.post("/api/user/asked-tokens")
async def mark_token_asked(payload: dict, current_user: User = Depends(get_current_user)):
    """
    标记 token 或 sentence 为已提问
    
    支持两种类型的标记：
    1. type='token': 标记单词（需要 sentence_token_id）
    2. type='sentence': 标记句子（sentence_token_id 可选）
    
    向后兼容：如果 type 未指定但 sentence_token_id 存在，默认为 'token'
    新系统集成：同时创建 VocabNotation 或 GrammarNotation
    """
    try:
        # ✅ 强制使用当前认证用户，避免跨用户写入
        user_id = str(current_user.user_id)
        text_id = payload.get("text_id")
        sentence_id = payload.get("sentence_id")
        sentence_token_id = payload.get("sentence_token_id")
        type_param = payload.get("type", None)  # 新增：标记类型
        vocab_id = payload.get("vocab_id", None)  # 新增：词汇ID
        grammar_id = payload.get("grammar_id", None)  # 新增：语法ID
        
        # 向后兼容逻辑：如果 type 未指定但 sentence_token_id 不为空，默认为 'token'
        if type_param is None:
            if sentence_token_id is not None:
                type_param = "token"
            else:
                type_param = "sentence"
        
        print(f"[AskedTokens] Marking as asked:")
        print(f"  - user_id (from current_user): {user_id}")
        print(f"  - text_id: {text_id}")
        print(f"  - sentence_id: {sentence_id}")
        print(f"  - sentence_token_id: {sentence_token_id}")
        print(f"  - type: {type_param}")
        print(f"  - vocab_id: {vocab_id}")
        print(f"  - grammar_id: {grammar_id}")
        
        # 验证必需参数
        if not text_id or sentence_id is None:
            return create_error_response("text_id 和 sentence_id 是必需的")
        
        # 如果是 token 类型，sentence_token_id 必须提供
        if type_param == "token" and sentence_token_id is None:
            return create_error_response("type='token' 时，sentence_token_id 是必需的")
        
        # 使用旧系统（向后兼容）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.mark_token_asked(
            user_id=user_id,
            text_id=text_id,
            sentence_id=sentence_id,
            sentence_token_id=sentence_token_id,
            type=type_param,
            vocab_id=vocab_id,
            grammar_id=grammar_id
        )
        
        # 同时使用新系统（向前兼容）
        if success:
            try:
                from data_managers.unified_notation_manager import get_unified_notation_manager
                unified_manager = get_unified_notation_manager(use_database=False, use_legacy_compatibility=False)
                
                if type_param == "token":
                    # 创建词汇标注
                    unified_manager.mark_notation(
                        notation_type="vocab",
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        token_id=sentence_token_id,
                        vocab_id=vocab_id
                    )
                elif type_param == "sentence":
                    # 创建语法标注
                    unified_manager.mark_notation(
                        notation_type="grammar",
                        user_id=user_id,
                        text_id=text_id,
                        sentence_id=sentence_id,
                        grammar_id=grammar_id,
                        marked_token_ids=[]
                    )
                print(f"[AskedTokens] Also created new system notation")
            except Exception as e:
                print(f"[WARN] Failed to create new system notation: {e}")
                # 不阻止旧系统操作成功
        
        if success:
            print(f" [AskedTokens] Token marked as asked successfully")
            return create_success_response(
                data={
                    "user_id": user_id,
                    "text_id": text_id,
                    "sentence_id": sentence_id,
                    "sentence_token_id": sentence_token_id
                },
                message="Token 已标记为已提问"
            )
        else:
            return create_error_response("标记 token 为已提问失败")
    except Exception as e:
        print(f" [AskedTokens] Error marking token as asked: {e}")
        return create_error_response(f"标记 token 为已提问失败: {str(e)}")

@app.delete("/api/user/asked-tokens")
async def unmark_token_asked(payload: dict, current_user: User = Depends(get_current_user)):
    """取消标记 token 为已提问"""
    try:
        # ✅ 强制使用当前认证用户，避免跨用户删除
        user_id = str(current_user.user_id)
        token_key = payload.get("token_key")
        
        print(f" [AskedTokens] Unmarking token: user={user_id}, key={token_key}")
        
        if not token_key:
            return create_error_response("token_key 是必需的")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        success = manager.unmark_token_asked(user_id, token_key)
        
        if success:
            print(f" [AskedTokens] Token unmarked successfully")
            return create_success_response(
                data={"token_key": token_key},
                message="Token 已取消标记"
            )
        else:
            return create_error_response("取消标记 token 失败")
    except Exception as e:
        print(f" [AskedTokens] Error unmarking token: {e}")
        return create_error_response(f"取消标记 token 失败: {str(e)}")

# ==================== End Asked Tokens API ====================

if __name__ == "__main__":
    import uvicorn
    
    # 打印所有注册的路由（调试用）
    print("\n" + "="*80)
    print("📋 已注册的API路由：")
    print("="*80)
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"  {methods:8} {route.path}")
    print("="*80 + "\n")
    
    print("="*80)
    print("🚀 启动数据库后端服务器（含 Chat/Session/MainAssistant）")
    print("="*80)
    print("📡 端口: 8000")
    print("📊 功能:")
    print("  ✅ Session 管理")
    print("  ✅ Chat 聊天（MainAssistant）")
    print("  ✅ Vocab/Grammar CRUD")
    print("  ✅ Notation 管理（主 ORM）")
    print("  ✅ Articles 上传与查看")
    print("="*80 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
