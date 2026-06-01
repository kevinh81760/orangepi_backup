import socket
from threading import Thread
from burger.service import Service, ERROR
from datetime import datetime
import os
from enum import Enum

class REQUEST_COMMAND(Enum):
    START = 1
    FINISH = 2
    OFF = 3
    FAIL = 6
    DISABLE = 7

class RESPONSE_COMMAND(Enum):
    START = 1
    FINISH = 2
    OFF = 3
    INVALID_QRCODE = 4
    NO_DATA = 5
    FAIL = 6
    DISABLE = 7

class Data:
    def __init__(self, data_bytes: bytes = None, command_id: int = None, conveyor_id: int = None, tray_no: int = None, tasks: list = None):
        if data_bytes is None:
            self.command_id = command_id
            self.conveyor_id = conveyor_id
            self.tray_no = tray_no
            self.tasks = tasks
            self.data_bytes = self._to_bytes(command_id, conveyor_id, tray_no, tasks)
        else:
            self.data_bytes = data_bytes
            self.command_id, self.conveyor_id, self.tray_no, self.tasks = self._to_fields(data_bytes)

    def _to_bytes(self, command_id: int, conveyor_id: int, tray_no: int, tasks: list) -> bytes:
        return b''.join(
            [
                command_id.to_bytes(1, 'big') if command_id is not None else b'',
                conveyor_id.to_bytes(1, 'big') if conveyor_id is not None else b'',
                tray_no.to_bytes(2, 'big') if tray_no is not None else b''
            ] + 
            [int(task).to_bytes(1, 'big') for task in tasks] if tasks is not None else []
        )

    def _to_fields(self, data_bytes: bytes) -> tuple:
        return (
            int(data_bytes[0]) if len(data_bytes) >= 1 else 0,
            int(data_bytes[1]) if len(data_bytes) >= 2 else 0,
            int.from_bytes(data_bytes[2:4], 'big') if len(data_bytes) >= 4 else 0,
            [int(task) for task in data_bytes[4:]] if len(data_bytes) >= 4 else []
        )
    
class SocketSVR:
    def __init__(self, address: str, port: int, number_of_listeners: int, servicer: Service):
        self.address = address
        self.port = port
        self.number_of_listeners = number_of_listeners  
        self.servicer = servicer
    
    def client_thread(self, conn: socket.socket, addr):
        with conn:
            print(f"Socket {datetime.now():%Y-%m-%d %H:%M:%S}: Connected to {addr[0]}:{addr[1]}")
            while True:
                data_bytes = conn.recv(1024)
                if not data_bytes:
                    break
                
                try:
                    reqData = Data(data_bytes=data_bytes)
                    print(vars(reqData))
                    if reqData.command_id == REQUEST_COMMAND.START.value:
                        tray_no, tasks, err = self.servicer.start_tray(reqData.conveyor_id)

                        resData = None
                        if err is None:
                            resData = Data(command_id=RESPONSE_COMMAND.START.value, conveyor_id=reqData.conveyor_id, tray_no=tray_no, tasks=tasks)
                        elif err == ERROR.QRCODE_IS_INVALID:
                            resData = Data(command_id=RESPONSE_COMMAND.INVALID_QRCODE.value, conveyor_id=reqData.conveyor_id, tray_no=tray_no, tasks=tasks)
                        elif err == ERROR.TRAY_HAS_NO_DATA:
                            resData = Data(command_id=RESPONSE_COMMAND.NO_DATA.value, conveyor_id=reqData.conveyor_id, tray_no=tray_no, tasks=tasks)

                        print(vars(resData))
                        conn.send(resData.data_bytes)

                    elif reqData.command_id == REQUEST_COMMAND.FINISH.value:
                        self.servicer.finish_tray(reqData.tray_no)
                        resData = reqData
                        print(vars(resData))
                        conn.send(resData.data_bytes)

                    elif reqData.command_id == REQUEST_COMMAND.OFF.value:
                        resData = reqData
                        print(f"Shutdown")
                        conn.send(resData.data_bytes)
                        os.system("sudo shutdown -h now")

                    elif reqData.command_id == REQUEST_COMMAND.FAIL.value:
                        self.servicer.fail_tray(reqData.tray_no, reqData.tasks)
                        resData = reqData
                        print(vars(resData))
                        conn.send(resData.data_bytes)

                    elif reqData.command_id == REQUEST_COMMAND.DISABLE.value:
                        self.servicer.disable_machines(reqData.tasks)
                        resData = reqData
                        print(vars(resData))
                        conn.send(resData.data_bytes)

                    else:
                        resData = reqData
                        print(vars(resData))
                        conn.send(resData.data_bytes)

                except Exception as inst:
                    print(inst)

        print(f"Socket {datetime.now():%Y-%m-%d %H:%M:%S}: Disconnected from {addr[0]}:{addr[1]}")

    def open(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.address, self.port))
            s.listen(self.number_of_listeners)
            print(f"Socket: Listening on {self.address}:{self.port}")

            while True:
                conn, addr = s.accept()
                thread = Thread(target=self.client_thread, args=(conn, addr, ))
                thread.start()

    def run(self):
        thread = Thread(target=self.open)
        thread.start()
        return thread
