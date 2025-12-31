class EventManager:

    # 单一实例
    _singleton = None

    def __init__(self):
        # 事件列表
        self.event_callbacks = {}

    @classmethod
    def get_singleton(cls):
        if cls._singleton is None:
            cls._singleton = cls()
        return cls._singleton

    # 处理事件
    def process_event(self, event: int, data: dict):
        if event in self.event_callbacks:
            for handler in self.event_callbacks[event]:
                try:
                    handler(event, data)
                except Exception as e:
                    print(f"[ERROR] Event handler failed: {e}")

    # 触发事件
    def emit(self, event: int, data: dict):
        # 在 CLI 版本中，我们直接同步处理事件
        # 如果后续需要异步，可以引入 threading 或 queue
        self.process_event(event, data)

    # 订阅事件
    def subscribe(self, event: int, handler: callable):
        if event not in self.event_callbacks:
            self.event_callbacks[event] = []
        if handler not in self.event_callbacks[event]:
            self.event_callbacks[event].append(handler)

    # 取消订阅事件
    def unsubscribe(self, event: int, handler: callable):
        if event in self.event_callbacks:
            try:
                self.event_callbacks[event].remove(handler)
            except ValueError:
                pass