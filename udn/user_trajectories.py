import matplotlib.pyplot as plt
from datetime import datetime
import csv
import numpy as np

# 计算两点之间的距离（米）
def calculate_distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    earth_radius = 6371000  # 地球半径，单位：米
    d_lat = np.radians(lat2 - lat1)
    d_lon = np.radians(lon2 - lon1)
    a = np.sin(d_lat / 2) * np.sin(d_lat / 2) + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(d_lon / 2) * np.sin(d_lon / 2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = earth_radius * c
    return distance

# 缩放数据到指定范围
def scale_data(data, target_range):
    latitudes = [item[0] for item in data]
    longitudes = [item[1] for item in data]
    
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)

    # 处理除以零的情况
    if max_lat == min_lat:
        max_lat += 0.0001
    if max_lon == min_lon:
        max_lon += 0.0001

    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon

    lat_scale = target_range[0] / lat_range
    lon_scale = target_range[1] / lon_range

    scaled_data = []
    for item in data:
        scaled_lat = (item[0] - min_lat) * lat_scale
        scaled_lon = (item[1] - min_lon) * lon_scale
        scaled_data.append((scaled_lat, scaled_lon, item[2],item[3]))
    
    return scaled_data

# 数据预处理：去除速度异常点并修正为周围数据点的平均值
def preprocess_data(data):
    preprocessed_data = [data[0]]  # 先将第一个数据点添加到处理后的数据中
    for i in range(2, len(data) - 1):

        lat1, lon1, direction,time1 = data[i-1]
        lat2, lon2, direction,time2 = data[i]
        lat3, lon3, direction,time3 = data[i+1]
        speed1 = calculate_distance((lat1, lon1), (lat2, lon2)) / (time2 - time1).total_seconds()
        speed2 = calculate_distance((lat2, lon2), (lat3, lon3)) / (time3 - time2).total_seconds()
        # print(speed1,speed2)
        if speed1 <= 8 and speed2 <= 8:  # 如果两个相邻数据点的速度都在正常范围内，则将当前数据点添加到处理后的数据中
            preprocessed_data.append(data[i])
        else:  # 如果有一个数据点的速度超过正常范围，则修正为前后数据点的平均值
            corrected_lat = (lat1 + lat3) / 2
            corrected_lon = (lon1 + lon3) / 2
            preprocessed_data.append((corrected_lat, corrected_lon, direction,time2))
    
    # 处理轨迹点与相邻轨迹点差距大于16米的情况
    for i in range(1, len(preprocessed_data) - 1):
        lat1, lon1,direction, time1 = preprocessed_data[i-1]
        lat2, lon2,direction, time2 = preprocessed_data[i]
        lat3, lon3,direction, time3 = preprocessed_data[i+1]
        dist1 = calculate_distance((lat1, lon1), (lat2, lon2))
        dist2 = calculate_distance((lat2, lon2), (lat3, lon3))
        if dist1 > 16 or dist2 > 16:
            lat_avg = (lat1 + lat2 + lat3) / 3
            lon_avg = (lon1 + lon2 + lon3) / 3
            preprocessed_data[i] = (lat_avg, lon_avg,  direction,time2)
    
    preprocessed_data.append(data[-1])  # 将最后一个数据点添加到处理后的数据中
    return preprocessed_data



# 从数据文件中读取经纬度数据
all_data = []
for i in range(50):
    data = []
    with open(f'D://UUDN//LSTM-for-Trajectory-Prediction-master//073//Trajectory//{i}.plt', 'r') as file:
        for index, line in enumerate(file):
            if index < 6:
                continue
            if line.strip() and not line.startswith('Reserved'):
                parts = line.split(',')
                latitude = float(parts[0])
                longitude = float(parts[1])
                direction = float(parts[3])
                timestamp = datetime.strptime(parts[5] + ' ' + parts[6].strip(), '%Y-%m-%d %H:%M:%S')
                data.append((latitude, longitude,  direction,timestamp))
    all_data.append(data)

# 数据预处理和缩放数据到200x200米的范围内
target_range = (200, 200)
scaled_preprocessed_data = []
for data in all_data:
    preprocessed_data = preprocess_data(data)
    scaled_data = scale_data(preprocessed_data, target_range)
    scaled_preprocessed_data.append(scaled_data)

print(scaled_preprocessed_data)

# 创建画布和子图
fig, ax = plt.subplots(figsize=(8, 8))

# 绘制缩放后的数据点
for i, data in enumerate(scaled_preprocessed_data):
        scaled_latitudes = [item[0] for item in data]
        scaled_longitudes = [item[1] for item in data]
        ax.plot(scaled_longitudes, scaled_latitudes, marker='.', label=f' {i+1}')

# 添加图例
ax.legend()

# 设置标题和坐标轴标签
ax.set_title('Locations of Datasets (Mapped to 200x200m Range)')
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')

plt.show()

# 将转换后的坐标点和速度存入文件
with open('mapped_data_with_speed.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['ID', 'Latitude', 'Longitude','direction' 'Speed'])
    for i, data in enumerate(scaled_preprocessed_data):
         # 获取第一个数据点的时间
        first_time = datetime.strptime(parts[5] + ' ' + parts[6].strip(), '%Y-%m-%d %H:%M:%S')
        for j in range(len(scaled_preprocessed_data) - 1):
                if j + 1 < len(data):  # 添加检查以确保索引不超出范围
                    lat1, lon1, direction, time1 = data[j]
                    lat2, lon2, direction, time2 = data[j+1]
                else:
                    break  # 如果超出范围，退出循环
                # 计算速度时使用相邻数据点的时间
                speed = ((lat2 - lat1)**2 + (lon2 - lon1)**2)**0.5 / (time2 - time1).total_seconds()
                time_interval = (time1 - first_time).total_seconds()
                if j == 0:
                    first_time_1 = time_interval
                time = time_interval - first_time_1

                # print((time2 - time1).total_seconds())
                # print(calculate_distance((lat1, lon1), (lat2, lon2)) ) 
                writer.writerow([i+1, lat1, lon1, direction, speed, time])

        # 最后一个数据点速度设为0
        lat_last, lon_last, direction,  _ = data[-1]
        writer.writerow([i+1, lat_last, lon_last,0,0,time+2])

print("转换后的坐标点和速度已存入文件 mapped_data_with_speed.csv")
