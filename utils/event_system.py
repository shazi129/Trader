import threading

class EventSystem:
    _instance = None
    _lock = threading.Lock()

    @staticmethod
    def get_instance():
        if EventSystem._instance is None:
            EventSystem._instance = EventSystem()
        return EventSystem._instance

    def __new__(cls):
        if not cls._instance:  # 第一次检查
            with cls._lock:
                if not cls._instance:  # 第二次检查（Double-Checked Locking）
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._listeners = {}
        
    def register_listner(self, event_type, listener):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def unregister_listener(self, event_type, listener):
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)

    def notify_listeners(self, event_type, *args, **kwargs):
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                listener(*args, **kwargs)