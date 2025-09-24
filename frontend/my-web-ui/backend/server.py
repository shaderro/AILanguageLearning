from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import sys
import uvicorn

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
result_dir = r'C:\Users\ranxi\AILanguageLearning\real_data_raw\result'
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
    print("Test token-to-vocab endpoint called")
    print(f"Request data: {request_data}")
    
    try:
        # 模拟token数据
        token_data = request_data.get('token', {})
        sentence_body = request_data.get('sentence_body', '')
        text_id = request_data.get('text_id', 1)
        sentence_id = request_data.get('sentence_id', 1)
        
        # 创建模拟的Token对象（使用新的数据模型）
        from backend.data_managers.data_classes_new import Token
        token = Token(
            token_body=token_data.get('token_body', ''),
            token_type=token_data.get('token_type', 'text'),
            difficulty_level=token_data.get('difficulty_level', 'hard'),
            global_token_id=token_data.get('global_token_id', 1),
            sentence_token_id=token_data.get('sentence_token_id', 1)
        )
        
        # 使用 TokenToVocabConverter 进行转换
        from backend.preprocessing.token_to_vocab import TokenToVocabConverter
        
        converter = TokenToVocabConverter()
        vocab_result = converter.convert_token_to_vocab(token, sentence_body, text_id, sentence_id)
        
        if vocab_result:
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
            print(f"Successfully converted token to vocab: {vocab_dict}")
            return {'success': True, 'data': vocab_dict}
        else:
            print("Failed to convert token to vocab")
            return {'success': False, 'error': 'Failed to convert token to vocab'}
    except Exception as e:
        # 将后端详细错误透传给前端，便于调试
        print(f'Error in test-token-to-vocab: {e}')
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return {
            'success': False,
            'error': str(e),
            'traceback': tb,
        }

if __name__ == '__main__':
    print('Starting debug API server on port 8000...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
