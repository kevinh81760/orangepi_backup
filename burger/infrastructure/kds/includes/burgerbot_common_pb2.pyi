from google.protobuf import timestamp_pb2 as _timestamp_pb2
from validate import validate_pb2 as _validate_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OrderCommand(_message.Message):
    __slots__ = ("id", "code", "level")
    ID_FIELD_NUMBER: _ClassVar[int]
    CODE_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    id: int
    code: str
    level: float
    def __init__(self, id: _Optional[int] = ..., code: _Optional[str] = ..., level: _Optional[float] = ...) -> None: ...

class OrderResultCommand(_message.Message):
    __slots__ = ("id", "is_disabled")
    ID_FIELD_NUMBER: _ClassVar[int]
    IS_DISABLED_FIELD_NUMBER: _ClassVar[int]
    id: int
    is_disabled: bool
    def __init__(self, id: _Optional[int] = ..., is_disabled: bool = ...) -> None: ...
