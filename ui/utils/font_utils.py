"""
字体工具类
处理中文字体设置和字体回退机制
"""

import os
import platform

class FontUtils:
    """字体工具类"""
    
    @staticmethod
    def get_chinese_font_family():
        """获取支持中文的字体族"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            # macOS 中文字体优先级 - 使用更通用的字体名称
            fonts = [
                "Arial Unicode MS", # Arial Unicode - 最通用的选择
                "Arial",            # Arial
                "Helvetica",        # Helvetica
                "Times",            # Times
                "Times New Roman"   # Times New Roman
            ]
        elif system == "Windows":
            # Windows 中文字体优先级
            fonts = [
                "Microsoft YaHei",  # 微软雅黑
                "SimHei",           # 黑体
                "SimSun",           # 宋体
                "Arial Unicode MS", # Arial Unicode
                "Arial"             # Arial
            ]
        elif system == "Linux":
            # Linux 中文字体优先级
            fonts = [
                "WenQuanYi Micro Hei", # 文泉驿微米黑
                "Noto Sans CJK SC",    # Noto Sans 中文简体
                "Source Han Sans CN",  # 思源黑体
                "Droid Sans Fallback", # Droid Sans
                "Arial Unicode MS",    # Arial Unicode
                "Arial"                # Arial
            ]
        else:
            # 默认字体
            fonts = ["Arial Unicode MS", "Arial"]
        
        return fonts
    
    @staticmethod
    def get_font_name():
        """获取字体名称字符串"""
        # 使用一个通用的字体名称，让Kivy自动回退到系统字体
        return "Arial"  # 使用Arial作为默认字体
    
    @staticmethod
    def get_label_font_properties():
        """获取Label组件的字体属性"""
        return {
            "font_name": FontUtils.get_font_name(),
            "font_size": 16  # 默认字体大小
        }
    
    @staticmethod
    def create_label_with_chinese_support(text, **kwargs):
        """创建支持中文的Label组件"""
        from kivy.uix.label import Label
        
        # 设置默认字体属性
        font_props = FontUtils.get_label_font_properties()
        
        # 合并用户指定的属性
        label_props = font_props.copy()
        label_props.update(kwargs)
        
        return Label(text=text, **label_props)
    
    @staticmethod
    def apply_chinese_font_to_widget(widget):
        """为现有组件应用中文字体"""
        if hasattr(widget, 'font_name'):
            widget.font_name = FontUtils.get_font_name()
        return widget 