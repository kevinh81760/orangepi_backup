from burger.infrastructure.database import Database
from burger.infrastructure.camera import Camera, OpenCVCamera, BaslerCamera
from burger.infrastructure.kds import KDS
from burger.service import Service
from burger.interface.socketsvr import SocketSVR

def Run(config):
    socket_address = config["socket"]["address"]
    socket_port = config["socket"]["port"]
    socket_listeners = config["socket"]["listeners"]

    sqlite_file = config["sqlite"]["file"]

    camera = None
    if "opencv" in config["camera"]:
        opencv = config["camera"]["opencv"]
        width = opencv["width"]
        height = opencv["height"]
        port = opencv["port"]
        camera = OpenCVCamera(port, width, height)
    elif "basler" in config["camera"]:
        camera = BaslerCamera()

    qrcode_retries = config["camera"]["qrcode_retries"]
    qrcode_min_size = config["camera"]["qrcode_min_size"]
    qrcode_expand_size = config["camera"]["qrcode_expand_size"]

    conveyors = config["conveyors"]

    init_conveyors = [None] * len(conveyors)
    rois = {}
    for idx, conveyor in enumerate(conveyors):
        init_conveyors[idx] = {
            "conveyor_id": conveyor["conveyor_id"],
            "conveyor_name": conveyor["conveyor_name"]
        }
        rois[conveyor["conveyor_id"]] = conveyor["roi"]

    kds_url = config["kds"]["url"]

    databaser = Database(sqlite_file)
    cameraer = Camera(camera, rois, qrcode_min_size, qrcode_expand_size, qrcode_retries)
    kdser = KDS(kds_url)
    servicer = Service(databaser, cameraer, kdser, init_conveyors)
    socket = SocketSVR(socket_address, socket_port, socket_listeners, servicer)

    procs = []
    procs.append(cameraer.run())
    procs.append(socket.run())
    for proc in procs:
        proc.join()
