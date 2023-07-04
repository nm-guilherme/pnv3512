import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))

import logging
import numpy as np
import pandas as pd
from collections import OrderedDict
from src.helpers import file_manager as fm
from src.helpers import geometric_calculations as gc
from src.helpers.graphic_generator import plot_routes


FORMAT = '%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def get_route_demand(route, demands):
    return sum(demands[client_no] for client_no in route)

def calculate_economies(distances: dict):
    economies = {}
    for client_i in distances.keys():
        for client_j in distances[client_i].keys():
            if not client_i==client_j:
                economies[(client_i, client_j)]={}
                d0i = distances[0][client_i]
                d0j = distances[0][client_j]
                dij = distances[client_i][client_j]
                economies[(client_i, client_j)]['d0i'] = d0i
                economies[(client_i, client_j)]['d0j'] = d0j
                economies[(client_i, client_j)]['dij'] = dij
                economies[(client_i, client_j)]['s_ij'] = economies[(client_i, client_j)]['d0i']+economies[(client_i, client_j)]['d0j']-economies[(client_i, client_j)]['dij']
    economies = OrderedDict(sorted(economies.items(), key=lambda x: x[1]['s_ij'], reverse=True))
    return economies

def get_initial_route(max_capacity, economies, demands):
    initial_route_selected = False
    i=0
    arcs = list(economies.keys())
    while not initial_route_selected:
        candidate_arc = arcs[i]
        if demands[candidate_arc[0]]+demands[candidate_arc[0]]<=max_capacity:
            route = list(candidate_arc)
            del economies[candidate_arc]
            return route, get_route_demand(route, demands)
        else:
            i+=1

def clarke_wright(max_capacity, clients):
    output_dir = fm.make_new_folder("Clarke_Wright")
    logging.info("Inicializando Algoritmo Clarke & Wright")
    distances = gc.calculate_nodes_distances(clients)
    distances_dict = distances.to_dict()
    logging.info("Matriz de distâncias calculadas")
    economies = calculate_economies(distances_dict)
    logging.info("Economias calculadas")
    demands = pd.Series(clients['DEMAND'].values,index = clients.index).to_dict()
    routes = []
    clients_not_in_route, clients_in_route = clients.index.values[1:], []
    solution_value, route = 0, []
    while len(clients_not_in_route)>0:  
        if not economies or len(clients_not_in_route)==1:
            route = clients_not_in_route
            routes.append(route)
            break
        route, route_demand = get_initial_route(max_capacity, economies, demands)
        clients_in_route.extend(route)
        while route_demand<max_capacity:
            arcs = [arc for arc in economies.keys() if \
                    (arc[0] == route[-1] and arc[1] not in clients_in_route and demands[arc[1]]+route_demand <= max_capacity)
                    or (arc[1]== route[0] and arc[0] not in clients_in_route and demands[arc[0]]+route_demand <= max_capacity)]
            if not arcs:
                break
            arc = arcs[0]
            if arc[0]==route[-1]:
                route+=[arc[1]]
                clients_in_route+=[arc[1]]
                route_demand+=demands[arc[1]]
            elif  arc[1] == route[0]:
                route.insert(0,arc[0])
                clients_in_route+=[arc[0]]
                route_demand+=demands[arc[0]]
        route.insert(0, 0)
        route.append(0)
        solution_value+= gc.calculate_route_distance(route, distances_dict)
        for tup in list(economies.keys()):
            if tup[0] in clients_in_route or tup[1] in clients_in_route:
                del economies[tup]
        routes.append(route)
    logging.info(f"Valor da função objetivo: {solution_value} km")
    fm.write_output(output_dir+"/results.csv", [f"Solution Value: {solution_value}"])
    for s in routes:
        fm.write_output(output_dir+"/results.csv", s)
    plot_routes(routes, clients, output_dir)
    return routes

if __name__=='__main__':
    clients = fm.read_inputs("R105.txt")
    MAX_CAPACITY = 200
    routes = clarke_wright(MAX_CAPACITY, clients)