import os
import csv
import time
from pandas import read_csv

def read_inputs(path):
    df = read_csv(path,
            skiprows=8, 
            delim_whitespace=True, 
            names=["CUST NO","XCOORD","YCOORD","DEMAND","READY_TIME","DUE_DATE","SERVICE_TIME"],
            index_col="CUST NO")
    return df

def write_output(csv_path, new_line):
        with open(csv_path, "a", newline='', encoding="utf-8") as output_status:
                wr = csv.writer(output_status, csv.QUOTE_ALL)
                wr.writerow(new_line)

def write_list_in_csv(csv_path, list_of_lists):
        with open(csv_path, 'w', newline='') as csvfile:
                wr = csv.writer(csvfile, csv.QUOTE_ALL)
                for row in list_of_lists:
                        wr.writerow(row)

def make_new_folder(algorithm):
    current_cwd = os.getcwd()
    current_time = time.strftime("%Y%m%d-%H%M%S")
    new_dir = os.path.join(current_cwd, "outputs", algorithm, current_time)
    os.makedirs(new_dir, exist_ok=True)
    return new_dir
