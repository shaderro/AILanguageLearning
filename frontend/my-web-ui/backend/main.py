from fastapi import FastAPI, Query, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import requests
import uuid
from datetime import datetime

# 首先设置路径
import os
import sys

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
    print("[OK] 使用简单文章处理器 (无AI依赖)")
except ImportError as e:
    print(f"Warning: Could not import article_processor: {e}")
    process_article = None
    save_structured_data = None

# 导入 asked tokens manager
from backend.data_managers.asked_tokens_manager import get_asked_tokens_manager

# 导入新的标注API路由
try:
    from backend.api.notation_routes import router as notation_router
    print("[OK] 加载新的标注API路由")
except ImportError as e:
    print(f"Warning: Could not import notation_routes: {e}")
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

# 添加请求日志中间件（用于调试）
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"📥 [Request] {request.method} {request.url.path}")
    # 如果是 POST 请求，记录请求体大小
    if request.method == "POST":
        body = await request.body()
        print(f"📦 [Request] Body size: {len(body)} bytes")
        # 将 body 放回，以便后续处理
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive
    response = await call_next(request)
    print(f"📤 [Response] {request.method} {request.url.path} -> {response.status_code}")
    return response

# 注册新的标注API路由
if notation_router:
    app.include_router(notation_router)
    print("[OK] 注册新的标注API路由: /api/v2/notations")

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
    
    db_manager = DatabaseManager('development')
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

# ==================== Session Management API ====================
# 这些API原本在server_frontend_mock.py中，现在添加到主服务器以支持前端功能

