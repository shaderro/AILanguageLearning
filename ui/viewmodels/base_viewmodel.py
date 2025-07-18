"""
通用ViewModel基类
提供基础的ViewModel功能和生命周期管理
"""

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from typing import Any, Optional, Dict, List, Callable
from abc import ABC, abstractmethod

class BaseViewModel(EventDispatcher, ABC):
    """通用ViewModel基类"""
    
    # 基础属性
    name = StringProperty('')
    is_loading = BooleanProperty(False)
    is_error = BooleanProperty(False)
    error_message = StringProperty('')
    
    # 数据绑定服务引用
    data_binding_service = ObjectProperty(None)
    
    def __init__(self, name: str = '', data_binding_service=None, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.data_binding_service = data_binding_service
        self._initialized = False
        self._cleanup_callbacks = []
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化ViewModel"""
        if self._initialized:
            return
        
        try:
            self.on_initialize()
            self._initialized = True
            print(f"BaseViewModel: {self.name} 初始化完成")
        except Exception as e:
            self.set_error(f"初始化失败: {e}")
            print(f"BaseViewModel: {self.name} 初始化失败 - {e}")
    
    @abstractmethod
    def on_initialize(self):
        """子类必须实现的初始化方法"""
        pass
    
    def set_loading(self, loading: bool):
        """设置加载状态
        
        Args:
            loading: 是否正在加载
        """
        self.is_loading = loading
        if loading:
            self.is_error = False
            self.error_message = ''
    
    def set_error(self, error_message: str):
        """设置错误状态
        
        Args:
            error_message: 错误信息
        """
        self.is_error = True
        self.error_message = error_message
        self.is_loading = False
        print(f"BaseViewModel: {self.name} 错误 - {error_message}")
    
    def clear_error(self):
        """清除错误状态"""
        self.is_error = False
        self.error_message = ''
    
    def bind_to_data_service(self, data_key: str, property_name: str, 
                           transform_func: Optional[Callable] = None) -> bool:
        """绑定到数据服务
        
        Args:
            data_key: 数据键名
            property_name: 属性名
            transform_func: 数据转换函数
            
        Returns:
            bool: 绑定是否成功
        """
        if not self.data_binding_service:
            print(f"BaseViewModel: {self.name} 数据绑定服务未设置")
            return False
        
        return self.data_binding_service.bind_data_to_viewmodel(
            data_key, self.name, property_name, transform_func
        )
    
    def unbind_from_data_service(self, data_key: str, property_name: str) -> bool:
        """从数据服务解绑
        
        Args:
            data_key: 数据键名
            property_name: 属性名
            
        Returns:
            bool: 解绑是否成功
        """
        if not self.data_binding_service:
            return False
        
        return self.data_binding_service.unbind_data_from_viewmodel(
            data_key, self.name, property_name
        )
    
    def update_data(self, data_key: str, value: Any, sync_immediately: bool = True) -> bool:
        """更新数据
        
        Args:
            data_key: 数据键名
            value: 数据值
            sync_immediately: 是否立即同步
            
        Returns:
            bool: 更新是否成功
        """
        if not self.data_binding_service:
            return False
        
        return self.data_binding_service.update_data(data_key, value, sync_immediately)
    
    def get_data(self, data_key: str) -> Any:
        """获取数据
        
        Args:
            data_key: 数据键名
            
        Returns:
            Any: 数据值
        """
        if not self.data_binding_service:
            return None
        
        return self.data_binding_service.get_data(data_key)
    
    def on_data_changed(self, data_key: str, old_value: Any, new_value: Any):
        """数据变化时的回调（子类可重写）
        
        Args:
            data_key: 数据键名
            old_value: 旧值
            new_value: 新值
        """
        pass
    
    def on_before_destroy(self):
        """销毁前的回调（子类可重写）"""
        pass
    
    def on_after_destroy(self):
        """销毁后的回调（子类可重写）"""
        pass
    
    def destroy(self):
        """销毁ViewModel"""
        try:
            self.on_before_destroy()
            
            # 执行清理回调
            for callback in self._cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"BaseViewModel: 清理回调执行失败 - {e}")
            
            # 从数据绑定服务注销
            if self.data_binding_service:
                self.data_binding_service.unregister_viewmodel(self.name)
            
            self.on_after_destroy()
            print(f"BaseViewModel: {self.name} 销毁完成")
        except Exception as e:
            print(f"BaseViewModel: {self.name} 销毁失败 - {e}")
    
    def add_cleanup_callback(self, callback: Callable):
        """添加清理回调
        
        Args:
            callback: 清理回调函数
        """
        self._cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable):
        """移除清理回调
        
        Args:
            callback: 清理回调函数
        """
        if callback in self._cleanup_callbacks:
            self._cleanup_callbacks.remove(callback)
    
    def validate_data(self, data: Any) -> bool:
        """验证数据（子类可重写）
        
        Args:
            data: 要验证的数据
            
        Returns:
            bool: 数据是否有效
        """
        return data is not None
    
    def transform_data(self, data: Any, transform_type: str) -> Any:
        """转换数据（子类可重写）
        
        Args:
            data: 原始数据
            transform_type: 转换类型
            
        Returns:
            Any: 转换后的数据
        """
        return data