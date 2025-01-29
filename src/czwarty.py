'''
Skrypt 4.

Skrypt po odczytaniu podanej przez użytkownika chmury wybierze jedynie klasę
budynków, a następnie przeprowadzi jej klasteryzację. W wyniku tej operacji każdy
budynek zostanie zidentyfikowany jako mniejsza oddzielna chmura punktów. Wynikiem
programu ma być wyświetlenie trójwymiarowej wizualizacji składającej się z gruntu
(wybrany jednolity kolor) oraz budynków (kolorowane losowo na podstawie klasteryzacji)

Skrypt 5.

Rozszerzenie zakresu skryptu z zadania 4 o wyznaczenie obrysów pojedynczych
budynków, a następnie wyeksportowanie ich w postaci wektorowej możliwej do otwarcia
w programie GIS (drugi parametr skryptu). Warstwa dla każdego budynku powinna poza
geometrią obrysu zawierać informację o polu powierzchni budynku (pole powierzchni
wyznaczonego poligonu) oraz o kubaturze budynku (objętość bryły zbudowanej z punktów
budynku).
W ramach weryﬁkacji działania programu prosimy o wyświetlenie wygenerowanych
obrysów na tle danych BDOT. Wizualizację wykonać w wybranym środowisku GIS na
podstawie danych wygenerowanych skryptem
'''

import os
import argparse
import numpy as np
import laspy
import open3d
from sklearn.cluster import DBSCAN
import geopandas as gpd
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull
import pandas as pd

def point_extraction_based_on_the_class(las, class_type):
    if class_type == 'buildings':
        return las.points[las.classification == 6]
    elif class_type == 'vegetation':
        return las.points[np.isin(las.classification, [3, 4, 5])]
    else:
        return las.points[las.classification == 2]

def main():
    parser = argparse.ArgumentParser(description="Klasteryzacja budynków.")
    parser.add_argument("file_path", type=str, help="Ścieżka do pliku LAS/LAZ.")
    parser.add_argument("out_folder", type=str, help="Ścieżka do folderu wyjściowego.")
    parser.add_argument("eps", type=float, help="Maksymalna odległość między dwoma próbkami, aby były uznane za sąsiednie.")
    parser.add_argument("min_samples", type=int, help="Minimalna liczba punktów w sąsiedztwie punktu, aby uznać go za rdzeniowy.")
    args = parser.parse_args()

    las = laspy.read(args.file_path)

    if not os.path.exists(args.out_folder):
        os.makedirs(args.out_folder)
    
    ground_points = point_extraction_based_on_the_class(las, 'ground')
    ground_points = np.vstack((ground_points.x, ground_points.y, ground_points.z)).T
    
    buildings_points = point_extraction_based_on_the_class(las, 'buildings')
    buildings_points = np.vstack((buildings_points.x, buildings_points.y, buildings_points.z)).T
    
    clustering = DBSCAN(eps=args.eps, min_samples=args.min_samples).fit(buildings_points)
    labels = clustering.labels_
    max_label_buildings = labels.max()

    colors_buildings = np.random.rand(max_label_buildings + 1, 3) 
    point_colors_buildings = np.zeros((labels.shape[0], 3))

    for i in range(max_label_buildings + 1):
        point_colors_buildings[labels == i] = colors_buildings[i]

    bds_cloud = open3d.geometry.PointCloud()
    bds_cloud.points = open3d.utility.Vector3dVector(buildings_points)
    bds_cloud.colors = open3d.utility.Vector3dVector(point_colors_buildings)

    ground_cloud = open3d.geometry.PointCloud()
    ground_cloud.points = open3d.utility.Vector3dVector(ground_points)
    ground_cloud.paint_uniform_color([0.5, 0.5, 0.5])

    open3d.visualization.draw_geometries([bds_cloud, ground_cloud])

    gdf = gpd.GeoDataFrame(columns=["geometry", "pole", "objetosc"], crs="EPSG:2180")
    for i in range (max_label_buildings + 1):
        building = buildings_points[labels == i]
        cloud = open3d.geometry.PointCloud()
        cloud.points = open3d.utility.Vector3dVector(building)
        
        hull3d = ConvexHull(np.asarray(cloud.points))
        volume = hull3d.volume

        hull2d = ConvexHull(np.asarray(cloud.points)[:, :2])
        area = hull2d.volume

        polygon = Polygon(hull2d.points[hull2d.vertices])
        new_row = gpd.GeoDataFrame([{"geometry": polygon, "pole": area, "objetosc": volume}], crs="EPSG:2180")
        gdf = pd.concat([gdf, new_row], ignore_index=True)

    gdf.to_file(f"{args.out_folder}/buildings.shp")

if __name__ == "__main__":
    main()
