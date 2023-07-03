import math
import time
import logging
import numpy as np
import pandas as pd
import src.helpers.file_manager as fm
import src.helpers.geometric_calculations as gc
from itertools import combinations, permutations

FORMAT = '%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def calculate_max_clients_in_route(clients: pd.DataFrame, max_capacity: int):
    used_capacity = 0
    max_clients_in_route = 1 #contando depósito
    for idx, row in clients.iterrows():
        if used_capacity+row["DEMAND"]<=max_capacity:
            used_capacity+=row["DEMAND"]
            max_clients_in_route+=1
    return max_clients_in_route

def check_if_route_respects_capacity(route, clients, max_capacity):
    return sum(clients.loc[client_no, "DEMAND"] for client_no in route)<=max_capacity

def is_symmetric_route(evaluated_routes, new_route):
        is_symmetric = False
        for route in evaluated_routes:
            if new_route == route[::-1]:  # Check if sublist is symmetric
                is_symmetric = True
                break

        if not is_symmetric:
            return False
        else:
            return True

def generate_routes_method(clients: pd.DataFrame, max_capacity: int, n_clients: int):
    output_dir = fm.make_new_folder("ExhaustiveRoutes")
    logging.info("Inicializando a geração exaustiva de rotas e permutações")
    routes = []
    start_time = time.time()
    distances = gc.calculate_nodes_distances(clients)
    logging.info("Matriz de distâncias calculadas")
    max_clients = calculate_max_clients_in_route(clients.loc[1:n_clients], max_capacity)
    max_n_combinations = max_clients if max_clients<=n_clients else n_clients
    logging.info(f"Serão avaliadas combinações de até {max_n_combinations} clientes")
    log_records = {}
    for i in range(1, max_n_combinations+1):
        log_records[i]={}
        log_records[i]['total_combinations'] = math.comb(n_clients,i)
        log_records[i]['total_permutations'] = math.perm(i,i)*log_records[i]['total_combinations']
        log_records[i]['combinations_respecting_demand'] = 0
        log_records[i]['permutations_respecting_demand'] = 0
        log_records[i]['permutations_respecting_demand_not_symmetric'] = 0

        logging.info(f"Avaliando {math.comb(n_clients,i)} combinações de {i} clientes")
        for route in combinations(clients.index.values[1:n_clients+1],i):
            if check_if_route_respects_capacity(route, clients, max_capacity):
                log_records[i]['combinations_respecting_demand'] += 1 
                best_route_distance = None
                evaluated_routes = []
                for permutated_route in permutations(route):
                    permutated_route = list(permutated_route)
                    log_records[i]['permutations_respecting_demand'] += 1 
                    if is_symmetric_route(evaluated_routes, permutated_route):
                        continue
                    else:
                        log_records[i]['permutations_respecting_demand_not_symmetric'] += 1     
                        evaluated_routes.append(permutated_route[:])
                        permutated_route.insert(0, 0) #depósito no início
                        permutated_route.append(0) #depósito no fim
                        route_distance = gc.calculate_route_distance(permutated_route, distances)
                        if not best_route_distance or route_distance<best_route_distance:
                            best_route_distance = route_distance
                            best_route = permutated_route
                routes.append(best_route)
                fm.write_output(output_dir+"/results.csv", best_route)

    end_time = time.time()
    execution_time = end_time - start_time
    minutes, seconds = divmod(execution_time, 60)
    time_formatted = "{:02d}m:{:02d}s".format(int(minutes), int(seconds))
    logging.info(f"Tempo de execução: {time_formatted}")
    pd.DataFrame().from_dict(log_dict).to_excel(output_dir+"/log_permutations.xlsx")
    return routes, log_records, execution_time

if __name__=='__main__':
    clients = fm.read_inputs("./R105.txt")
    MAX_CAPACITY=60
    routes, log_dict, execution_time = generate_routes_method(clients, MAX_CAPACITY, 40)
    fm.write_output("times.csv", [40, execution_time])
        