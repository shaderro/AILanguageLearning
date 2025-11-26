#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML 正文提取模块
从 URL 获取原始 HTML，自动抽取正文（去掉导航、标题、链接、作者信息等）
"""

import re
from typing import Optional
from urllib.parse import urlparse

def extract_main_text_from_url(url: str) -> str:
    """
    输入 URL，返回网页正文（纯文本）
    自动清洗掉：
    - 页面标题
    - 作者/日期栏
    - 网站导航区域
    - 页脚
    - 所有 HTML 标签、超链接（但保留文本内容）
    
    Args:
        url: 网页 URL
        
    Returns:
        str: 提取的正文文本
    """
    if not url or not url.strip():
        return ""
    
    url = url.strip()
    
    # 验证 URL 格式
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {url}")
    except Exception as e:
        print(f"❌ [HTML Extractor] Invalid URL: {e}")
        return ""
    
    # 方案1：尝试使用 trafilatura（推荐）
    try:
        import trafilatura
        print(f"🔍 [HTML Extractor] 使用 trafilatura 提取正文...")
        
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if text:
                cleaned_text = _clean_extracted_text(text)
                print(f"✅ [HTML Extractor] trafilatura 提取成功，正文长度: {len(cleaned_text)} 字符")
                return cleaned_text
    except ImportError:
        print(f"⚠️ [HTML Extractor] trafilatura 未安装，尝试 fallback...")
    except Exception as e:
        print(f"⚠️ [HTML Extractor] trafilatura 提取失败: {e}，尝试 fallback...")
    
    # 方案2：fallback 到 readability-lxml
    try:
        from readability import Document
        import requests
        
        print(f"🔍 [HTML Extractor] 使用 readability-lxml 提取正文...")
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        doc = Document(response.text)
        html_content = doc.summary()
        
        if html_content:
            text = _extract_text_from_html(html_content)
            cleaned_text = _clean_extracted_text(text)
            print(f"✅ [HTML Extractor] readability-lxml 提取成功，正文长度: {len(cleaned_text)} 字符")
            return cleaned_text
    except ImportError:
        print(f"⚠️ [HTML Extractor] readability-lxml 未安装，尝试 fallback...")
    except Exception as e:
        print(f"⚠️ [HTML Extractor] readability-lxml 提取失败: {e}，尝试 fallback...")
    
    # 方案3：手动回退到 BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        import requests
        
        print(f"🔍 [HTML Extractor] 使用 BeautifulSoup 提取正文...")
        
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 移除不需要的元素
        for element in soup.find_all(['nav', 'footer', 'header', 'script', 'style', 'noscript']):
            element.decompose()
        
        # 移除特定 class 的元素
        unwanted_classes = ['sidebar', 'menu', 'share', 'advertisement', 'sponsored', 'comment', 
                           'ad', 'ads', 'advertisement', 'social', 'related', 'recommendation']
        for class_name in unwanted_classes:
            for element in soup.find_all(class_=re.compile(class_name, re.I)):
                element.decompose()
        
        # 优先提取 <article>、<main> 内容
        main_content = None
        for tag in ['article', 'main']:
            element = soup.find(tag)
            if element:
                main_content = element
                break
        
        # 如果没有找到 article 或 main，尝试提取所有 <p> 标签
        if not main_content:
            main_content = soup
        
        # 提取文本
        text = main_content.get_text(separator='\n', strip=True)
        cleaned_text = _clean_extracted_text(text)
        
        print(f"✅ [HTML Extractor] BeautifulSoup 提取成功，正文长度: {len(cleaned_text)} 字符")
        return cleaned_text
        
    except ImportError:
        print(f"❌ [HTML Extractor] BeautifulSoup 未安装，无法提取正文")
        return ""
    except Exception as e:
        print(f"❌ [HTML Extractor] BeautifulSoup 提取失败: {e}")
        return ""


def _extract_text_from_html(html_content: str) -> str:
    """
    从 HTML 内容中提取纯文本
    
    Args:
        html_content: HTML 字符串
        
    Returns:
        str: 纯文本
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except:
        # 简单回退：使用正则表达式移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', html_content)
        return text


def _clean_extracted_text(text: str) -> str:
    """
    清洗提取的文本
    
    清洗规则：
    - 去掉多余换行（连续3个以上换行符合并为2个）
    - 去掉"来源：…"、"阅读更多"等模式
    - 去除首尾空白
    
    Args:
        text: 原始文本
        
    Returns:
        str: 清洗后的文本
    """
    if not text:
        return ""
    
    # 去掉特定文本模式
    patterns_to_remove = [
        r'来源[：:].*?$',  # "来源：xxx"
        r'阅读更多.*?$',  # "阅读更多"
        r'Read more.*?$',  # "Read more"
        r'继续阅读.*?$',  # "继续阅读"
        r'查看更多.*?$',  # "查看更多"
        r'点击查看.*?$',  # "点击查看"
        r'分享到.*?$',  # "分享到"
        r'Share.*?$',  # "Share"
    ]
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查是否匹配需要移除的模式
        should_remove = False
        for pattern in patterns_to_remove:
            if re.search(pattern, line, re.IGNORECASE):
                should_remove = True
                break
        
        if not should_remove:
            cleaned_lines.append(line)
    
    # 合并文本
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 去掉多余换行（连续3个以上换行符合并为2个）
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # 去除首尾空白
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text

