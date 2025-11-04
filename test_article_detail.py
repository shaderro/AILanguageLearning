import requests
import json

try:
    # 测试文章详情API
    r = requests.get('http://localhost:8001/api/v2/texts/1?include_sentences=true', timeout=5)
    print(f'Status: {r.status_code}')
    
    if r.status_code == 200:
        data = r.json()
        print(f'Success: {data.get("success")}')
        
        text_data = data.get("data", {})
        print(f'\nText ID: {text_data.get("text_id")}')
        print(f'Title: {text_data.get("text_title")}')
        print(f'Sentence count: {text_data.get("sentence_count")}')
        
        sentences = text_data.get("sentences", [])
        print(f'Sentences in response: {len(sentences)}')
        
        if sentences:
            print(f'\nFirst sentence:')
            s = sentences[0]
            print(f'  sentence_id: {s.get("sentence_id")}')
            print(f'  sentence_body: {s.get("sentence_body")[:100] if s.get("sentence_body") else "None"}')
        else:
            print('\n⚠️ No sentences returned!')
            
        # 同时检查数据库是否有数据
        print('\n--- 检查数据库 ---')
        from database_system.database_manager import DatabaseManager
        from backend.data_managers import OriginalTextManagerDB
        
        db = DatabaseManager('development')
        session = db.get_session()
        mgr = OriginalTextManagerDB(session)
        
        text = mgr.get_text_by_id(1, include_sentences=True)
        if text:
            print(f'DB Text ID: {text.text_id}')
            print(f'DB Title: {text.text_title}')
            print(f'DB Sentences: {len(text.text_by_sentence)}')
            if text.text_by_sentence:
                print(f'DB First sentence: {text.text_by_sentence[0].sentence_body[:100]}')
        else:
            print('⚠️ Text not found in database!')
            
        session.close()
            
    else:
        print(f'Error response: {r.text[:500]}')
        
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()

