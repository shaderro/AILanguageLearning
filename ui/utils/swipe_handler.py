"""
滑动手势处理工具
"""


class SwipeHandler:
    """滑动手势处理器"""
    
    def __init__(self, threshold=30):
        self.threshold = threshold
        self.touch_start_x = None
        self.touch_start_y = None
        self.swipe_detected = False
        self.callback = None
    
    def bind_to_widget(self, widget, callback):
        """绑定到组件"""
        self.callback = callback
        widget.bind(
            on_touch_down=self._on_touch_down,
            on_touch_move=self._on_touch_move,
            on_touch_up=self._on_touch_up
        )
    
    def _on_touch_down(self, touch, *args):
        """触摸开始"""
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        self.swipe_detected = False
    
    def _on_touch_move(self, touch, *args):
        """触摸移动"""
        if not self.touch_start_x or self.swipe_detected:
            return
        
        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y
        
        # 如果水平滑动距离大于垂直滑动距离且超过阈值
        if abs(dx) > abs(dy) and abs(dx) > self.threshold:
            self.swipe_detected = True
            
            if dx > 0:  # 向右滑动
                if self.callback:
                    self.callback('right')
            else:  # 向左滑动
                if self.callback:
                    self.callback('left')
    
    def _on_touch_up(self, touch, *args):
        """触摸结束"""
        if hasattr(self, 'swipe_detected'):
            self.swipe_detected = False 