import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))

import math
import time
import copy
import random
import logging
import numpy as np
import pandas as pd
import src.helpers.file_manager as fm
import src.helpers.geometric_calculations as gc
from src.helpers.graphic_generator import plot_routes

FORMAT = '%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def choose_clients(m, distances):
    chosen_clients = [0]
    for n_clients in range(m):
        most_distant_client = distances.drop(columns=chosen_clients)[distances.index.isin(chosen_clients)].sum().idxmax()
        chosen_clients.append(most_distant_client)
    return [[0,x,0] for x in chosen_clients if x!=0], chosen_clients

def random_int(p, i):
    seed_value = time.time()*1000+i
    random.seed(seed_value)
    random_number = random.randint(0, p-1)
    return random_number   

# @profile
def get_p_closest_clients(p, route, route_demand, max_capacity, distances, stacked_distances, allocated_clients):
    not_allocated = list(filter(lambda x: x not in allocated_clients, distances.columns.values))
    demand_restriction = clients[clients["DEMAND"]+route_demand<=max_capacity].index
    viable_clients = list(set(demand_restriction) & set(not_allocated))
    viable_clients = (stacked_distances['c_j'].isin(viable_clients)) &\
                     (stacked_distances['c_i'].isin(route[1:-1]))
    closest_clients, _ = [], []
    for idx, row in stacked_distances[viable_clients].iterrows():
        if not row['c_j'] in _:
            closest_clients.append((row['c_i'], row['c_j']))
            _.append(row['c_j'])
            if len(closest_clients)==p:
                break
    return closest_clients    

def get_number_of_vehicles(clients, max_capacity):
    all_demand = clients["DEMAND"].sum()
    vehicles_needed = math.ceil((all_demand/max_capacity))
    logging.info(f"São necessários {vehicles_needed} veículos com {max_capacity} de capacidade para atender a demanda de {all_demand}")
    return vehicles_needed

def get_best_insert_position(route, new_client, actual_client, distances):
    lowest_cost = np.inf
    for i in range(len(route)):
        if i!=0:
            client_before, client_after= route[i-1], route[i]
            before_new = distances.loc[client_before, new_client]
            new_after = distances.loc[client_after, new_client]
            before_after = distances.loc[client_before, client_after]
            cost_of_insertion = before_new+new_after-before_after
            if cost_of_insertion<lowest_cost:
                lowest_cost = cost_of_insertion
                insert_position = i
    return insert_position, lowest_cost

def get_route_demand(route):
    return sum(clients.loc[client_no, "DEMAND"] for client_no in route)

# @profile
def find_solution(initial_routes, p_closest, count_restarts, max_capacity, 
                  vehicles_needed, chosen_clients,
                  stacked_distances, distances):
    allocated_clients = copy.deepcopy(chosen_clients)
    solution_value = 0
    for route in initial_routes:
        route_demand = get_route_demand(route)
        solution_value+= gc.calculate_route_distance(route, distances)
        while route_demand<=max_capacity:

            closest_clients = get_p_closest_clients(p_closest, route, route_demand, max_capacity, distances, 
                                                    stacked_distances, allocated_clients)
            if len(closest_clients)==0:
                break
            idx_sort = p_closest if len(closest_clients)>p_closest else len(closest_clients)
            old_client, new_client = closest_clients[random_int(idx_sort, count_restarts)]
            allocated_clients.append(new_client)
            route_demand += clients.loc[new_client, "DEMAND"]
            insert_position, cost = get_best_insert_position(route, new_client, old_client, distances)
            route.insert(insert_position, new_client)
            solution_value += cost
    if len(allocated_clients)!=len(distances.columns):
        vehicles_needed+=1
        initial_routes = choose_clients(vehicles_needed, distances)
        find_solution(initial_routes, p_closest, count_restarts, max_capacity, 
                  vehicles_needed, chosen_clients,
                  stacked_distances, distances)
    return initial_routes, solution_value

# @profile
def multi_start_heuristics(clients, max_capacity, n_restarts, p_closest):
    output_dir = fm.make_new_folder("MultiStarts")
    logging.info("Inicializando Heurística Construtiva Probabilística de Múltiplos Recomeços")
    distances = gc.calculate_nodes_distances(clients)
    stacked_distances = gc.get_stacked_distances(distances)
    logging.info("Matriz de distâncias calculadas")
    vehicles_needed = get_number_of_vehicles(clients, max_capacity)
    initial_routes, chosen_clients = choose_clients(vehicles_needed, distances)
    count_restarts=0
    best_solution, best_solution_value = [], np.inf
    records = []

    while count_restarts<n_restarts:
        count_restarts+=1
        logging.info(f"Recomeços: {count_restarts} -- {count_restarts/n_restarts*100:.0f}%")
        _initial_routes = copy.deepcopy(initial_routes)
        feasible_solution, solution_value = find_solution(_initial_routes, p_closest, count_restarts, 
                                                          max_capacity, vehicles_needed, chosen_clients,
                                                          stacked_distances, distances)
        records.append(solution_value)
        if solution_value<best_solution_value:
            best_solution, best_solution_value = feasible_solution, solution_value

    logging.info(f"Melhor resultado obtido: {best_solution_value} km")      
    fm.write_output(output_dir+"/results.csv", [f"Solution Value: {best_solution_value}"])
    for s in best_solution:
        fm.write_output(output_dir+"/results.csv", s)
    pd.DataFrame(data= records, columns=["solution_value"]).to_excel(output_dir+"/ObjectiveFunctionValues.xlsx")
    plot_routes(best_solution, clients, output_dir)

if __name__=="__main__":     
    base_dir = "./R105.txt"
    clients = fm.read_inputs(base_dir)
    multi_start_heuristics(clients, 200, 200, 5)
       