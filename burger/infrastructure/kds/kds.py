import grpc
import services.burgerbot.connector_pb2_grpc as connector_pb2_grpc
import services.burgerbot.connector_pb2 as connector_pb2

class KDS:
    def __init__(self, url: str):
        self.url = url
        self.channel = grpc.insecure_channel(self.url)

    def get_order_request(self, req: connector_pb2.GetOrderRequest) -> connector_pb2.GetOrderResponse:
        print("Start stub get_order_request")
        stub = connector_pb2_grpc.ConnectorServiceStub(self.channel)
        print("Finish stub get_order_request")
        try:
            return stub.GetOrder(req)
        except: 
            return None

    def complete_order(self, req: connector_pb2.CompleteOrderRequest):
        print("Start stub complete_order")
        stub = connector_pb2_grpc.ConnectorServiceStub(self.channel)
        print("Finish stub complete_order")
        try:
            stub.CompleteOrder(req)
        except:
            return None
        
    def mark_failed_order(self, req: connector_pb2.MarkFailedOrderRequest):
        print("Start stub mark_failed_order")
        print(req)
        stub = connector_pb2_grpc.ConnectorServiceStub(self.channel)
        print("Finish stub mark_failed_order")
        try:
            stub.MarkFailedOrder(req)
        except:
            return None
