import csv
import re
import netCDF4 as nc
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, ListedColormap, BoundaryNorm
from matplotlib.cm import ScalarMappable
import numpy as np

def extract_depth_layers(netcdf_file, output_folder, variable_name, colormap_name, low_cmap, high_cmap, file_no_path, csv_path):
    # Open the NetCDF file
    nc_file = nc.Dataset(netcdf_file, 'r')

    # Extract the variable data
    variable_data = nc_file[variable_name][:]

    # depth_dimension = nc_file.dimensions['s_rho'].size
    depth_dimension = variable_data.shape[1]

    # Define the colormap
    colormap = plt.get_cmap(colormap_name)
    # print(np.nanmin(variable_data), np.nanmax(variable_data))

    norm = Normalize(vmin=low_cmap, vmax=high_cmap)

    # Loop through each depth layer and save as an image
    for depth_index in range(depth_dimension):
        # Extract the depth layer
        depth_layer = variable_data[0, depth_index, :, :]
        # depth_layer = np.where(np.isfinite(depth_layer), depth_layer, np.nan)

        depth_layer = np.ma.masked_invalid(depth_layer)
        # depth_layer = np.transpose(depth_layer)

        # Create a figure and axis
        fig, ax = plt.subplots()
        
        # Plot the depth layer with specified colormap
        im = ax.imshow(depth_layer, cmap=colormap, origin='lower', norm = norm)
        im.cmap.set_bad('gray')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label(variable_name)
        # cbar.cmap.set_bad('gray')

        # Save the figure as an image (modify the filename as needed)
        output_filename = f"{file_no_path}_{variable_name}_{depth_index}.png"
        output_filepath = output_folder+output_filename
        plt.savefig(output_filepath, format='png', dpi=300)
        

        timestep = int(file_no_path[18:22])
        with open(csv_path, 'a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            row = [depth_index, timestep, variable_name, output_filename]
            csv_writer.writerow(row)
        # Close the figure to avoid memory issues
        plt.close()

    # Close the NetCDF file
    nc_file.close()

# : depth: s_rho, size: 40;xi_rho Size: 2113; eta_rho Size: 1887

netcdf_file = '/home/toshit/datasets/roms_bobhires_avg_0001.nc'
netcdf_file = '/home/toshit/Downloads/roms_bobhires_avg_1080.nc'
output_folder = '/home/toshit/cinema/'
csv_path = '/home/toshit/cinema/data.csv'
variable_name = 'salt'
colormap_name = 'hsv'
parent_folder_path = "/home/toshit/ROMS/RUN1km_exp3_river/output/"

# extract_depth_layers(netcdf_file, output_folder, variable_name, colormap_name)

with open('/home/toshit/cinema/filelist.txt', 'r') as filelist:
    filelist.seek(0)
    for i in range(500):
        line = filelist.readline().strip()

        nc_file = parent_folder_path+line 

        extract_depth_layers(nc_file, output_folder, 'salt', 'gist_ncar', 25 , 40, line, csv_path)
        extract_depth_layers(nc_file, output_folder, 'temp', 'hsv', 0 , 36, line, csv_path)
        # extract_depth_layers(nc_file, output_folder, 'u_eastward', 'nipy_spectral', -2 , 2, line, csv_path)
        # extract_depth_layers(nc_file, output_folder, 'v_northward', 'nipy_spectral', -2 , 2, line, csv_path)
        