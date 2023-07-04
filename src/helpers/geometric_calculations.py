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


def calculate_route_distance(permutated_route: list, distances: pd.DataFrame):
    distance = 0
    for client_idx in range(len(permutated_route)-1):
        client_A, client_B = permutated_route[client_idx], permutated_route[client_idx+1]
        distance += distances.loc[client_A, client_B]
    return distance

def calculate_vectors(clients, c1, c2):
    x1, y1 = clients.loc[c1][["XCOORD", "YCOORD"]].values
    x2, y2= clients.loc[c2][["XCOORD", "YCOORD"]].values
    
    direction = np.array([x2 - x1, y2 - y1])
    norm_direction = direction / np.linalg.norm(direction)
    return norm_direction

def calculate_distance(vector, norm_direction, c, clients):
        x, y = clients.loc[c][["XCOORD", "YCOORD"]].values
        x1, y1 = clients.loc[vector[0]][["XCOORD", "YCOORD"]].values
        point_vector = np.array([x - x1, y - y1])
        projection = np.dot(point_vector, norm_direction)
        distance = np.linalg.norm(point_vector - projection * norm_direction)
        return distance if distance>10e-15 else 0
    
def get_vectors_matrix(clients: pd.DataFrame):
    vectors = {}
    for idx, comb in enumerate(combinations(clients.index.values,2)):
        vectors[str(comb)] = {}
        norm_direction = calculate_vectors(clients, comb[0], comb[1])
        for c in clients.index.values:
            vectors[str(comb)][c] = calculate_distance(comb, norm_direction, c, clients)
    return pd.DataFrame.from_dict(vectors, orient='index').stack().sort_values(ascending=False)

def calculate_nodes_distances(clients:pd.DataFrame):
    distances = np.zeros((len(clients.index.values), len(clients.index.values)))
    for comb in combinations(clients.index.values,2):
        distances[comb[0], comb[1]]= calculate_points_distance(comb[0], comb[1], clients)
    return pd.DataFrame(distances+distances.T)


def get_stacked_distances(distances):
    stacked_distances = distances.stack().to_frame().reset_index()
    stacked_distances.columns = ['c_i', 'c_j', 'dist']
    stacked_distances.sort_values(by='dist', inplace=True)
    return stacked_distances

if __name__=="__main__":
    base_dir = "./R105.txt"
    clients = fm.read_inputs(base_dir)
    get_vectors_matrix(clients)