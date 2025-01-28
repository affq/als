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

import argparse
import laspy
import numpy as np
import open3d
import open3d.visualization
from sklearn.cluster import DBSCAN
from scipy.spatial import ConvexHull
import geopandas as gpd
from shapely.geometry import Polygon

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

def main():
    parser = argparse.ArgumentParser(description="Klasteryzacja budynków.")
    parser.add_argument("file_path", type=str, help="Ścieżka do pliku LAS/LAZ.")
    args = parser.parse_args()

    las = laspy.read(args.file_path)
    
    ground_points = point_extraction_based_on_the_class(las, 'ground')
    ground_points = np.vstack((ground_points.x, ground_points.y, ground_points.z)).T
    
    buildings_points = point_extraction_based_on_the_class(las, 'buildings')
    buildings_points = np.vstack((buildings_points.x, buildings_points.y, buildings_points.z)).T
    
    clustering = DBSCAN(eps=3.5, min_samples=35).fit(buildings_points)
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

    # open3d.visualization.draw_geometries([bds_cloud, ground_cloud])

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
        gdf = gdf._append({"geometry": polygon, "pole": area, "objetosc": volume}, ignore_index=True)

    gdf.to_file("out/buildings.shp")

if __name__ == "__main__":
    main()