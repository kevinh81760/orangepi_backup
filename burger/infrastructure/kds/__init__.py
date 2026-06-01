import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .kds import KDS
from services.burgerbot.connector_pb2 import GetOrderRequest, GetOrderResponse, CompleteOrderRequest, CompleteOrderResponse, MarkFailedOrderRequest, MarkFailedOrderResponse
from includes.burgerbot_common_pb2 import OrderCommand, OrderResultCommand