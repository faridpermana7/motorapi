from typing import Generic, TypeVar

from pydantic import BaseModel


RecordT = TypeVar("RecordT")


class PaginationResponseDTO(BaseModel, Generic[RecordT]):
    records: list[RecordT]
    total: int
    skip: int
    limit: int
