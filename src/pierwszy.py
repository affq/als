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

def classify_points(las, class_ids):
    return {name: las.points[las.classification == cid] for name, cid in class_ids.items()}

def visualize_data(classified, colors_map):
    plt.bar(classified.keys(), [len(c) for c in classified.values()], color="red")
    plt.title("Liczba punktów w poszczególnych klasach")
    plt.xlabel("Klasy")
    plt.ylabel("Liczba punktów")
    plt.show()

    points = np.vstack([np.vstack((cls.x, cls.y, cls.z)).T for cls in classified.values()])
    classifications = np.hstack([cls.classification for cls in classified.values()])
    point_colors = np.array([mcolors.hex2color(colors_map[c]) for c in classifications])

    cloud = open3d.geometry.PointCloud()
    cloud.points = open3d.utility.Vector3dVector(points)
    cloud.colors = open3d.utility.Vector3dVector(point_colors)
    open3d.visualization.draw_geometries([cloud])

def main():
    parser = argparse.ArgumentParser(description="Klasyfikacja.")
    parser.add_argument("file_path", type=str, help="Ścieżka do pliku LAS/LAZ.")
    args = parser.parse_args()

    las = laspy.read(args.file_path)

    class_ids = {
        "ground": 2,
        "low vegetation": 3,
        "medium vegetation": 4,
        "high vegetation": 5,
        "building": 6,
    }
    colors_map = {
        2: '#aa5500',
        3: '#00aaaa',
        4: '#55ff55',
        5: '#00aa00',
        6: '#ff5555',
    }

    classified = classify_points(las, class_ids)
    visualize_data(classified, colors_map)

if __name__ == "__main__":
    main()