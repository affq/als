'''
Skrypt 1.

Uzytkownik podaje na wejściu ścieżkę do chmury punktów w formacie LAS/LAZ.
Skrypt po wczytaniu chmury analizuje informację o klasyfikacji punktów i
przygotowuje dwie wizualizacje – 1) wykres słupkowy pokazujący liczbę punktów
w danej klasie definiowanej przez ASPRS; 2) Interaktywną wizualizację 3D
prezentującą punkty pokolorowane po numerze klasy wg przyjętej palety barwnej
(np. zbliżonej do CloudCompare lub ArcGIS Pro).
'''

import argparse
import laspy
import numpy as np
import open3d
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def classify(las):
    ground_points = las.points[las.classification == 2]
    vegetation_low = las.points[las.classification == 3]
    vegetation_medium = las.points[las.classification == 4]
    vegetation_high = las.points[las.classification == 5]
    buildings = las.points[las.classification == 6]
    water = las.points[las.classification == 9]
    
    classified = {
        "ground": ground_points,
        "low vegetation": vegetation_low,
        "medium vegetation": vegetation_medium,
        "high vegetation": vegetation_high,
        "building": buildings,
        "water": water
    }
    return classified

def main():
    parser = argparse.ArgumentParser(description="Klasyfikacja.")
    parser.add_argument("file_path", type=str, help="Ścieżka do pliku LAS/LAZ.")
    args = parser.parse_args()

    las = laspy.read(args.file_path)
    x, y, z = las.x, las.y, las.z
    points = np.vstack((x, y, z)).T

    classified = classify(las)

    plt.bar(classified.keys(), [len(classy) for classy in classified.values()], color="red")
    plt.title("Liczba punktów w poszczególnych klasach")
    plt.xlabel("Klasy")
    plt.ylabel("Liczba punktów")
    plt.show()

    class_colors_map = {
        2: 'red',
        3: 'green',
        4: 'blue',
        5: 'black',
        6: 'white',
        9: 'yellow',
    }

    points_from_chosen_classes = []
    for record in classified.values():
        points = np.vstack((record.x, record.y, record.z)).T
        points_from_chosen_classes.append(points)

    points_from_chosen_classes = np.vstack(points_from_chosen_classes)
    all_classifications = np.hstack([record.classification for record in classified.values()])
    point_colors = np.array([class_colors_map[classy] for classy in all_classifications])
    
    cloud = open3d.geometry.PointCloud()
    cloud.points = open3d.utility.Vector3dVector(points_from_chosen_classes)
    rgb_colors = np.array([mcolors.to_rgb(color) for color in point_colors])
    cloud.colors = open3d.utility.Vector3dVector(rgb_colors)
    
    open3d.visualization.draw_geometries([cloud])

if __name__ == "__main__":
    main()