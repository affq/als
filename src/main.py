import argparse
import laspy
import numpy as np
import open3d
import matplotlib.pyplot as plt

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
    parser = argparse.ArgumentParser(description="Analiza chmury punktów z pliku LAS/LAZ.")

    parser.add_argument(
        "file_path",
        type=str,
        help="Ścieżka do pliku LAS/LAZ."
    )

    parser.add_argument(
        "-d",
        "--density",
        choices=["2d", "3d"],
        help="Tryb wyznaczania gęstości: 2d (default) lub 3d."
    )

    parser.add_argument(
        "-g", 
        "--ground-only",
        action="store_true",
        help="Jeśli ustawiona, analiza będzie dotyczyła tylko klasy gruntu. Domyślnie analizowana jest cała chmura."
        )

    args = parser.parse_args()
    # args.file_path, args.density, args.ground_only

    las = laspy.read(args.file_path)
    x, y, z = las.x, las.y, las.z
    points = np.vstack((x, y, z)).T
    print("Liczba punktów:", len(points))

    header = las.header
    print("Wersja LAS:", header.version)
    print("Identyfikator systemu:", header.system_identifier)
    print("Oprogramowanie generujące:", header.generating_software)
    print("Wartości minimalne i maksymalne:")
    print("Min X, Y, Z:", header.min)
    print("Max X, Y, Z:", header.max)

    point_format = las.point_format
    for spec in point_format:
        print(spec.name)

    classified = classify(las)

    plt.bar(classified.keys(), [len(classy) for classy in classified.values()], color="red")
    plt.title("Liczba punktów w poszczególnych klasach")
    plt.xlabel("Klasy")
    plt.ylabel("Liczba punktów")
    plt.show()

    cloud = open3d.geometry.PointCloud()
    cloud.points = open3d.utility.Vector3dVector(points)
    open3d.visualization.draw_geometries([cloud])


if __name__ == "__main__":
    main()