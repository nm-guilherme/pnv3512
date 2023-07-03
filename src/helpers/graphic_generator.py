import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import src.helpers.file_manager as fm
import math

def generate_color_list():
    colormap = plt.cm.get_cmap('tab20')
    num_colors = colormap.N
    color_list = [colormap(i) for i in range(num_colors)]
    return color_list

def plot_routes(routes: list, clients: pd.DataFrame, output_dir:str):
    colors_list = generate_color_list()
    xlim = (0, 100)
    ylim = (0, 100)

    for idx, route in enumerate(routes):
        fig, ax = plt.subplots(figsize=(5, 5))

        routes_coordinates = clients[clients.index.isin(route)].copy()
        routes_coordinates = routes_coordinates.reindex(route)
        ax.plot(routes_coordinates['XCOORD'], routes_coordinates['YCOORD'], '--o', color=colors_list[idx])
        ax.plot([routes_coordinates['XCOORD'].iloc[-1], routes_coordinates['XCOORD'].iloc[0]],
                [routes_coordinates['YCOORD'].iloc[-1], routes_coordinates['YCOORD'].iloc[0]], '--o', color=colors_list[idx])
        for x, y, label in zip(routes_coordinates["XCOORD"], routes_coordinates["YCOORD"], route):
            ax.annotate(label, (x, y), textcoords="offset points", xytext=(0,10), ha='center')
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)  
        fig.suptitle(f"Route_{idx}")
        fig.tight_layout()
        fig.savefig(output_dir+f"/Route_{idx}.png")



if __name__=="__main__":     
    clients = fm.read_inputs(r"C:\Users\gmorae01\OneDrive - Kearney\Documents\Personal\POLI\PNV3512 - Planejamento de Sistemas Logísticos\R105.txt")
    routes = [[0,53,28,27,65,52,18,84,5,60,99,59,92,91,42,97,95,0],
    [0,89,96,87,37,100,38,61,85,98,93,6,58,0],
    [0,46,90,26,12,25,39,67,56,75,41,22,74,72,21,2,0],
    [0,40,68,80,54,55,4,73,57,15,43,14,13,94,64,0],
    [0,17,8,82,48,47,36,62,10,88,31,69,1,78,50,0],
    [0,76,77,3,33,81,51,70,20,66,9,34,29,24,23,0],
    [0,16,83,45,7,49,11,63,32,30,71,35,79,0],
    [0,19,86,44,0]]

    plot_routes(routes, clients)