# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:27:22 2023

@author: 86150
"""
import tables
import numpy as np
import os
import plotly.graph_objs as go
import matplotlib.pyplot as plt

def get_h5_info(file_path):
    with tables.open_file(file_path, 'r') as file:
        print("Datasets in the file:")
        for node in file:
            if isinstance(node, tables.array.Array):
                print(f" - {node.name}, dimensions: {node.shape}")


    
def create_animation(file_path, dataset_name, output_path, output_filename, background_dataset_name=None, frame_number=None, downsample_factor=100, frame_step=1):
    # Ensure that downsample_factor is an integer greater than or equal to 1
    downsample_factor = max(int(downsample_factor), 1)
    # Ensure that frame_step is an integer greater than or equal to 1
    frame_step = max(int(frame_step), 1)

    with tables.open_file(file_path, 'r') as file:
        data_node = file.get_node(f'/{dataset_name}')
        
        # Calculate the new shape based on the downsample factor
        new_shape = (data_node.shape[0] // downsample_factor,
                     data_node.shape[1] // downsample_factor,
                     data_node.shape[2] // downsample_factor)
        # Add a call to plot a static frame for verification

        # Prepare the figure
        fig = go.Figure()
        
        # Load background data if present
        if background_dataset_name:
            background_node = file.get_node(f'/{background_dataset_name}')
            background_data = background_node.read().astype(np.float32)
            background_data = background_data[::downsample_factor, ::downsample_factor, ::downsample_factor]
            # Add the background as a static layer in the figure
            fig.add_trace(go.Volume(
                x=np.linspace(0, new_shape[0], new_shape[0]),
                y=np.linspace(0, new_shape[1], new_shape[1]),
                z=np.linspace(0, new_shape[2], new_shape[2]),
                value=background_data.flatten(),
                isomin=background_data.min(),
                isomax=background_data.max(),
                opacity=0.1,  # Set the opacity for the background
                surface_count=1,  # Only one surface for the background
                colorscale='Greys',
                showscale=False
            ))
        
        # Add data frames
        for frame_index in range(0, data_node.shape[3], frame_step):
            
            # Read a single frame without downsample_factor
            data_slice = data_node[:, :, :, frame_index]
            
            # Now apply downsample_factor to each spatial dimension
            data = data_slice[::downsample_factor, ::downsample_factor, ::downsample_factor].astype(np.float32)
            print(f"Data range: {data.min()} to {data.max()}")
            print(f"Background range: {background_data.min()} to {background_data.max()}")
            print(data.shape)
            fig.add_trace(go.Volume(
                x=np.linspace(0, new_shape[0], new_shape[0]),
                y=np.linspace(0, new_shape[1], new_shape[1]),
                z=np.linspace(0, new_shape[2], new_shape[2]),
                value=data.flatten(),
                isomin=data.min(),
                isomax=data.max(),
                opacity=0.5,  # Adjust the opacity for the data
                surface_count=17,  # Adjust the number of isosurfaces for performance
                colorscale='Viridis',
                name=f'frame_{frame_index}'  # Give a unique name to each frame
            ))

    # Save the figure as a static HTML file
    output_file = os.path.join(output_path, f"{output_filename}.html")
    fig.write_html(output_file)
    print(f"Interactive 3D animation saved to {output_file}")



if __name__ == "__main__":
    file_path = input("Enter the path to the HDF5 file: ")
    get_h5_info(file_path)
    dataset_name = input("Enter the name of the dataset to animate: ")
    background_dataset_name = input("Enter the name of the background dataset (optional): ").strip() or None
    
    default_output_path = r'D:\Research\data\simulation\video'
    default_output_filename = os.path.splitext(os.path.basename(file_path))[0]
    output_path = input(f"Enter the output path (default: {default_output_path}): ") or default_output_path
    output_filename = input(f"Enter the output filename (default: {default_output_filename}): ") or default_output_filename
    
    frame_input = input("Enter a frame number to display a single frame, or leave blank to create an interactive 3D animation: ").strip()
    frame_number = int(frame_input) if frame_input.isdigit() else None
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        
    downsample_factor_input = input("Enter downsample factor (default is 100, higher values save memory): ").strip()
    downsample_factor = int(downsample_factor_input) if downsample_factor_input.isdigit() else 100

    frame_step_input = input("Enter frame step (default is 1, higher values skip frames): ").strip()
    frame_step = int(frame_step_input) if frame_step_input.isdigit() else 1
    # Add a call to plot a static frame for verification
    
    create_animation(file_path, dataset_name, output_path, output_filename, background_dataset_name, frame_number, downsample_factor, frame_step)