from burger.infrastructure.database import Database
from burger.infrastructure.camera import Camera
from burger.infrastructure.kds import KDS, GetOrderRequest, CompleteOrderRequest, MarkFailedOrderRequest, OrderCommand, OrderResultCommand
from .entity import Conveyor, Machine
from collections import defaultdict 
from enum import Enum

class ERROR(Enum):
    QRCODE_IS_INVALID = 1
    TRAY_HAS_NO_DATA = 2

class Service:
    def __init__(self, databaser: Database, cameraer: Camera, kdser: KDS, conveyors: list):
        self.databaser = databaser
        self.cameraer = cameraer
        self.kdser = kdser
        self.conveyors = [Conveyor(conveyor["conveyor_id"], conveyor["conveyor_name"]) for conveyor in conveyors]

    def get_all_conveyors(self):
        return self.conveyors

    def get_all_stations(self):
        def _get_all_stations(cursor):
            return self.databaser.get_all_stations(cursor)
        return self.databaser.with_read_transaction(_get_all_stations)

    def get_all_machines(self):
        def _get_all_machines(cursor):
            return self.databaser.get_all_machines(cursor)
        return self.databaser.with_read_transaction(_get_all_machines)

    # Return the job of machines
    def start_tray(self, conveyor_id: int):
        tray_no = self.cameraer.qrcode(conveyor_id)
        print("Start Tray {} on Conveyor {}".format(tray_no, conveyor_id)) 

        try:
            if tray_no is not None:
                tray_no = int(tray_no)
                if not 0 < tray_no <= 65535:
                    raise(ValueError)
        except ValueError:
            tray_no = None

        def _start_tray(cursor, tray_no: int):
            err = None

            stations = self.databaser.get_all_stations(cursor)
            machines = self.databaser.get_all_machines(cursor)
            station_machines = defaultdict(list[Machine])
            for machine in machines:
                station_machines[machine.station_id].append(machine)

            machine_commands = dict[str, OrderCommand]()
            if tray_no is not None:
                print("Start to get request from KDS for Tray {}".format(tray_no)) 
                req = self.kdser.get_order_request(GetOrderRequest(tray_number=tray_no))

                if req is not None:
                    print("Finish getting request from KDS for Tray {} of Order {}".format(tray_no, req.order_id)) 

                    for command in req.commands:
                        machine_commands[command.code] = command

                    self.databaser.delete_tray_machines_by_tray(cursor, tray_no)
                    self.databaser.delete_tray(cursor, tray_no)

                    self.databaser.insert_tray(cursor, tray_no, req.order_id, req.client_id)
                else:
                    print("No data when getting request from KDS for Tray {}".format(tray_no)) 

                    err = ERROR.TRAY_HAS_NO_DATA
            else:
                err = ERROR.QRCODE_IS_INVALID
                tray_no = 0

            tasks = []
            for station in stations:
                if station.station_has_multi_machine:
                    for machine in station_machines[station.station_id]:
                        command_code = "{}_{}".format(station.station_arrange, machine.machine_arrange)
                        machine_level = 0
                        if command_code in machine_commands:
                            command = machine_commands[command_code]
                            command_level = int(command.level)
                            if station.station_min_level <= command_level <= station.station_max_level:
                                machine_level = command_level

                            if machine_level:
                                self.databaser.insert_tray_machine(cursor, tray_no, machine.machine_id, command.id, machine_level)

                        tasks.append(machine_level)
                else:
                    machine_id = 0
                    machine_level = 0
                    command_id = 0
                    for machine in station_machines[station.station_id]:
                        command_code = "{}_{}".format(station.station_arrange, machine.machine_arrange)
                        if command_code in machine_commands:
                            command = machine_commands[command_code]
                            command_level = int(command.level)
                            if not station.station_min_level <= command_level <= station.station_max_level:
                                command_level = 0
                            if command_level:
                                if machine_level < machine.machine_arrange:
                                    machine_id = machine.machine_id
                                    machine_level = machine.machine_arrange
                                    command_id = command.id

                    if machine_id:
                        self.databaser.insert_tray_machine(cursor, tray_no, machine_id, command_id, machine_level)

                    tasks.append(machine_level)

            return tray_no, tasks, err

        return self.databaser.with_write_transaction(_start_tray, (tray_no, ))

    def finish_tray(self, tray_no: int):
        if not 0 < tray_no <= 65535:
            tray_no = None
        print("Finish Tray {}".format(tray_no)) 

        def _finish_tray(cursor, tray_no: int):
            if tray_no is None:
                return

            tray = self.databaser.get_tray(cursor, tray_no)
            if tray is None:
                return

            print("Start to complete order {} by Tray {} for KDS ".format(tray.order_id, tray_no)) 
            self.kdser.complete_order(CompleteOrderRequest(order_id=tray.order_id, client_id=tray.client_id))
            print("Finish completing order {} by Tray {} for KDS ".format(tray.order_id, tray_no)) 

        self.databaser.with_read_transaction(_finish_tray, (tray_no, ))

    def fail_tray(self, tray_no: int, tasks: list[int]):
        if not 0 < tray_no <= 65535:
            tray_no = None
        print("Fail Tray {}".format(tray_no)) 
    
        def _fail_tray(cursor, tray_no: int, tasks: list[int]):
            if tray_no is None:
                return

            tray = self.databaser.get_tray(cursor, tray_no)
            if tray is None:
                return

            stations = self.databaser.get_all_stations(cursor)
            machines = self.databaser.get_all_machines(cursor)
            disabled_machines = self.databaser.get_all_disabled_machines(cursor)
            
            station_machines = defaultdict(list[Machine])
            for machine in machines:
                station_machines[machine.station_id].append(machine)

            disabled_machine_ids = defaultdict(bool)
            for disabled_machine in disabled_machines:
                disabled_machine_ids[disabled_machine.machine_id] = True
            print(disabled_machine_ids)

            tray_machines = self.databaser.get_tray_machines_by_tray(cursor, tray_no)
            machine_levels = defaultdict(int)
            for tray_machine in tray_machines:
                machine_levels[tray_machine.machine_id] = tray_machine.tray_machine_level

            task_idx = 0
            failed_machine_ids = {}
            for station in stations:
                if station.station_has_multi_machine:
                    for machine in station_machines[station.station_id]:
                        if tasks[task_idx] != machine_levels[machine.machine_id]:
                            failed_machine_ids[machine.machine_id] = True
                        task_idx += 1
                else:
                    for machine in station_machines[station.station_id]:
                        if machine_levels[machine.machine_id] and tasks[task_idx] != machine.machine_arrange:
                            failed_machine_ids[machine.machine_id] = True
                    task_idx += 1

            completed_commands = []
            failed_commands = []
            for tray_machine in tray_machines:
                command_id = tray_machine.command_id
                machine_id = tray_machine.machine_id

                if machine_id in failed_machine_ids:
                    failed_commands.append(OrderResultCommand(
                        id=command_id,
                        is_disabled=disabled_machine_ids[machine_id],
                    ))
                else:
                    completed_commands.append(OrderResultCommand(
                        id=command_id,
                        is_disabled=disabled_machine_ids[machine_id],
                    ))

            print("Start to mark failed order {} by Tray {} for KDS".format(tray.order_id, tray_no)) 
            self.kdser.mark_failed_order(MarkFailedOrderRequest(
                order_id=tray.order_id,
                client_id=tray.client_id,
                completed_commands=completed_commands,
                failed_commands=failed_commands,
            ))
            print("Finish marking failed order {} by Tray {} for KDS".format(tray.order_id, tray_no)) 

        self.databaser.with_read_transaction(_fail_tray, (tray_no, tasks, ))

    def disable_machines(self, tasks: list[int]):
        def _disable_machines(cursor):
            stations = self.databaser.get_all_stations(cursor)
            machines = self.databaser.get_all_machines(cursor)

            station_machines = defaultdict(list[Machine])
            for machine in machines:
                station_machines[machine.station_id].append(machine)

            self.databaser.delete_all_disabled_machines(cursor)

            task_idx = 0
            for station in stations:
                if station.station_has_multi_machine:
                    for machine in station_machines[station.station_id]:
                        if tasks[task_idx]:
                            self.databaser.insert_disabled_machine(cursor, machine.machine_id)
                        task_idx += 1
                else:
                    disabled_flags = "{:04b}".format(tasks[task_idx])
                    for machine_idx, machine in enumerate(station_machines[station.station_id]):
                        if int(disabled_flags[machine_idx]):
                            self.databaser.insert_disabled_machine(cursor, machine.machine_id)
                    task_idx += 1

        self.databaser.with_write_transaction(_disable_machines)
