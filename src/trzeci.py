'''
Skrypt 3.

Skrypt na wejściu przyjmuje dwie chmury punktów tego samego obszaru. Po
wczytaniu chmur wyznaczane są rastry wysokościowe NMT (klasa grunt) oraz
NMPT (grunt + budynki + roślinność) dla obu chmur. Następnie na podstawie
dwóch rastrów NMPT generowany jest raster różnicowy prezentujący zmiany
pokrycia terenu. Ścieżka do winikowego rastra w formacie GeoTIFF podawana jest
jako trzeci parametr skryptu.
'''

import argparse
import laspy
import numpy as np
from scipy.interpolate import griddata
import rasterio
from rasterio.transform import from_origin
from rasterio.crs import CRS
import os

def point_extraction_based_on_the_class(las, class_type):
    if class_type == 'buildings':
        buildings_points = las.points[las.classification == 6]
        return buildings_points
    elif class_type == 'vegetation':
        vegetation_points = las.points[np.isin(las.classification, [3, 4, 5])]
        return vegetation_points
    else:
        ground_points = las.points[las.classification == 2]
        return ground_points

def nmt(las, output_path):
    ground_points = point_extraction_based_on_the_class(las, 'ground')

    x, y, z = ground_points.x, ground_points.y, ground_points.z

    resolution = 1
    grid_x, grid_y = np.mgrid[x.min():x.max():resolution, y.min():y.max():resolution]
    grid_z = griddata((x, y), z, (grid_x, grid_y), method='linear')

    transform = from_origin(x.min(), y.max(), resolution, resolution)
    
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=grid_z.shape[0],
        width=grid_z.shape[1],
        count=1,
        dtype=grid_z.dtype,
        crs=CRS.from_string("EPSG:2180"),
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_z, 1)

def nmpt(las, output_path):
    ground_points = point_extraction_based_on_the_class(las, 'ground')
    buildings_points = point_extraction_based_on_the_class(las, 'buildings')
    vegetation_points = point_extraction_based_on_the_class(las, 'vegetation')

    x, y, z = ground_points.x, ground_points.y, ground_points.z
    x_buildings, y_buildings, z_buildings = buildings_points.x, buildings_points.y, buildings_points.z
    x_vegetation, y_vegetation, z_vegetation = vegetation_points.x, vegetation_points.y, vegetation_points.z

    resolution = 0.1
    grid_x, grid_y = np.mgrid[x.min():x.max():resolution, y.min():y.max():resolution]
    grid_z = griddata((x, y), z, (grid_x, grid_y), method='linear')
    grid_z_buildings = griddata((x_buildings, y_buildings), z_buildings, (grid_x, grid_y), method='linear')
    grid_z_vegetation = griddata((x_vegetation, y_vegetation), z_vegetation, (grid_x, grid_y), method='linear')

    grid_z = np.maximum(grid_z, grid_z_buildings, grid_z_vegetation)
    transform = from_origin(x.min(), y.max(), resolution, resolution)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=grid_z.shape[0],
        width=grid_z.shape[1],
        count=1,
        dtype=grid_z.dtype,
        crs=CRS.from_string("EPSG:2180"),
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_z, 1)

def difference_raster(nmpt_first_path, nmpt_second_path, output_path):
    with rasterio.open(nmpt_first_path) as nmpt_first:
        nmpt_first_data = nmpt_first.read(1)
    with rasterio.open(nmpt_second_path) as nmpt_second:
        nmpt_second_data = nmpt_second.read(1)

    difference = nmpt_second_data - nmpt_first_data
    transform = nmpt_first.transform

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=difference.shape[0],
        width=difference.shape[1],
        count=1,
        dtype=difference.dtype,
        crs=CRS.from_string("EPSG:2180"),
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(difference, 1)

def main():
    parser = argparse.ArgumentParser(description="NMPT.")
    parser.add_argument("first_las", type=str, help="Ścieżka do pliku LAS/LAZ.")
    parser.add_argument("second_las", type=str, help="Ścieżka do pliku LAS/LAZ.")
    args = parser.parse_args()

    first_las = laspy.read(args.first_las)
    nmt_first_path = 'tifs/nmt_first.tif'
    nmpt_first_path = 'tifs/nmpt_first.tif'
    nmt(first_las, nmt_first_path)
    nmpt(first_las, nmpt_first_path)

    second_las = laspy.read(args.second_las)
    nmt_second_path = 'tifs/nmt_second.tif'
    nmpt_second_path = 'tifs/nmpt_second.tif'
    nmt(second_las, nmt_second_path)
    nmpt(second_las, nmpt_second_path)

    difference_nmpt_path = 'tifs/difference_nmpt.tif'
    difference_raster(nmpt_first_path, nmpt_second_path, difference_nmpt_path)

    difference_nmt_path = 'tifs/difference_nmt.tif'
    difference_raster(nmt_first_path, nmt_second_path, difference_nmt_path)

if __name__ == "__main__":
    main()