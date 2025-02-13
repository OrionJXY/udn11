import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d

# 定义参数
density = 1000  # 基站密度，单位：个/平方公里
min_distance =10# np.sqrt(1 / density)  # 最小距离，单位：千米
area_size = 40000  # 区域大小，单位：平方米

# 生成泊松分布的随机点
def generate_poisson_points(area_size, min_distance):
    num_points = int(density * area_size / 1000000)  # 计算需要生成的点的数量
    points = np.random.uniform(low=0, high=np.sqrt(area_size), size=(1, 2))  # 生成第一个点
    while len(points) < num_points:
        point = np.random.uniform(low=0, high=np.sqrt(area_size), size=(1, 2))  # 生成新的随机点
        if np.min(np.linalg.norm(points - point, axis=1)) > min_distance:  # 检查新点与已有点的距离是否大于最小距离
            points = np.vstack([points, point])
    return points

# 生成随机基站位置
points = generate_poisson_points(area_size, min_distance)

# 保存基站位置到文件
file_path = r'D:\UUDN\wireless-network-simulator-master\base_station_positions.txt'
np.savetxt(file_path, points, fmt='%f')

# 计算泰森多边形
vor = Voronoi(points)

# 绘制泰森多边形和基站
plt.figure(figsize=(8, 8))
voronoi_plot_2d(vor, show_vertices=False, line_colors='blue', line_width=2)
plt.plot(points[:,0], points[:,1], 'go', markersize=2)  # 绿色点表示基站
plt.title('Random Base Stations with Voronoi Coverage')
plt.xlabel('X')
plt.ylabel('Y')
plt.xlim(0, np.sqrt(area_size))
plt.ylim(0, np.sqrt(area_size))
plt.grid(True)
plt.show()
