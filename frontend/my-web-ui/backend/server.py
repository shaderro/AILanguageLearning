from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

result_dir = r'E:\langApp514\real_data_raw\result'

@app.get('/api/health')
async def health():
    return {'status': 'ok'}

@app.get('/api/articles')
async def articles():
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

if __name__ == '__main__':
    print('Starting API server on port 8000...')
    uvicorn.run(app, host='0.0.0.0', port=8000)
