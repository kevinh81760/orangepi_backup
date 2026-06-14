from threading import Thread
from queue import Queue, Empty
import cv2
from .entity import Area
from pyzbar.pyzbar import decode
from pyzbar.pyzbar import ZBarSymbol
from multiprocessing import Pipe, get_context
from time import time, sleep
from pypylon import pylon
from typing import Any

class CameraInterface:
    def open(self) -> None:
        pass

    def release(self) -> None:
        pass

    def is_open(self) -> bool:
        pass

    def read(self) -> tuple[bool, Any]:
        pass

class OpenCVCamera(CameraInterface):
    def __init__(self, port: int | str, width: int, height: int):
        self.port = port
        self.width = width
        self.height = height
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.port)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3)

    def release(self):
        if self.cap is not None and self.is_open():
            self.cap.release()

    def is_open(self):
        if self.cap is not None:
            return self.cap.isOpened()
        return False

    def read(self):
        if self.cap is not None:
            return self.cap.read()
        return False, None

class BaslerCamera(CameraInterface):
    def __init__(self):
        self.camera = None

    def open(self):
        try:
            self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
            self.camera.Open()
            # self.camera.ExposureAuto.Value = "Continuous"
            self.camera.ExposureAuto.Value = "Off"
            self.camera.ExposureTime.SetValue(10000)
            self.camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

            self.converter = pylon.ImageFormatConverter()
            self.converter.OutputPixelFormat = pylon.PixelType_BGR8packed
            self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        except Exception as e:
            self.camera = None
            print(f"Can't connect camera: {e}")

    def release(self):
        if self.camera is not None:
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            if self.camera.IsOpen():
                self.camera.Close()
            self.camera = None

    def is_open(self):
        if self.camera is not None:
            return self.camera.IsGrabbing()
        return False

    def read(self):
        if self.camera is not None:
            try:
                grabResult = self.camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                if grabResult.GrabSucceeded():
                    image = self.converter.Convert(grabResult)
                    img = image.GetArray()
                    grabResult.Release()
                    return True, img
                grabResult.Release()
            except:
                print("Can't grab image")
        return False, None
    
class Camera:
    def __init__(self, camera: CameraInterface, rois: dict, qrcode_min_size: int, qrcode_expand_size: int, qrcode_number_of_retries: int):
        self.camera = camera
        self.areas = [Area(area_id, rois[area_id]) for area_id in rois]
        self.qrcode_min_size = qrcode_min_size
        self.qrcode_expand_size = qrcode_expand_size
        self.qrcode_number_of_retries = qrcode_number_of_retries

        self.area_idxes = {}
        for i, area in enumerate(self.areas):
            self.area_idxes[area.area_id] = i
        
        self.qrcode_client_pipes = []
        self.qrcode_server_pipes = []
        for _ in range(len(self.areas)):
            client_pipe, server_pipe = Pipe()
            self.qrcode_client_pipes.append(client_pipe)
            self.qrcode_server_pipes.append(server_pipe)

    def process(self):
        split_queue = Queue(0)
        qrcode_queues = [Queue(0) for _ in range(len(self.areas))]
        qrcode_flags = [False for _ in range(len(self.areas))]
        
        def read_qrcode(img, min_size: int, expand_size: int):
            cv2.imwrite(f"{int(time())}.png", img)

            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur_img = cv2.GaussianBlur(gray_img, (0, 0), 3)
            sharpened_img = cv2.addWeighted(gray_img, 1.5, blur_img, -0.5, 0)

            for scalar in [1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
                qr_img = cv2.resize(sharpened_img, (0, 0), fx=scalar, fy=scalar)
                decoded_data = decode(qr_img, symbols=[ZBarSymbol.QRCODE])
                if len(decoded_data) > 0:
                    return decoded_data[0].data.decode()

            hist_img = cv2.equalizeHist(sharpened_img)
            for scalar in [1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
                qr_img = cv2.resize(hist_img, (0, 0), fx=scalar, fy=scalar)
                decoded_data = decode(qr_img, symbols=[ZBarSymbol.QRCODE])
                if len(decoded_data) > 0:
                    return decoded_data[0].data.decode()

            for scalar in [1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]:
                qr_img = cv2.resize(gray_img, (0, 0), fx=scalar, fy=scalar)
                decoded_data = decode(qr_img, symbols=[ZBarSymbol.QRCODE])
                if len(decoded_data) > 0:
                    return decoded_data[0].data.decode()

            return None

        def capture():
            camera = self.camera

            camera.open()
            while True:
                while camera.is_open():
                    ret, frame = camera.read()

                    if ret == False:
                        continue
                    
                    split_queue.put((frame, time()))

                camera.release()
                camera.open()
                sleep(3.0)

        def split():
            areas = self.areas
            while True:
                frame, timestamp = split_queue.get()
                if frame is None:
                    break
                
                height, width, _ = frame.shape
                for i, area in enumerate(areas):
                    if qrcode_flags[i]:
                        (x, y, w, h) = area.rois
                        if x >= 0 and x + w <= width and y >= 0 and y + h <= height:
                            qrcode_queues[i].put((frame[y:y+h, x:x+w].copy(), timestamp))

        def qrcode(area_index: int):
            min_size = self.qrcode_min_size
            expand_size = self.qrcode_expand_size
            number_of_retries = self.qrcode_number_of_retries
            server_pipe = self.qrcode_server_pipes[area_index]
            qrcode_queue = qrcode_queues[area_index]
            last_qrcode = None
            last_timestamp = 0
            while True:
                start_timestamp = server_pipe.recv()
                if start_timestamp <= last_timestamp:
                    server_pipe.send(last_qrcode)
                    continue

                qrcode_flags[area_index] = True
                attempt = 0
                last_qrcode = None
                while attempt < number_of_retries:
                    try:
                        frame, timestamp = qrcode_queue.get(timeout=0.1)
                        if timestamp < start_timestamp:
                            continue
                        last_qrcode = read_qrcode(frame, min_size, expand_size)
                        last_timestamp = timestamp
                        if last_qrcode is not None:
                            break
                        attempt += 1
                    except Empty:
                        if time() - start_timestamp >= 2.0:
                            break

                server_pipe.send(last_qrcode)
                qrcode_flags[area_index] = False

                while not qrcode_queue.empty():
                    qrcode_queue.get()

        capture_process = Thread(target=capture, daemon=True)
        capture_process.start()

        split_process = Thread(target=split, daemon=True)
        split_process.start()

        qrcode_processes = []
        for i in range(len(self.areas)):
            qrcode_process = Thread(target=qrcode, args=(i, ), daemon=True)
            qrcode_process.start()
            qrcode_processes.append(qrcode_process)

        capture_process.join()
        split_process.join()
        for qrcode_process in qrcode_processes:
            qrcode_process.join()

    def qrcode(self, area_id: int):
        area_index = self.area_idxes[area_id]
        client_pipe = self.qrcode_client_pipes[area_index]
        client_pipe.send(time())
        return client_pipe.recv()

    def run(self):
        process = get_context("spawn").Process(target=self.process, daemon=True)
        process.start()
        return process
