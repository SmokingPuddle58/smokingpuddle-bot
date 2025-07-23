from os import system

from database import init_database, init_route_list, init_bus_stop, init_route_stop

system("rm database.db")

init_database()

init_route_list()

init_bus_stop()

init_route_stop()
