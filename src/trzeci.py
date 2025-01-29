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
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def extract_points_by_class(las, class_type):
    class_map = {
        'buildings': 6,
        'ground': 2,
        'vegetation': [3, 4, 5]
    }
    if class_type not in class_map:
        raise ValueError(f"Nieznana klasa: {class_type}")
    mask = np.isin(las.classification, class_map[class_type])
    return las.points[mask]

def generate_raster(x, y, z, resolution, crs, output_path):
    grid_x, grid_y = np.mgrid[x.min():x.max():resolution, y.min():y.max():resolution]
    grid_z = griddata((x, y), z, (grid_x, grid_y), method='linear')
    grid_z_rotated = np.rot90(grid_z, k=1)
    transform = from_origin(x.min(), y.max(), resolution, resolution)
    
    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=grid_z_rotated.shape[0],
        width=grid_z_rotated.shape[1],
        count=1,
        dtype=grid_z_rotated.dtype,
        crs=crs,
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_z_rotated, 1)

def process_nmt(las, output_path, resolution, crs):
    ground_points = extract_points_by_class(las, 'ground')
    generate_raster(ground_points.x, ground_points.y, ground_points.z, resolution, crs, output_path)
    logging.info(f"Wygenerowano NMT: {output_path}")

def process_nmpt(las, output_path, resolution, crs):
    ground_points = extract_points_by_class(las, 'ground')
    buildings_points = extract_points_by_class(las, 'buildings')
    vegetation_points = extract_points_by_class(las, 'vegetation')

    x = np.concatenate((ground_points.x, buildings_points.x, vegetation_points.x))
    y = np.concatenate((ground_points.y, buildings_points.y, vegetation_points.y))
    z = np.concatenate((ground_points.z, buildings_points.z, vegetation_points.z))

    generate_raster(x, y, z, resolution, crs, output_path)
    logging.info(f"Wygenerowano raster NMPT: {output_path}")

def calculate_difference_raster(first_raster_path, second_raster_path, output_path):
    with rasterio.open(first_raster_path) as first_raster:
        first_data = first_raster.read(1)
        transform = first_raster.transform

    with rasterio.open(second_raster_path) as second_raster:
        second_data = second_raster.read(1)

    difference = second_data - first_data

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=difference.shape[0],
        width=difference.shape[1],
        count=1,
        dtype=difference.dtype,
        crs=first_raster.crs,
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(difference, 1)

    logging.info(f"Wygenerowano różnicowy raster: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generowanie NMT, NMPT i obliczanie różnic.")
    parser.add_argument("first_las", type=str, help="Ścieżka do pliku LAS/LAZ.")
    parser.add_argument("second_las", type=str, help="Ścieżka do pliku LAS/LAZ.")
    parser.add_argument("out_folder", type=str, help="Ścieżka do folderu wynikowego.")
    parser.add_argument("-r", "--resolution", type=float, default=5.0, help="Rozdzielczość rastrów.")
    parser.add_argument("-c", "--crs", type=int, default=2180, help="Układ współrzędnych (CRS).")
    args = parser.parse_args()

    os.makedirs(args.out_folder, exist_ok=True)

    crs = CRS.from_epsg(args.crs)
    first_las = laspy.read(args.first_las)
    second_las = laspy.read(args.second_las)

    process_nmt(first_las, os.path.join(args.out_folder, "nmt_first.tif"), args.resolution, crs)
    process_nmpt(first_las, os.path.join(args.out_folder, "nmpt_first.tif"), args.resolution, crs)
    process_nmt(second_las, os.path.join(args.out_folder, "nmt_second.tif"), args.resolution, crs)
    process_nmpt(second_las, os.path.join(args.out_folder, "nmpt_second.tif"), args.resolution, crs)

    calculate_difference_raster(
        os.path.join(args.out_folder, "nmpt_first.tif"),
        os.path.join(args.out_folder, "nmpt_second.tif"),
        os.path.join(args.out_folder, "difference_nmpt.tif")
    )
    calculate_difference_raster(
        os.path.join(args.out_folder, "nmt_first.tif"),
        os.path.join(args.out_folder, "nmt_second.tif"),
        os.path.join(args.out_folder, "difference_nmt.tif")
    )

if __name__ == "__main__":
    main()
