from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class BaseAdapter(ABC):
    def __init__(self, config: dict):
        self.config = config
        self.connection = None

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        pass

    @abstractmethod
    def execute_query(self, query: str) -> Tuple[List[Dict], int]:
        """Returns (rows, rows_affected)"""
        pass

    @abstractmethod
    def fetch_before_image(self, table: str, where_clause: str) -> List[Dict]:
        pass

    @abstractmethod
    def execute_recovery_sql(self, sql: str) -> bool:
        pass

    def is_connected(self) -> bool:
        return self.connection is not None
