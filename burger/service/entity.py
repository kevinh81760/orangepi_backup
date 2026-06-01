class Conveyor:
    def __init__(self, conveyor_id: int = None, conveyor_name: str = None):
        self.conveyor_id = conveyor_id
        self.conveyor_name = conveyor_name

class Machine:
    def __init__(self, machine_id: int = None, machine_arrange: int = None, machine_name: str = None, station_id: int = None):
        self.machine_id = machine_id
        self.machine_arrange = machine_arrange
        self.machine_name = machine_name
        self.station_id = station_id