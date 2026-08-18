"""
Personal AI OS - Custom Types
兼容 SQLite 和 PostgreSQL 的类型
"""
import json
from sqlalchemy import TypeDecorator, String


class CompatibleJSON(TypeDecorator):
    """兼容 SQLite 和 PostgreSQL 的 JSON 类型"""
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return None
    
    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None


class CompatibleUUID(TypeDecorator):
    """兼容 SQLite 和 PostgreSQL 的 UUID 类型"""
    impl = String
    cache_ok = True
    
    def __init__(self, as_uuid=True, **kwargs):
        self.as_uuid = as_uuid
        super().__init__(**kwargs)
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return None
    
    def process_result_value(self, value, dialect):
        return value
