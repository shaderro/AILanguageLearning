from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
import uvicorn
# Import saver with fallbacks for both package and script execution
try:
    from .server_save_to_json import save_vocab_to_json
except Exception:
    try:
        from backend.server_save_to_json import save_vocab_to_json
    except Exception:
        import importlib
        SAVE_DIR = os.path.dirname(__file__)
        if SAVE_DIR not in sys.path:
            sys.path.insert(0, SAVE_DIR)
        save_vocab_to_json = importlib.import_module('server_save_to_json').save_vocab_to_json

# Ensure project root and backend package are importable
# server.py is at: <repo>/frontend/my-web-ui/backend/server.py
# We add: <repo>/ and <repo>/backend to sys.path
CURRENT_DIR = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..', '..', '..'))
BACKEND_DIR = os.path.join(REPO_ROOT, 'backend')
for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

print("Creating FastAPI app...")
app = FastAPI()

print("Adding CORS middleware...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

vocab_file = r'C:\Users\ranxi\AILanguageLearning\backend\data\current\vocab.json'
result_dir = r'C:\Users\ranxi\AILanguageLearning\backend\data\current\articles'
print(f"Vocab file path: {vocab_file}")
print(f"Vocab file exists: {os.path.exists(vocab_file)}")
print(f"Result dir path: {result_dir}")
print(f"Result dir exists: {os.path.exists(result_dir)}")

@app.get('/api/health')
async def health():
    print("Health endpoint called")
    return {'status': 'ok'}

@app.get('/api/vocab')
async def get_vocab_list():
    print("Vocab endpoint called")
    try:
        if os.path.exists(vocab_file):
            print("Loading vocab file...")
            with open(vocab_file, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
            print(f"Loaded {len(vocab_data)} vocab items")
            return {'data': vocab_data}
        else:
            print("Vocab file not found")
            return {'data': []}
    except Exception as e:
        print(f'Error loading vocab: {e}')
        return {'data': []}

@app.post('/api/vocab/refresh')
async def refresh_vocab_data():
    """手动刷新词汇数据"""
    print("Manual vocab refresh requested")
    try:
        if os.path.exists(vocab_file):
            with open(vocab_file, 'r', encoding='utf-8') as f:
                vocab_data = json.load(f)
            print(f"Refreshed {len(vocab_data)} vocab items")
            return {'success': True, 'message': f'Successfully refreshed {len(vocab_data)} vocab items', 'data': vocab_data}
        else:
            return {'success': False, 'message': 'Vocab file not found', 'data': []}
    except Exception as e:
        print(f'Error refreshing vocab: {e}')
        return {'success': False, 'message': str(e), 'data': []}

@app.get('/api/articles')
async def articles():
    print("Articles endpoint called")
    articles = []
    
    try:
        files = os.listdir(result_dir)
        
        for filename in files:
            if '_processed_' in filename and filename.endswith('.json'):
                filepath = os.path.join(result_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    article = {
                        'id': data.get('text_id', 1),
                        'text_id': data.get('text_id', 1),
                        'title': data.get('text_title', 'Article'),
                        'text_title': data.get('text_title', 'Article'),
                        'summary': data.get('summary', ''),
                        'total_sentences': data.get('total_sentences', 0),
                        'total_tokens': data.get('total_tokens', 0),
                        'timestamp': filename.split('_')[-2] + '_' + filename.split('_')[-1].replace('.json', '')
                    }
                    articles.append(article)
    except Exception as e:
        print(f'Error loading articles: {e}')
    
    return {'data': articles}

@app.get('/api/articles/{article_id}')
async def get_article(article_id: int):
    print(f"Get article endpoint called for ID: {article_id}")
    try:
        for filename in os.listdir(result_dir):
            if '_processed_' in filename and filename.endswith('.json'):
                filepath = os.path.join(result_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if data.get('text_id') == article_id:
                        if 'sentences' in data:
                            for sentence in data['sentences']:
                                if 'tokens' in sentence:
                                    for token in sentence['tokens']:
                                        if isinstance(token, dict) and token.get('token_type') == 'text':
                                            token['selectable'] = True
                                        else:
                                            token['selectable'] = False
                        
                        return {'data': data}
    except Exception as e:
        print(f'Error loading article: {e}')
        return {'data': None}
    
    return {'data': None}

@app.post('/api/test-token-to-vocab')
async def test_token_to_vocab(request_data: dict):
    """测试token转vocab功能"""
    print("🚀 [Backend] Test token-to-vocab endpoint called")
    print(f"📥 [Backend] Request data: {request_data}")
    
    try:
        # 解析请求数据
        token_data = request_data.get('token', {})
        sentence_body = request_data.get('sentence_body', '')
        text_id = request_data.get('text_id', 1)
        sentence_id = request_data.get('sentence_id', 1)
        
        print(f"🔍 [Backend] Parsed data:")
        print(f"  - Token data: {token_data}")
        print(f"  - Sentence body: {sentence_body}")
        print(f"  - Text ID: {text_id}")
        print(f"  - Sentence ID: {sentence_id}")
        
        # 创建Token对象（使用新的数据模型）
        from backend.data_managers.data_classes_new import Token
        token = Token(
            token_body=token_data.get('token_body', ''),
            token_type=token_data.get('token_type', 'text'),
            difficulty_level=token_data.get('difficulty_level', 'hard'),
            global_token_id=token_data.get('global_token_id', 1),
            sentence_token_id=token_data.get('sentence_token_id', 1)
        )
        
        print(f"🏗️ [Backend] Created Token object:")
        print(f"  - token_body: {token.token_body}")
        print(f"  - token_type: {token.token_type}")
        print(f"  - difficulty_level: {token.difficulty_level}")
        
        # 使用 TokenToVocabConverter 进行转换
        from backend.preprocessing.token_to_vocab import TokenToVocabConverter
        
        print("🔄 [Backend] Initializing TokenToVocabConverter...")
        converter = TokenToVocabConverter()
        
        print("⚡ [Backend] Converting token to vocab...")
        vocab_result = converter.convert_token_to_vocab(token, sentence_body, text_id, sentence_id)
        
        if vocab_result:
            print("✅ [Backend] Token to vocab conversion successful!")
            print(f"📊 [Backend] Vocab result details:")
            print(f"  - vocab_id: {vocab_result.vocab_id}")
            print(f"  - vocab_body: {vocab_result.vocab_body}")
            print(f"  - explanation: {vocab_result.explanation}")
            print(f"  - source: {vocab_result.source}")
            print(f"  - examples count: {len(vocab_result.examples)}")
            
            # 转换为字典格式返回
            vocab_dict = {
                'vocab_id': vocab_result.vocab_id,
                'vocab_body': vocab_result.vocab_body,
                'explanation': vocab_result.explanation,
                'source': vocab_result.source,
                'is_starred': vocab_result.is_starred,
                'examples': [
                    {
                        'vocab_id': ex.vocab_id,
                        'text_id': ex.text_id,
                        'sentence_id': ex.sentence_id,
                        'context_explanation': ex.context_explanation,
                        'token_indices': ex.token_indices
                    } for ex in vocab_result.examples
                ]
            }
            
            # 🆕 保存到 vocab.json 文件（模块化）
            print("💾 [Backend] Attempting to save vocab to JSON file...")
            try:
                final_id, total_count = save_vocab_to_json(vocab_file, vocab_dict)
                vocab_dict['vocab_id'] = final_id
                print(f"✅ [Backend] Successfully saved vocab to file! vocab_id: {final_id}")
                print(f"📈 [Backend] Total vocab count: {total_count}")
            except Exception as save_error:
                print(f"⚠️ [Backend] Failed to save to file: {save_error}")
                print("🔄 [Backend] Continuing with response anyway...")
            
            print(f"🎉 [Backend] Final vocab dict: {json.dumps(vocab_dict, ensure_ascii=False, indent=2)}")
            return {'success': True, 'data': vocab_dict, 'saved_to_file': True}
        else:
            print("❌ [Backend] Failed to convert token to vocab")
            return {'success': False, 'error': 'Failed to convert token to vocab'}
    except Exception as e:
        # 将后端详细错误透传给前端，便于调试
        print(f'💥 [Backend] Error in test-token-to-vocab: {e}')
        import traceback
        tb = traceback.format_exc()
        print(f'🔍 [Backend] Full traceback:\n{tb}')
        return {
            'success': False,
            'error': str(e),
            'traceback': tb,
        }

if __name__ == '__main__':
    print('Starting debug API server on port 8000...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
