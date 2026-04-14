from dataclasses import dataclass
from datetime import datetime


@dataclass
class FetchResponse:
    source: str
    page: int
    fetched_at: datetime
    payload: dict
    has_more: bool


@dataclass
class SQLQuery:
    table: str
    conflict_key: str
    fields: dict
