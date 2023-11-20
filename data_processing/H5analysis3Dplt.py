# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:27:22 2023

@author: 86150
"""
import tables
import numpy as np
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

def get_h5_info(file_path):
    """Reads HDF5 file and prints out the datasets within."""
    with tables.open_file(file_path, 'r') as file:
        print("Datasets in the file:")
        for node in file:
            if isinstance(node, tables.array.Array):
                print(f" - {node.name}, dimensions: {node.shape}")

def create_animation(file_path, dataset_name, output_path, output_filename, slice_dim, slice_index, cmap='viridis', bg_cmap='gray', frame_number=None, use_background=True, background_dataset_name=None):
    """Creates an animation from a selected 2D slice of 4D data."""
    with tables.open_file(file_path, 'r') as file:
        # Load only the selected slice from the dataset
        data_node = file.get_node(f'/{dataset_name}')
        if slice_dim == 0:
            data_slice = data_node[slice_index, :, :, :]
        elif slice_dim == 1:
            data_slice = data_node[:, slice_index, :, :]
        elif slice_dim == 2:
            data_slice = data_node[:, :, slice_index, :]

        data = data_slice
        background_data = None
        if use_background and background_dataset_name:
            background_node = file.get_node(f'/{background_dataset_name}')
            if slice_dim == 0:
                background_slice = background_node[slice_index, :, :, :]
            elif slice_dim == 1:
                background_slice = background_node[:, slice_index, :, :]
            elif slice_dim == 2:
                background_slice = background_node[:, :, slice_index, :]
            background_data = background_slice

    fig, ax = plt.subplots()

    if background_data is not None and use_background:
        ax.imshow(background_data[:, :, 0].T, cmap=bg_cmap)

    if frame_number is not None and 0 <= frame_number < data.shape[2]:
        ax.imshow(data[:, :, frame_number].T, cmap=cmap)
    else:
        animation = ax.imshow(data[:, :, 0].T, animated=True, cmap=cmap, alpha=0.9)

        def update(frame):
            animation.set_array(data[:, :, frame].T)
            return animation,

        ani = FuncAnimation(fig, update, frames=data.shape[2], blit=True)
        ani.save(os.path.join(output_path, f'{output_filename}_dim{slice_dim}_idx{slice_index}.gif'), writer='pillow')

    plt.show()

if __name__ == "__main__":
    file_path = input("Enter the path to the HDF5 file: ")
    get_h5_info(file_path)
    dataset_name = input("Enter the name of the dataset to animate: ")
    
    use_background_input = input("Do you want to use a background image? (yes/no): ").strip().lower()
    use_background = (use_background_input == 'yes')
    background_dataset_name = None
    
    if use_background:
       background_dataset_name = input("Enter the name of the background dataset: ")
       
    slice_dim = int(input("Enter the dimension for slicing (0/1/2): "))
    slice_index = int(input(f"Enter the index for slicing along dimension {slice_dim}: "))
    
   
    default_output_path = r'D:\Research\23-24\data\simulation\video'
    default_output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = input(f"Enter the output path (default: {default_output_path}): ") or default_output_path
    output_filename = input(f"Enter the output filename (default: {default_output_filename}_dim{slice_dim}_idx{slice_index}): ") or f"{default_output_filename}_dim{slice_dim}_idx{slice_index}"

    bg_colormap = 'gray'  # Default colormap for background
    if use_background_input == 'yes':
        bg_colormap = input("Enter the colormap for the background (default: gray): ") or 'gray'
    colormap = input("Enter the colormap for the animation (default: RdBu): ") or 'RdBu'
    
    frame_input = input("Enter a frame number to display a single frame, or leave blank to create an animation: ").strip()
    frame_number = int(frame_input) if frame_input.isdigit() else None
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    create_animation(file_path, dataset_name, output_path, output_filename, slice_dim, slice_index, cmap=colormap, bg_cmap=bg_colormap, frame_number=frame_number, use_background=use_background_input=='yes', background_dataset_name=background_dataset_name)
