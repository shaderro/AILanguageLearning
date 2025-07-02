#!/usr/bin/env python3
"""
测试运行脚本
用于运行 DialogueRecordBySentence 的测试用例
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    # 运行所有测试
    loader = unittest.TestLoader()
    start_dir = 'data_managers'
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 根据测试结果设置退出码
    sys.exit(not result.wasSuccessful()) 