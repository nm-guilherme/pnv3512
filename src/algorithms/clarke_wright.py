import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))

import logging
import numpy as np
import pandas as pd
from src.helpers import file_manager as fm
from src.helpers import geometric_calculations as gc
from src.helpers.graphic_generator import plot_routes


FORMAT = '%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)

def get_route_demand(route, clients):
    return sum(clients.loc[client_no, "DEMAND"] for client_no in route)

def calculate_economies(distances: pd.DataFrame):
    economies = []
    for client_i in distances.index.values[1:]:
        for client_j in distances.columns.values[1:]:
            tuple_clients = (min(client_i, client_j), max(client_i, client_j))
            if not client_i==client_j:
                economy = distances.loc[0, tuple_clients[0]]+distances.loc[0, tuple_clients[1]]-distances.loc[tuple_clients[0], tuple_clients[1]]
                economies.append([int(client_i), int(client_j) ,economy])   
    economies = pd.DataFrame(economies, columns=["c_i", "c_j", "s_ij"]).sort_values(by="s_ij", ascending=False)
    economies = economies.astype({"c_i": int, "c_j": int})
    return economies

def remove_route(new_client, old_client, economies):
    economies = economies[economies['c_i']!=old_client]
    economies = economies[economies['c_j']!=new_client]
    return economies

def get_initial_route(max_capacity, economies):
    initial_economies = economies.copy()
    initial_economies["route_demand"] = initial_economies.apply(lambda row: clients.loc[row["c_i"], "DEMAND"]+clients.loc[row["c_j"], "DEMAND"], axis=1)
    demand_restriction = initial_economies["route_demand"]<=max_capacity
    highest_economy_route = economies[demand_restriction]['s_ij'].idxmax() #captando rota de maior economia 
    highest_economy_clients = economies.loc[highest_economy_route][['c_i', 'c_j']].to_list() 
    route = highest_economy_clients
    route_demand = clients.loc[route[0], "DEMAND"]+clients.loc[route[1], "DEMAND"] #atualizando demanda ocupada da rota
    economies = economies[~economies['c_j'].isin(route)]
    del initial_economies
    return route, route_demand, economies

def get_end_start_restrictions(economies, route, route_demand, max_capacity):
    start_restriction = economies["c_i"]==route[0] #restrição de estar ligado ao cliente inicial da rota
    end_restriction =  economies["c_i"]==route[-1] #restrição de estar ligado ao cliente final da rota
    start_restriction.update(economies[start_restriction]["c_j"].isin(clients[clients["DEMAND"]+route_demand<=max_capacity].index.values))
    end_restriction.update(economies[end_restriction]["c_j"].isin(clients[clients["DEMAND"]+route_demand<=max_capacity].index.values))
    return start_restriction, end_restriction

def insert_client_in_route(start_client, end_client, route):
    existing_client, new_client = (start_client, end_client) if start_client in route else (end_client, start_client)
    if route.index(existing_client)+1==len(route):
        route.append(new_client) #adicionado ao fim da rota
    else:
        route.insert(0, new_client) #adicionado ao início da rota
    return new_client, existing_client

def update_allocated_clients(route, clients_not_in_route, clients_in_route, economies):
    clients_not_in_route = list(filter(lambda x: x not in route, clients_not_in_route)) #removendo clientes da lista de clientes a alocar
    clients_in_route += route
        
    already_allocated_clients = (economies["c_i"].isin(clients_in_route) | economies["c_j"].isin(clients_in_route)) #removendo clientes alocados da lista de economias
    economies.drop(index=economies[already_allocated_clients].index, inplace=True) #removendo clientes alocados da lista de economias
    return clients_not_in_route, clients_in_route

def clarke_wright(max_capacity, clients):
    output_dir = fm.make_new_folder("Clarke_Wright")
    logging.info("Inicializando Algoritmo Clarke & Wright")
    distances = gc.calculate_nodes_distances(clients)
    distances_dict = distances.to_dict()
    logging.info("Matriz de distâncias calculadas")
    economies = calculate_economies(distances)
    logging.info("Economias calculadas")
    routes = []
    clients_not_in_route, clients_in_route = clients.index.values[1:], []
    solution_value, route = 0, []
    while len(clients_not_in_route)>0:  
        logging.info(f"Restam {len(clients_not_in_route)} para serem alocados")
        if economies.empty or len(clients_not_in_route)==1:
            route = clients_not_in_route
            routes.append(route)
            clients_not_in_route = list(filter(lambda x: x not in route, clients_not_in_route))
            break
        route, route_demand, economies = get_initial_route(max_capacity, economies)
        no_viable_options = True
        while route_demand<max_capacity or no_viable_options:
            start_restriction, end_restriction = get_end_start_restrictions(economies, route, route_demand, max_capacity)
            viable_routes  = start_restriction | end_restriction
            if economies[viable_routes].shape[0]==0: 
                no_viable_options = False
                break
            highest_economy_route = economies[viable_routes]['s_ij'].idxmax() 
            start_client, end_client = economies.loc[highest_economy_route][['c_i', 'c_j']].values 
            new_client, existing_client = insert_client_in_route(start_client, end_client, route)
            route_demand+=clients.loc[new_client, "DEMAND"] 
            economies = remove_route(new_client, existing_client, economies)
        clients_not_in_route, clients_in_route = update_allocated_clients(route, clients_not_in_route, clients_in_route, economies)
        
        route = [int(x) for x in route]
        route.insert(0, 0) #depósito no início
        route.append(0) #depósito no fim
        solution_value+= gc.calculate_route_distance(route, distances_dict)
        routes.append(route)
        fm.write_output(output_dir+"/results.csv", route)
    logging.info(f"Valor da função objetivo: {solution_value} km")
    fm.write_output(output_dir+"/results.csv", [f"Solution Value: {solution_value}"])
    plot_routes(routes, clients, output_dir)
    return routes

if __name__=='__main__':
    clients = fm.read_inputs("R105.txt")
    MAX_CAPACITY = 200
    routes = clarke_wright(MAX_CAPACITY, clients)