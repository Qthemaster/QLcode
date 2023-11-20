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

def create_animation(file_path, dataset_name, output_path, output_filename, cmap='viridis', bg_cmap='gray', frame_number=None, use_background=True, background_dataset_name=None):
    with tables.open_file(file_path, 'r') as file:
        data = file.get_node(f'/{dataset_name}')[:]
        background_data = None
        if use_background and background_dataset_name:
            background_data = file.get_node(f'/{background_dataset_name}')[:]
        
        # Check if the data is two-dimensional and reshape it to three dimensions if necessary
        if len(data.shape) == 2:
            data = data[:, :, np.newaxis]  # Add a new axis to make it three-dimensional
        
        # If a background dataset is provided and chosen to be used, reshape it as well
        if background_data is not None and len(background_data.shape) == 2:
            background_data = background_data[:, :, np.newaxis]

    fig, ax = plt.subplots()
    
    # Plot the static background if it's available and wanted
    if background_data is not None and use_background:
        ax.imshow(background_data[:, :, 0].T, cmap=bg_cmap)
    
    if frame_number is not None and 0 <= frame_number < data.shape[2]:
        # If a valid frame number is provided, show only that frame
        ax.imshow(data[:, :, frame_number].T, cmap=cmap)
    else:
        # Otherwise, create an animation
        animation = ax.imshow(data[:, :, 0].T, animated=True, cmap=cmap, alpha=0.9)

        def update(frame):
            # Update only the animation layer
            animation.set_array(data[:, :, frame].T)
            return animation,

        ani = FuncAnimation(fig, update, frames=data.shape[2], blit=True)
        ani.save(os.path.join(output_path, f'{output_filename}.gif'), writer='pillow')

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
    
    default_output_path = r'D:\Research\data\simulation\video'
    default_output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = input(f"Enter the output path (default: {default_output_path}): ") or default_output_path
    output_filename = input(f"Enter the output filename (default: {default_output_filename}): ") or default_output_filename
    
    bg_colormap = 'gray'  # Default colormap for background
    if use_background:
        bg_colormap = input("Enter the colormap for the background (default: gray): ") or 'gray'
    colormap = input("Enter the colormap for the animation (default: RdBu): ") or 'RdBu'
    
    frame_input = input("Enter a frame number to display a single frame, or leave blank to create an animation: ").strip()
    frame_number = int(frame_input) if frame_input.isdigit() else None
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    
    create_animation(file_path, dataset_name, output_path, output_filename, cmap=colormap, bg_cmap=bg_colormap, frame_number=frame_number, use_background=use_background, background_dataset_name=background_dataset_name)