import os
import sys
import numpy as np
import pandas as pd
import src.helpers.file_manager as fm
from itertools import combinations, permutations
sys.path.append(os.path.abspath(os.path.join(os.path.dirname( __file__ ), '../..')))


def calculate_points_distance(clientA: int, clientB:int , clients: pd.DataFrame):
        client_A_coords = clients.loc[clientA][["XCOORD", "YCOORD"]].values
        client_B_coords= clients.loc[clientB][["XCOORD", "YCOORD"]].values
        distance = np.linalg.norm(client_A_coords - client_B_coords)
        return distance

def calculate_route_distance(permutated_route: list, distances_dict: dict):
    distance = 0
    for client_idx in range(len(permutated_route)-1):
        client_A, client_B = permutated_route[client_idx], permutated_route[client_idx+1]
        distance += distances_dict[client_A][client_B]
    return distance

def calculate_nodes_distances(clients:pd.DataFrame):
    distances = np.zeros((len(clients.index.values), len(clients.index.values)))
    for comb in combinations(clients.index.values,2):
        distances[comb[0], comb[1]]= calculate_points_distance(comb[0], comb[1], clients)
    return pd.DataFrame(distances+distances.T)

def get_stacked_distances(distances: pd.DataFrame):
    stacked_distances = distances.stack().to_frame().reset_index()
    stacked_distances.columns = ['c_i', 'c_j', 'dist']
    stacked_distances.sort_values(by='dist', inplace=True)
    return stacked_distances