class Station:
    def __init__(self, station_id: int, station_arrange: int, station_name: str, station_min_level: int, station_max_level: int, station_prefix: str, station_suffix: str, station_has_multi_machine: bool):
        self.station_id = station_id
        self.station_arrange = station_arrange
        self.station_name = station_name
        self.station_min_level = station_min_level
        self.station_max_level = station_max_level
        self.station_prefix = station_prefix
        self.station_suffix = station_suffix
        self.station_has_multi_machine = station_has_multi_machine

class Machine:
    def __init__(self, machine_id: int, machine_arrange: int, machine_name: str, station_id: int):
        self.machine_id = machine_id
        self.machine_arrange = machine_arrange
        self.machine_name = machine_name
        self.station_id = station_id

class DisabledMachine:
    def __init__(self, machine_id: int):
        self.machine_id = machine_id

class Tray:
    def __init__(self, tray_no: int, order_id: int, client_id: int):
        self.tray_no = tray_no
        self.order_id = order_id
        self.client_id = client_id

class TrayMachine:
    def __init__(self, tray_no: int, machine_id: int, command_id: int, tray_machine_level: int):
        self.tray_no = tray_no
        self.machine_id = machine_id
        self.command_id = command_id
        self.tray_machine_level = tray_machine_level
