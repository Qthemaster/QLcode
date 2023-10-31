# -*- coding: utf-8 -*-
"""
Created on Fri Oct 27 17:56:56 2023

@author: Qian
"""
import tables
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def get_h5_info(file_path):
    with tables.open_file(file_path, 'r') as file:
        print("Datasets in the file:")
        for node in file:
            if isinstance(node, tables.array.Array):
                print(f" - {node.name}, dimensions: {node.shape}")

def create_animation(file_path, dataset_name, output_path, output_filename):
    with tables.open_file(file_path, 'r') as file:
        data = file.get_node(f'/{dataset_name}')[:]
    
    fig, ax = plt.subplots()
    im = ax.imshow(data[0, :, :], animated=True)
    
    def update(frame):
        im.set_array(data[frame, :, :])
        return im,
    
    ani = FuncAnimation(fig, update, frames=len(data), blit=True)
    ani.save(f'{output_path}/{output_filename}.gif', writer='imagemagick')
    plt.show()

if __name__ == "__main__":
    file_path = input("Enter the path to the HDF5 file: ")
    get_h5_info(file_path)
    dataset_name = input("Enter the name of the dataset to animate: ")
    
    # 提供默认的输出路径和文件名
    default_output_path = 'D:\Research\data\simulation\video'
    default_output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = input(f"Enter the output path (default: {default_output_path}): ") or default_output_path
    output_filename = input(f"Enter the output filename (default: {default_output_filename}): ") or default_output_filename
    
    create_animation(file_path, dataset_name, output_path, output_filename)