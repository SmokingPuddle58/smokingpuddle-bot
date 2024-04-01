import sqlite3
from itertools import chain
import json
import urllib.request

connection = sqlite3.connect("database.db")

cursor = connection.cursor()


def get_json(url: str) -> dict:
    a = urllib.request.urlopen(url)
    return json.loads(str(a.read(), 'utf-8'))


def init_database():
    try:
        cursor.execute("""
             CREATE TABLE ROUTE_LIST (
             ROUTE TEXT,
             BOUND TEXT,
             SERV_TYPE TEXT,
             ORIG_EN TEXT,
             ORIG_TR TEXT,
             ORIG_SI TEXT,
             DEST_EN TEXT,
             DEST_TR TEXT,
             DEST_SI TEXT,
             UNIQUE (ROUTE, BOUND, SERV_TYPE, ORIG_EN, DEST_EN) ON CONFLICT REPLACE 
         )""")

        cursor.execute("""
             CREATE TABLE STOP_LIST (
             STOP_ID TEXT,
             NAME_EN TEXT,
             NAME_TR TEXT,
             NAME_SI TEXT,
             LAT REAL,
             LONG REAL,
             UNIQUE (STOP_ID) ON CONFLICT REPLACE 
         )""")

        cursor.execute("""
             CREATE TABLE ROUTE_STOP (
             ROUTE TEXT,
             BOUND TEXT,
             SERV_TYPE INT,
             SEQ INT,
             STOP_ID TEXT,
             UNIQUE (ROUTE, BOUND, SERV_TYPE, SEQ, STOP_ID) ON CONFLICT IGNORE 
         )""")

        print("ALL CREATED")

        connection.commit()

    except sqlite3.OperationalError:
        pass


def init_route_list():
    route_list = [get_json("https://data.etabus.gov.hk/v1/transport/kmb/route/")['data'],get_json("https://rt.data.gov.hk/v2/transport/citybus/route/ctb")['data']]

    for datum in route_list:

        route_list_tuple = [tuple(d.values()) for d in datum]

    cursor.executemany(f"""
        INSERT INTO ROUTE_LIST VALUES ({KMB, CTB},?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, route_list_tuple)

    connection.commit()


def init_bus_stop():
    stop_list = get_json("https://data.etabus.gov.hk/v1/transport/kmb/stop")['data']

    stop_list_tuple = [tuple(d.values()) for d in stop_list]

    cursor.executemany("""
        INSERT INTO STOP_LIST VALUES (?, ?, ?, ?, ?, ?)
    """, stop_list_tuple)

    connection.commit()


def init_route_stop():
    route_stop_list = get_json("https://data.etabus.gov.hk//v1/transport/kmb/route-stop")['data']

    stop_list_tuple = [tuple(d.values()) for d in route_stop_list]

    cursor.executemany("""
        INSERT INTO ROUTE_STOP VALUES (?, ?, ?, ?, ?)
    """, stop_list_tuple)

    connection.commit()


def get_route_info(route) -> list:
    route = cursor.execute("""
        SELECT * FROM ROUTE_LIST WHERE ROUTE = ?
    """, (route,)).fetchall()
    return route


def get_stop_info(route: str, start: str, end: str, serv_type: str) -> list:
    bound = cursor.execute("""
        SELECT BOUND FROM ROUTE_LIST WHERE ROUTE = ? AND ORIG_TR = ? AND DEST_TR = ? AND SERV_TYPE = ?
    """, (route, start, end, serv_type)).fetchone()[0]

    station_list = cursor.execute("""
        SELECT STOP_ID FROM ROUTE_STOP WHERE ROUTE = ? AND BOUND = ? AND SERV_TYPE = ?
    """, (route, bound, serv_type))

    return list(chain.from_iterable(station_list))

def get_route_list() -> list:
    route = cursor.execute("""
        SELECT ROUTE FROM ROUTE_LIST
    """).fetchall()

    return list(chain.from_iterable(route))


def convert_id_to_name(id_: str) -> str:
    name = cursor.execute("""
        SELECT NAME_TR FROM STOP_LIST WHERE STOP_ID = ?
    """, (id_,)).fetchone()

    return name[0]


def get_direction(route: str) -> list:
    return cursor.execute("""
            SELECT ORIG_TR, DEST_TR FROM ROUTE_LIST WHERE ROUTE = ?
        """, (route,)).fetchall()


def get_serv_type(route: str, start: str, end: str):
    list_of_serv = cursor.execute("""
        SELECT SERV_TYPE FROM ROUTE_LIST WHERE ROUTE=? AND ORIG_TR=? AND DEST_TR=?
    """, (route, start, end,)).fetchall()

    print(list_of_serv)

    return list(chain.from_iterable(list_of_serv))


def get_bound(route, start, end, serv_type):
    bound = cursor.execute("""
        SELECT BOUND FROM ROUTE_LIST WHERE ROUTE = ? AND ORIG_TR = ? AND DEST_TR = ? AND SERV_TYPE = ?
    """, (route, start, end, serv_type)).fetchone()[0]

    return bound
