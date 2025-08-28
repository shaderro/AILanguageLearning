from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

# 导入自定义模块
from models import ApiResponse
from services import data_service
from utils import create_success_response, create_error_response

app = FastAPI(
    title="语言学习 API", 
    description="词汇和语法学习 API，支持统一响应格式",
    version="1.0.0"
)

# 启用 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # React 开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=ApiResponse)
async def root():
    """根路径，返回 API 状态信息"""
    return create_success_response(
        data={
            "message": "语言学习 API 正在运行！",
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
    """健康检查"""
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
        
        # 查找匹配的词汇
        for vocab in vocab_list:
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
        
        # 未找到单词
        return create_error_response(f"未找到单词: {word}")
        
    except Exception as e:
        return create_error_response(f"查询单词失败: {str(e)}")


@app.get("/api/grammar/{rule_id}", response_model=ApiResponse)
async def get_grammar_by_id(rule_id: int):
    """按规则ID查询"""
    try:
        grammar = data_service.get_grammar_by_id(rule_id)
        
        if grammar is None:
            return create_error_response(f"未找到 ID 为 {rule_id} 的语法规则")
        
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
            message=f"成功获取词汇列表，共 {len(vocab_list)} 条记录"
        )
        
    except Exception as e:
        return create_error_response(f"获取词汇列表失败: {str(e)}")


@app.get("/api/vocab/{vocab_id}", response_model=ApiResponse)
async def get_vocab_by_id(vocab_id: int):
    """根据 ID 获取单个词汇详情"""
    try:
        vocab = data_service.get_vocab_by_id(vocab_id)
        
        if vocab is None:
            return create_error_response(f"未找到 ID 为 {vocab_id} 的词汇")
        
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 