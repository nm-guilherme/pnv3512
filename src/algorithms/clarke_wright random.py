import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))

import copy
import random
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
    return economies

def update_economies(economies, lower, upper):
    m = random.uniform(lower, upper)
    for arc in economies.keys():
        economies[arc]['s_ij'] = economies[arc]['d0i']+economies[arc]['d0j']-m*economies[arc]['dij']
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

def clarke_wright(clients, economies, demands, max_capacity, distances_dict):
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
        viable_options = True
        while route_demand<max_capacity and viable_options:
            viable_options = False
            for arc in economies.keys():
                add_to_right = (arc[0] == route[-1] and arc[1] not in clients_in_route and demands[arc[1]]+route_demand <= max_capacity)
                add_to_left = (arc[1]== route[0] and arc[0] not in clients_in_route and demands[arc[0]]+route_demand <= max_capacity)
                if add_to_right:
                    route+=[arc[1]]
                    clients_in_route+=[arc[1]]
                    route_demand+=demands[arc[1]]
                    viable_options = True
                elif add_to_left:
                    route.insert(0,arc[0])
                    clients_in_route+=[arc[0]]
                    route_demand+=demands[arc[0]]
                    viable_options = True
                    # del economies[arc]
                if route_demand>=200:
                    break
        route.insert(0, 0) #depósito no início
        route.append(0) #depósito no fim
        solution_value+= gc.calculate_route_distance(route, distances_dict)
        for tup in list(economies.keys()):
            if tup[0] in clients_in_route or tup[1] in clients_in_route:
                del economies[tup]
        routes.append(route)
    return routes, solution_value

def randomic_clarke_wright(clients, max_capacity, n_restarts, lower, upper):
    output_dir = fm.make_new_folder("RandomicCWS")
    logging.info("Inicializando Clarke Wright randômico.")
    distances = gc.calculate_nodes_distances(clients)
    logging.info("Matriz de distâncias calculadas")
    distances_dict = distances.to_dict()
    logging.info("Matriz de economias calculadas")
    economies = calculate_economies(distances_dict)
    demands = pd.Series(clients['DEMAND'].values,index = clients.index).to_dict()
    count_restarts=0
    best_solution, best_solution_value = [], np.inf
    records = []
    while count_restarts<n_restarts:
        count_restarts+=1
        logging.info(f"Recomeços: {count_restarts} - {count_restarts/n_restarts*100:.0f}%")
        economies = update_economies(economies, lower, upper)
        feasible_solution, solution_value = clarke_wright(clients, copy.deepcopy(economies), demands, max_capacity, distances_dict)
        records.append(solution_value)
        if solution_value<best_solution_value:
            best_solution, best_solution_value = feasible_solution, solution_value

    logging.info(f"Melhor resultado obtido: {best_solution_value} km")      
    fm.write_output(output_dir+"/results.csv", [f"Solution Value: {best_solution_value}"])
    for s in best_solution:
        fm.write_output(output_dir+"/results.csv", s)
    pd.DataFrame(data= records, columns=["solution_value"]).to_excel(output_dir+"/ObjectiveFunctionValues.xlsx")
    plot_routes(best_solution, clients, output_dir)

if __name__=='__main__':
    clients = fm.read_inputs("R105.txt")
    MAX_CAPACITY = 200
    randomic_clarke_wright(clients, MAX_CAPACITY, 200, 0.5, 1.5)

