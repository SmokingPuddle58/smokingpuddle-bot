from os import system

system("rm database.db")

from database import init_database, init_route_list, init_bus_stop, init_route_stop

init_database()

init_route_list()

init_bus_stop()

init_route_stop()
