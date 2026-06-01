from includes import burgerbot_common_pb2 as _burgerbot_common_pb2
from validate import validate_pb2 as _validate_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetOrderRequest(_message.Message):
    __slots__ = ("tray_number",)
    TRAY_NUMBER_FIELD_NUMBER: _ClassVar[int]
    tray_number: int
    def __init__(self, tray_number: _Optional[int] = ...) -> None: ...

class GetOrderResponse(_message.Message):
    __slots__ = ("order_id", "client_id", "tray_number", "commands")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    TRAY_NUMBER_FIELD_NUMBER: _ClassVar[int]
    COMMANDS_FIELD_NUMBER: _ClassVar[int]
    order_id: int
    client_id: int
    tray_number: int
    commands: _containers.RepeatedCompositeFieldContainer[_burgerbot_common_pb2.OrderCommand]
    def __init__(self, order_id: _Optional[int] = ..., client_id: _Optional[int] = ..., tray_number: _Optional[int] = ..., commands: _Optional[_Iterable[_Union[_burgerbot_common_pb2.OrderCommand, _Mapping]]] = ...) -> None: ...

class CompleteOrderRequest(_message.Message):
    __slots__ = ("order_id", "client_id")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    order_id: int
    client_id: int
    def __init__(self, order_id: _Optional[int] = ..., client_id: _Optional[int] = ...) -> None: ...

class CompleteOrderResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class MarkFailedOrderRequest(_message.Message):
    __slots__ = ("order_id", "client_id", "completed_commands", "failed_commands")
    ORDER_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    COMPLETED_COMMANDS_FIELD_NUMBER: _ClassVar[int]
    FAILED_COMMANDS_FIELD_NUMBER: _ClassVar[int]
    order_id: int
    client_id: int
    completed_commands: _containers.RepeatedCompositeFieldContainer[_burgerbot_common_pb2.OrderResultCommand]
    failed_commands: _containers.RepeatedCompositeFieldContainer[_burgerbot_common_pb2.OrderResultCommand]
    def __init__(self, order_id: _Optional[int] = ..., client_id: _Optional[int] = ..., completed_commands: _Optional[_Iterable[_Union[_burgerbot_common_pb2.OrderResultCommand, _Mapping]]] = ..., failed_commands: _Optional[_Iterable[_Union[_burgerbot_common_pb2.OrderResultCommand, _Mapping]]] = ...) -> None: ...

class MarkFailedOrderResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...
