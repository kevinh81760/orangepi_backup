from sqlite3 import Error, connect, Cursor
from pathlib import Path
from .entity import Station, Machine, DisabledMachine, Tray, TrayMachine
from contextlib import closing

class Database:
    def __init__(self, sqlite_file: Path):
        self.sqlite_file = sqlite_file

    def create_connection(self, isolation_level: str):
        conn = None
        try:
            conn = connect(self.sqlite_file, isolation_level=isolation_level)
        except Error as e:
            print("Database Error: {}".format(e))

        return conn

    def with_transaction(self, isolation_level: str, fn, args = None):
        result = None
        with closing(self.create_connection(isolation_level)) as conn:
            with conn:
                with closing(conn.cursor()) as cursor:
                    if args is None:
                        result = fn(cursor)
                    else:
                        result = fn(cursor, *args)
        return result

    def with_write_transaction(self, fn, args = None):
        return self.with_transaction("IMMEDIATE", fn, args)

    def with_read_transaction(self, fn, args = None):
        return self.with_transaction("DEFERRED", fn, args)




    def get_all_stations(self, cursor: Cursor) -> list[Station]:
        rs = cursor.execute("""
            SELECT
                station_id,
                station_arrange,
                station_name,
                station_min_level,
                station_max_level,
                station_prefix,
                station_suffix,
                station_has_multi_machine
            FROM station
            ORDER BY
                station_arrange; """ ,
        )
        stations = []
        for row in rs.fetchall():
            stations.append(Station(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7] == 1))
        return stations




    def get_all_machines(self, cursor: Cursor) -> list[Machine]:
        rs = cursor.execute("""
            SELECT
                machine_id,
                machine_arrange,
                machine_name,
                station_id
            FROM machine
            ORDER BY
                station_id,
                machine_arrange; """ ,
        )
        machines = []
        for row in rs.fetchall():
            machines.append(Machine(row[0], row[1], row[2], row[3]))
        return machines




    def insert_disabled_machine(self, cursor: Cursor, machine_id: int):
        cursor.execute("""
            INSERT INTO disabled_machine (
                machine_id
            )
            VALUES (?); """ ,
            (machine_id, ),
        )

    def delete_all_disabled_machines(self, cursor: Cursor):
        cursor.execute("""
            DELETE FROM disabled_machine; """ ,
        )

    def get_all_disabled_machines(self, cursor: Cursor) -> list[DisabledMachine]:
        rs = cursor.execute("""
            SELECT
                machine_id
            FROM disabled_machine; """ ,
        )
        disabled_machines = []
        for row in rs.fetchall():
            disabled_machines.append(DisabledMachine(row[0]))
        return disabled_machines
    



    def insert_tray(self, cursor: Cursor, tray_no: int, order_id: int, client_id: int):
        cursor.execute("""
            INSERT INTO tray (
                tray_no,
                order_id,
                client_id
            )
            VALUES (?, ?, ?)
            ON CONFLICT (tray_no)
            DO UPDATE SET
                order_id = excluded.order_id,
                client_id = excluded.client_id; """ ,
            (tray_no, order_id, client_id, ),
        )

    def delete_tray(self, cursor: Cursor, tray_no: int):
        cursor.execute("""
            DELETE FROM tray
            WHERE
                tray_no = ?; """ ,
            (tray_no, ),
        )
    
    def get_tray(self, cursor: Cursor, tray_no: int):
        rs = cursor.execute("""
            SELECT
                tray_no,
                order_id,
                client_id
            FROM tray
            WHERE
                tray_no = ?; """ ,
            (tray_no, ),
        )
        row = rs.fetchone()
        if row is None:
            return None
        return Tray(row[0], row[1], row[2])
    



    def insert_tray_machine(self, cursor: Cursor, tray_no: int, machine_id: int, command_id: int, tray_machine_level: int):
        cursor.execute("""
            INSERT INTO tray_machine (
                tray_no,
                machine_id,
                command_id,
                tray_machine_level
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT (tray_no, machine_id)
            DO UPDATE SET
                tray_machine_level = excluded.tray_machine_level; """ ,
            (tray_no, machine_id, command_id, tray_machine_level, ),
        )

    def delete_tray_machines_by_tray(self, cursor: Cursor, tray_no: int):
        cursor.execute("""
            DELETE FROM tray_machine
            WHERE
                tray_no = ?; """ ,
            (tray_no, ),
        )

    def get_tray_machines_by_tray(self, cursor: Cursor, tray_no: int) -> list[TrayMachine]:
        rs = cursor.execute("""
            SELECT
                tray_no,
                machine_id,
                command_id,
                tray_machine_level
            FROM tray_machine
            WHERE
                tray_no = ?; """ ,
            (tray_no, ),
        )
        tray_machines = []
        for row in rs.fetchall():
            tray_machines.append(TrayMachine(row[0], row[1], row[2], row[3]))
        return tray_machines
