"""
通用数据绑定服务基类
提供核心的数据绑定和同步功能
"""

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, DictProperty
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from ..viewmodels.base_viewmodel import BaseViewModel

class BaseDataBindingService(EventDispatcher):
    """通用数据绑定服务基类"""
    
    # 数据控制器引用
    data_controller = ObjectProperty(None)
    
    # 存储绑定关系
    _viewmodels = DictProperty({})
    _bindings = DictProperty({})
    _data_cache = DictProperty({})
    
    def __init__(self, data_controller=None, **kwargs):
        super().__init__(**kwargs)
        self.data_controller = data_controller
        self._viewmodels = {}
        self._bindings = {}
        self._data_cache = {}
    
    def register_viewmodel(self, name: str, viewmodel: 'BaseViewModel') -> bool:
        """注册ViewModel
        
        Args:
            name: ViewModel名称
            viewmodel: ViewModel实例
            
        Returns:
            bool: 注册是否成功
        """
        try:
            self._viewmodels[name] = viewmodel
            print(f"BaseDataBindingService: 注册ViewModel - {name}")
            return True
        except Exception as e:
            print(f"BaseDataBindingService: 注册ViewModel失败 - {e}")
            return False
    
    def unregister_viewmodel(self, name: str) -> bool:
        """注销ViewModel
        
        Args:
            name: ViewModel名称
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if name in self._viewmodels:
                del self._viewmodels[name]
                # 清理相关绑定
                self._cleanup_bindings_for_viewmodel(name)
                print(f"BaseDataBindingService: 注销ViewModel - {name}")
                return True
            return False
        except Exception as e:
            print(f"BaseDataBindingService: 注销ViewModel失败 - {e}")
            return False
    
    def bind_data_to_viewmodel(self, data_key: str, viewmodel_name: str, 
                              property_name: str, transform_func: Optional[Callable] = None) -> bool:
        """绑定数据到ViewModel属性
        
        Args:
            data_key: 数据键名
            viewmodel_name: ViewModel名称
            property_name: ViewModel属性名
            transform_func: 数据转换函数（可选）
            
        Returns:
            bool: 绑定是否成功
        """
        try:
            if viewmodel_name not in self._viewmodels:
                print(f"BaseDataBindingService: 错误 - ViewModel {viewmodel_name} 未注册")
                return False
            
            viewmodel = self._viewmodels[viewmodel_name]
            
            # 创建绑定记录
            binding_key = f"{data_key}_{viewmodel_name}_{property_name}"
            self._bindings[binding_key] = {
                'data_key': data_key,
                'viewmodel_name': viewmodel_name,
                'property_name': property_name,
                'viewmodel': viewmodel,
                'transform_func': transform_func
            }
            
            print(f"BaseDataBindingService: 创建数据绑定 - {data_key} -> {viewmodel_name}.{property_name}")
            return True
        except Exception as e:
            print(f"BaseDataBindingService: 创建数据绑定失败 - {e}")
            return False
    
    def unbind_data_from_viewmodel(self, data_key: str, viewmodel_name: str, property_name: str) -> bool:
        """解绑数据与ViewModel属性
        
        Args:
            data_key: 数据键名
            viewmodel_name: ViewModel名称
            property_name: ViewModel属性名
            
        Returns:
            bool: 解绑是否成功
        """
        try:
            binding_key = f"{data_key}_{viewmodel_name}_{property_name}"
            if binding_key in self._bindings:
                del self._bindings[binding_key]
                print(f"BaseDataBindingService: 解绑数据 - {data_key} -> {viewmodel_name}.{property_name}")
                return True
            return False
        except Exception as e:
            print(f"BaseDataBindingService: 解绑数据失败 - {e}")
            return False
    
    def update_data(self, data_key: str, new_value: Any, sync_immediately: bool = True) -> bool:
        """更新数据并同步到绑定的ViewModel
        
        Args:
            data_key: 数据键名
            new_value: 新数据值
            sync_immediately: 是否立即同步到ViewModel
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 更新数据缓存
            self._data_cache[data_key] = new_value
            
            # 立即同步到ViewModel
            if sync_immediately:
                self._sync_to_viewmodels(data_key, new_value)
            
            print(f"BaseDataBindingService: 更新数据 - {data_key}: {str(new_value)[:50]}...")
            return True
        except Exception as e:
            print(f"BaseDataBindingService: 更新数据失败 - {e}")
            return False
    
    def get_data(self, data_key: str) -> Any:
        """获取数据
        
        Args:
            data_key: 数据键名
            
        Returns:
            Any: 数据值
        """
        return self._data_cache.get(data_key)
    
    def sync_all_data(self) -> bool:
        """同步所有数据到ViewModel
        
        Returns:
            bool: 同步是否成功
        """
        try:
            for data_key, value in self._data_cache.items():
                self._sync_to_viewmodels(data_key, value)
            print("BaseDataBindingService: 所有数据同步完成")
            return True
        except Exception as e:
            print(f"BaseDataBindingService: 数据同步失败 - {e}")
            return False
    
    def _sync_to_viewmodels(self, data_key: str, value: Any) -> None:
        """同步数据到ViewModel
        
        Args:
            data_key: 数据键名
            value: 数据值
        """
        for binding_key, binding in self._bindings.items():
            if binding['data_key'] == data_key:
                viewmodel = binding['viewmodel']
                property_name = binding['property_name']
                transform_func = binding.get('transform_func')
                
                try:
                    # 应用数据转换函数
                    if transform_func:
                        transformed_value = transform_func(value)
                    else:
                        transformed_value = value
                    
                    # 设置ViewModel属性
                    setattr(viewmodel, property_name, transformed_value)
                    print(f"BaseDataBindingService: 同步数据 - {data_key} -> {binding['viewmodel_name']}.{property_name}")
                except Exception as e:
                    print(f"BaseDataBindingService: 同步数据失败 - {e}")
    
    def _cleanup_bindings_for_viewmodel(self, viewmodel_name: str) -> None:
        """清理指定ViewModel的所有绑定
        
        Args:
            viewmodel_name: ViewModel名称
        """
        keys_to_remove = []
        for binding_key, binding in self._bindings.items():
            if binding['viewmodel_name'] == viewmodel_name:
                keys_to_remove.append(binding_key)
        
        for key in keys_to_remove:
            del self._bindings[key]
    
    def get_binding_info(self) -> Dict[str, Any]:
        """获取绑定信息（用于调试）
        
        Returns:
            Dict: 绑定信息
        """
        return {
            'viewmodels': list(self._viewmodels.keys()),
            'bindings': list(self._bindings.keys()),
            'data_cache': list(self._data_cache.keys())
        } 