# 初始化全局 SessionState（使用完整的 SessionState 类）
from backend.assistants.chat_info.session_state import SessionState
from backend.assistants.chat_info.selected_token import SelectedToken
from backend.data_managers.data_classes_new import Sentence as NewSentence

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
def import_article_to_database(result: dict, article_id: int, user_id, language: str = None):
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
        
        article_data = {
            "article_id": article_id,
            "title": result.get('text_title', 'Untitled Article'),
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
        
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        
        try:
            # 验证用户是否存在
            user = session.query(User).filter(User.user_id == user_id).first()
            if not user:
                print(f"❌ [Import] 用户 {user_id} 不存在")
                return False
            
            from backend.data_managers import OriginalTextManagerDB
            from database_system.business_logic.crud import TokenCRUD
            from database_system.business_logic.models import TokenType
            
            text_manager = OriginalTextManagerDB(session)
            token_crud = TokenCRUD(session)
            
            # 1. 创建文章（使用指定的article_id）
            # 先检查文章是否已存在且属于该用户
            existing_text = text_manager.get_text_by_id(article_id, include_sentences=False)
            if existing_text:
                # 检查文章是否属于该用户（通过数据库查询验证）
                from database_system.business_logic.models import OriginalText
                text_model = session.query(OriginalText).filter(
                    OriginalText.text_id == article_id,
                    OriginalText.user_id == user_id
                ).first()
                
                if text_model:
                    print(f"⚠️ [Import] 文章 {article_id} 已存在且属于用户 {user_id}，跳过创建")
                else:
                    print(f"❌ [Import] 文章 {article_id} 已存在但属于其他用户，无法导入")
                    return False
            else:
                # 创建文章记录（使用text_manager.add_text方法，支持language参数）
                # 注意：由于需要指定article_id，我们不能直接使用add_text（它使用数据库自增ID）
                # 所以我们需要直接创建OriginalText模型并指定text_id
                from database_system.business_logic.models import OriginalText
                text_model = OriginalText(
                    text_id=article_id,
                    text_title=result.get('text_title', 'Untitled Article'),
                    user_id=user_id,
                    language=language
                )
                session.add(text_model)
                session.flush()  # 刷新以获取ID
                print(f"✅ [Import] 创建文章: {text_model.text_title} (ID: {article_id}, User: {user_id}, Language: {language})")
            
            # 2. 导入句子和tokens
            sentences = result.get('sentences', [])
            total_sentences = 0
            total_tokens = 0
            
            for sentence_data in sentences:
                sentence_id = sentence_data.get('sentence_id', total_sentences + 1)
                sentence_body = sentence_data.get('sentence_body', '')
                
                # 检查句子是否已存在
                existing_sentence = text_manager.get_sentence(article_id, sentence_id)
                if existing_sentence:
                    print(f"⚠️ [Import] 句子 {article_id}:{sentence_id} 已存在，跳过")
                    continue
                
                # 创建句子
                sentence = text_manager.add_sentence_to_text(
                    text_id=article_id,
                    sentence_text=sentence_body,
                    difficulty_level=None
                )
                total_sentences += 1
                
                # 3. 导入tokens
                tokens = sentence_data.get('tokens', [])
                for token_data in tokens:
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
                    
                    # 创建token（传递枚举名称字符串，数据库期望枚举名称）
                    token_crud.create(
                        text_id=article_id,
                        sentence_id=sentence_id,
                        token_body=token_body,
                        token_type=token_type_name,  # 传递枚举名称字符串（'TEXT', 'PUNCTUATION', 'SPACE'）
                        sentence_token_id=sentence_token_id,
                        pos_tag=token_data.get('pos_tag'),
                        lemma=token_data.get('lemma')
                    )
                    total_tokens += 1
                
                if total_sentences % 50 == 0:
                    print(f"📊 [Import] 已导入 {total_sentences} 个句子，{total_tokens} 个tokens...")
            
            session.commit()
            print(f"✅ [Import] 导入完成: {total_sentences} 个句子，{total_tokens} 个tokens (User: {user_id}, Language: {language})")
            return True
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ [Import] 导入文章到数据库失败: {e}")
        import traceback
        traceback.print_exc()
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
        sentence = NewSentence(
            text_id=sentence_data['text_id'],
            sentence_id=sentence_data['sentence_id'],
            sentence_body=sentence_data['sentence_body'],
            tokens=tuple(sentence_data.get('tokens', []))
        )
        session_state.set_current_sentence(sentence)
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
            
            current_sentence = NewSentence(
                text_id=sentence_data['text_id'],
                sentence_id=sentence_data['sentence_id'],
                sentence_body=sentence_data['sentence_body'],
                tokens=tuple(sentence_data.get('tokens', []))
            )
            session_state.set_current_sentence(current_sentence)
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
        
        db_manager = DatabaseManager('development')
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
async def chat_with_assistant(payload: dict, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """聊天功能（完整 MainAssistant 集成）"""
    import traceback
    try:
        import time
        request_id = int(time.time() * 1000) % 10000
        user_id = current_user.user_id  # 获取当前用户ID
        
        print("\n" + "="*80)
        print(f"💬 [Chat #{request_id}] ========== Chat endpoint called ==========")
        print(f"📥 [Chat #{request_id}] Payload: {payload}")
        print(f"👤 [Chat #{request_id}] User ID: {user_id}")
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

        # 创建 MainAssistant 实例（绑定本轮独立的 session_state）
        from backend.assistants.main_assistant import MainAssistant
        main_assistant = MainAssistant(
            data_controller_instance=global_dc,
            session_state_instance=local_state
        )
        
        print(f"🚀 [Chat] 调用 MainAssistant...")
        
        # 🔧 先快速生成主回答，立即返回给前端
        effective_sentence_body = selected_text if selected_text else current_sentence.sentence_body
        print("🚀 [Chat] 生成主回答...")
        ai_response = main_assistant.answer_question_function(
            quoted_sentence=current_sentence,
            user_question=current_input,
            sentence_body=effective_sentence_body
        )
        print("✅ [Chat] 主回答就绪，立即返回给前端")
        
        # 🔧 先立即返回主回答，然后在后台处理 grammar/vocab 和创建 notations
        # 这样主回答能立即显示，notations 通过轮询获取
        
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
            from backend.assistants import main_assistant as _ma_mod
            prev_disable_grammar = getattr(_ma_mod, 'DISABLE_GRAMMAR_FEATURES', True)
            try:
                print("🧠 [Background] 执行 handle_grammar_vocab_function...")
                _ma_mod.DISABLE_GRAMMAR_FEATURES = False
                main_assistant.handle_grammar_vocab_function(
                    quoted_sentence=current_sentence,
                    user_question=current_input,
                    ai_response=ai_response,
                    effective_sentence_body=effective_sentence_body
                )
                
                # 🔧 调用 add_new_to_data() 以创建新词汇和 notations
                print("🧠 [Background] 执行 add_new_to_data()...")
                main_assistant.add_new_to_data()
                print("✅ [Background] add_new_to_data() 完成")
                
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
            except Exception as bg_e:
                print(f"❌ [Background] 后台流程失败: {bg_e}")
                traceback.print_exc()
            finally:
                try:
                    _ma_mod.DISABLE_GRAMMAR_FEATURES = prev_disable_grammar
                except Exception:
                    pass
        
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

@app.get("/api/vocab-example-by-location")
async def get_vocab_example_by_location(
    text_id: int = Query(..., description="文章ID"),
    sentence_id: Optional[int] = Query(None, description="句子ID"),
    token_index: Optional[int] = Query(None, description="Token索引"),
    authorization: Optional[str] = Header(None)
):
    """按位置查找词汇例句"""
    try:
        print(f"🔍 [VocabExample] Searching by location: text_id={text_id}, sentence_id={sentence_id}, token_index={token_index}")
        
        # 🔧 修复：从数据库查询，而不是从 global_dc（文件系统管理器）查询
        from database_system.database_manager import DatabaseManager
        from database_system.business_logic.models import VocabExpressionExample, OriginalText
        from backend.adapters import VocabExampleAdapter
        
        db_manager = DatabaseManager('development')
        session = db_manager.get_session()
        
        try:
            # 🔧 修复：支持 guest 用户（没有 token 时）
            user_id = None
            if authorization and authorization.startswith("Bearer "):
                try:
                    token = authorization.replace("Bearer ", "")
                    from backend.utils.auth import decode_access_token
                    payload = decode_access_token(token)
                    if payload and "sub" in payload:
                        user_id = int(payload["sub"])
                except Exception:
                    # 如果 token 无效，继续作为 guest 用户
                    pass
            
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
                print(f"⚠️ [VocabExample] No user_id provided, querying all users' examples")
            
            if sentence_id is not None:
                query = query.filter(VocabExpressionExample.sentence_id == sentence_id)
                print(f"🔍 [VocabExample] Filtering by sentence_id={sentence_id}")
            
            examples = query.all()
            print(f"🔍 [VocabExample] Found {len(examples)} example(s) before token_index filtering (user_id={user_id})")
            
            # 🔧 修复：如果按当前用户找不到 example，尝试查询所有用户的 example
            # 因为 example 是针对句子的，不是针对用户的，所以应该允许跨用户查询
            if len(examples) == 0:
                print(f"⚠️ [VocabExample] 没有找到属于用户 {user_id} 的 example，尝试查询所有用户的 example")
                fallback_query = session.query(VocabExpressionExample).join(
                    VocabExpression,
                    VocabExpressionExample.vocab_id == VocabExpression.vocab_id
                ).filter(
                    VocabExpressionExample.text_id == text_id
                )
                if sentence_id is not None:
                    fallback_query = fallback_query.filter(VocabExpressionExample.sentence_id == sentence_id)
                examples = fallback_query.all()
                print(f"🔍 [VocabExample] 所有用户的 example 数量: {len(examples)}")
                for ex in examples[:5]:  # 只打印前5个
                    vocab_model = session.query(VocabExpression).filter(VocabExpression.vocab_id == ex.vocab_id).first()
                    print(f"  - Example: vocab_id={ex.vocab_id}, text_id={ex.text_id}, sentence_id={ex.sentence_id}, token_indices={ex.token_indices}, vocab_user_id={vocab_model.user_id if vocab_model else 'N/A'}")
            else:
                # 打印找到的 examples 的详细信息
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
async def list_articles(current_user: User = Depends(get_current_user)):
    """
    获取文章列表摘要（文件系统版本，已废弃，建议使用 /api/v2/texts/）
    
    ⚠️ 警告：此端点没有用户隔离，返回所有文件系统中的文章。
    建议使用 /api/v2/texts/ 端点，它有完整的用户隔离。
    """
    try:
        # 即使使用文件系统，也记录用户信息（用于调试）
        print(f"⚠️ [API] /api/articles 被调用（用户 {current_user.user_id}），此端点没有用户隔离")
        summaries = _collect_articles_summary()
        return create_success_response(
            data=summaries,
            message=f"成功获取文章列表，共 {len(summaries)} 篇（⚠️ 注意：包含所有用户的文章）"
        )
    except Exception as e:
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
    title: str = Form("Untitled Article"),
    language: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """
    上传文件并进行预处理（需要认证）
    
    - **file**: 上传的文件（支持 .txt, .md 格式）
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
            print(f"📝 [Upload] 开始处理文章: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text_content, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库
            print(f"💾 [Upload] 开始导入文章到数据库...")
            import_success = import_article_to_database(result, article_id, user_id, language)
            if not import_success:
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
            
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
        
        # 抓取URL内容（添加User-Agent避免被网站阻止）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        # 简单提取文本内容（这里可以集成更复杂的HTML解析）
        text_content = response.text
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 [Upload] 开始处理URL文章: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text_content, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库或返回游客数据
            print(f"💾 [Upload] 开始导入文章...")
            import_result = import_article_to_database(result, article_id, user_id, language)
            
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
                # 正式用户模式：已成功保存到数据库
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
                # 导入失败
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
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
            return create_error_response("预处理系统未初始化")
            
    except Exception as e:
        print(f"❌ [Upload] URL内容抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return create_error_response(f"URL内容抓取失败: {str(e)}")

# 新增：文字输入处理API
@app.post("/api/upload/text", response_model=ApiResponse)
async def upload_text(
    text: str = Form(...),
    title: str = Form("Text Article"),
    language: str = Form(...),
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
        
        # 验证语言参数
        if not language or language not in ['中文', '英文', '德文']:
            return create_error_response("语言参数无效，请选择：中文、英文、德文")
        
        if not text.strip():
            return create_error_response("文字内容不能为空")
        
        # 生成文章ID
        article_id = int(datetime.now().timestamp())
        
        # 使用简单文章处理器处理文章
        if process_article:
            print(f"📝 [Upload] 开始处理文字内容: {title} (用户 {user_id}, 语言: {language})")
            result = process_article(text, article_id, title, language=language)
            
            # 保存到文件系统
            save_structured_data(result, RESULT_DIR)
            
            # 保存到数据库或返回游客数据
            print(f"💾 [Upload] 开始导入文章...")
            import_result = import_article_to_database(result, article_id, user_id, language)
            
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
                # 导入失败
                print(f"⚠️ [Upload] 数据库导入失败，但文件系统保存成功")
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
async def get_asked_tokens(user_id: str = Query(..., description="用户ID"), 
                          text_id: int = Query(..., description="文章ID"),
                          include_new_system: bool = Query(False, description="是否包含新系统数据")):
    """
    获取用户在指定文章下已提问的 token 键集合
    
    支持两种模式：
    1. 传统模式（include_new_system=False）：只返回旧系统数据
    2. 兼容模式（include_new_system=True）：合并新旧系统数据
    """
    try:
        print(f"[AskedTokens] Getting asked tokens for user={user_id}, text_id={text_id}, include_new_system={include_new_system}")
        
        # 使用 JSON 文件模式（测试阶段）
        manager = get_asked_tokens_manager(use_database=False)
        asked_tokens = manager.get_asked_tokens_for_article(user_id, text_id)
        
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
                new_notations = unified_manager.get_notations("all", text_id, user_id)
                
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
async def mark_token_asked(payload: dict):
    """
    标记 token 或 sentence 为已提问
    
    支持两种类型的标记：
    1. type='token': 标记单词（需要 sentence_token_id）
    2. type='sentence': 标记句子（sentence_token_id 可选）
    
    向后兼容：如果 type 未指定但 sentence_token_id 存在，默认为 'token'
    新系统集成：同时创建 VocabNotation 或 GrammarNotation
    """
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
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
        print(f"  - user_id: {user_id}")
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
async def unmark_token_asked(payload: dict):
    """取消标记 token 为已提问"""
    try:
        user_id = payload.get("user_id", "default_user")  # 默认用户ID
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
