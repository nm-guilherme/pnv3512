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

def get_p_closest_clients(route, route_demand, max_capacity, distances, stacked_distances, allocated_clients):
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
            if len(closest_clients)==5:
                break
    return closest_clients    

def get_number_of_vehicles(clients, max_capacity):
    all_demand = clients["DEMAND"].sum()
    vehicles_needed = math.ceil((all_demand/max_capacity))
    logging.info(f"São necessários {vehicles_needed} veículos com {max_capacity} de capacidade para atender a demanda de {all_demand}")
    return vehicles_needed

def get_best_insert_position(route, new_client, distances_dict):
    lowest_cost = np.inf
    for i in range(len(route)):
        if i!=0:
            client_before, client_after= route[i-1], route[i]
            before_new = distances_dict[client_before][new_client]
            new_after = distances_dict[client_after][new_client]
            before_after = distances_dict[client_before][client_after]
            cost_of_insertion = before_new+new_after-before_after
            if cost_of_insertion<lowest_cost:
                lowest_cost = cost_of_insertion
                insert_position = i
    return insert_position, lowest_cost

def get_route_demand(route, demands):
    return sum(demands[client_no] for client_no in route)

def find_solution(initial_routes, count_restarts, max_capacity, vehicles_needed, chosen_clients, stacked_distances, distances, distances_dict, demands):
    allocated_clients = copy.deepcopy(chosen_clients)
    solution_value = 0
    solution_routes = []
    exists_viableRoutes = vehicles_needed
    routes_demands = {str(route): get_route_demand(route, demands) for route in initial_routes}
    solution_value = sum([gc.calculate_route_distance(r, distances_dict) for r in initial_routes])
    while exists_viableRoutes>0:
        for route in initial_routes:
            key = str(route)
            closest_clients = get_p_closest_clients(route, routes_demands[str(route)], max_capacity, distances, 
                                                    stacked_distances, allocated_clients)
            if len(closest_clients)==0:
                solution_routes.append(route[:])
                initial_routes.remove(route)
                exists_viableRoutes-=1
                continue
            idx_sort = len(closest_clients)
            _, new_client = closest_clients[random_int(idx_sort, count_restarts)]
            allocated_clients.append(new_client)
            routes_demands[str(route)] += demands[new_client]
            insert_position, cost = get_best_insert_position(route, new_client, distances_dict)
            route.insert(insert_position, new_client)
            routes_demands[str(route)] = routes_demands.pop(key)
            solution_value += cost
    if len(allocated_clients)!=len(distances_dict.keys()):
        vehicles_needed+=1
        initial_routes, chosen_clients = choose_clients(vehicles_needed, distances)
        return find_solution(initial_routes, count_restarts, max_capacity, vehicles_needed, chosen_clients, stacked_distances, distances, distances_dict, demands)
    return solution_routes, solution_value

def multi_start_heuristics(clients, max_capacity, n_restarts):
    output_dir = fm.make_new_folder("MultiStarts")
    logging.info("Inicializando Heurística Construtiva Probabilística de Múltiplos Recomeços")
    s = time.time()
    distances = gc.calculate_nodes_distances(clients)
    distances_dict = distances.to_dict()
    demands = pd.Series(clients['DEMAND'].values,index = clients.index).to_dict()
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
        feasible_solution, solution_value = find_solution(_initial_routes, count_restarts, 
                                                          max_capacity, vehicles_needed, chosen_clients,
                                                          stacked_distances, distances, distances_dict, demands)
        records.append(solution_value)
        if solution_value<best_solution_value:
            best_solution, best_solution_value = feasible_solution, solution_value


    logging.info(f"Melhor resultado obtido: {best_solution_value} km")      
    e = time.time()
    logging.info(f"Tempo de processamento (s): {e-s}")
    fm.write_output(output_dir+"/results.csv", [f"Solution Value: {best_solution_value}"])
    for s in best_solution:
        fm.write_output(output_dir+"/results.csv", s)
    pd.DataFrame(data= records, columns=["solution_value"]).to_excel(output_dir+"/ObjectiveFunctionValues.xlsx")
    plot_routes(best_solution, clients, output_dir)

if __name__=="__main__":     
    base_dir = "./R105.txt"
    clients = fm.read_inputs(base_dir)
    multi_start_heuristics(clients, 200, 1000)
       