'''
Skrypt 2.

Skrypt po wczytaniu chmury z wykorzystaniem analizy sąsiedztwa wyznacza jej
gęstość (liczba punktów na metr kwadratowy/sześcienny). Następnie wynik
analizowany jest i prezentowany w formie histogramu rozkładu gęstości punktów.
Parametrami skryptu są:
a. Ścieżka do pliku LAS/LAZ (parametr obowiązkowy)
b. Flaga pozwalająca na wybór wyznaczania gęstości 2D/3D (domyślnie 2D)
c. Flaga, która powoduje, że analiza prowadzona jest tylko dla klasy gruntu
(domyślnie analizowana jest cała chmura)
'''

import argparse
import laspy
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.spatial import KDTree

def main():
    parser = argparse.ArgumentParser(description="Gęstość punktów.")
    parser.add_argument("file_path", type=str, help="Ścieżka do pliku LAS/LAZ.")
    parser.add_argument("-d", "--density", choices=["2d", "2D", "3d", "3D"], default="2D", help="Tryb wyznaczania gęstości: 2d (default) lub 3d.")
    parser.add_argument("-g", "--ground-only", action="store_true", help="Jeśli ustawiona, analiza będzie dotyczyła tylko klasy gruntu. Domyślnie analizowana jest cała chmura.")

    args = parser.parse_args()

    las = laspy.read(args.file_path)

    if args.density.lower() == "3d":
        points = np.vstack((las.x, las.y, las.z)).T
    else:
        points = np.vstack((las.x, las.y)).T

    if args.ground_only:
        ground_mask = (las.classification == 2)
        points = points[ground_mask]

    tree = KDTree(points)

    densities = []
    for point in points:
        indices = tree.query_ball_point(point, r=1)
        densities.append(len(indices) - 1)

    densities = np.array(densities)

    sns.histplot(densities, bins=50, kde=True)
    plt.title("Density (r=1)")
    plt.xlabel("Density")
    plt.ylabel("Count")
    plt.show()

if __name__ == "__main__":
    main()