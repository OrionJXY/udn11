import environment
import util
import numpy as np
import matplotlib.pyplot as plt
import NRBaseStation as mbs
from NRBaseStation import BaseStation
import UserEquipment as ue
import random
import time
import os
import pandas as pd
import csv

PLOT = False     # 是否进行绘图
N_UE = 40           # 用户设备数
ITER = 2        # 模拟迭代次数

#关联模式 1:RSRP 2:SINR 3:pridiction+SINR  4：速率因子和位置因子 5 ：自己的算法
# ue_class = [0,0,0,0,0,0,0,0,0,0,1,1,1,1,1,1,2,2,2,2,3,3,3,3,3,4,4,4,4,4,5,5,5,5,5,5,5,5,5,5]  #25M
ue_class = [7,6,5,5,5,5,5,5,5,5,3,3,3,4,4,1,1,1,1,1,1,2,2,2,2,3,3,3,3,3,4,4,4,4,4,0,0,0,0,0]  #30M
# ue_class=[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
# ue_class=[4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]
# ue_class=[5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
# ue_class= [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

random.seed(2)      # 设置随机数种子  


#场景大小（米）和 采样时间间隔
#关联模式 1:RSRP 2:SINR 3:pridiction+SINR  4：速率因子和位置因子 5 ：自己的算法
env = environment.wireless_environment(200,200, sampling_time=1,connectMode = 3)


#清空文件
with open('data/RA_result.csv', 'w') as file:
    pass
with open('data/virtual_cell.txt', 'w') as file:
    pass
with open('data/connected_users.txt', 'w') as file:
    pass
with open('data/connection_info.csv', 'w') as file:
    pass


ue = []# 初始化UE列表、基站列表、误差记录、延迟记录及资源分配记录
bs = []
error = []
latency = {}
prbs = {}
bitrates = {}
total_data = 0
# 随机生成N_UE个UE并插入到环境中
for i in range(0, N_UE):
    id = env.insert_ue(ue_class[i], starting_position=(random.randint(0, env.x_limit-1), random.randint(0, env.y_limit-1), 1), speed = 1, direction = random.randint(0, 359))
    ue.append(id)
# file_path = r'D:data/base_station_positions.txt'# 读取文件中的位置数据
file_path = r'D:data/base_road.txt' #十字路口
positions = np.loadtxt(file_path)# 遍历文件中的位置数据
for pos in positions:
    freq = 3500  # 频率信息
    numerology = 1  # 数字调制方式信息
    power =23  # 发射功率信息
    gain = 5   # 收发增益信息
    loss =1   # 衰减损耗
    bandwidth = 50   # 带宽信息
    max_bitrate =1200 # 最大比特率信息
    parm = [{
        "pos": (pos[0], pos[1], 10),  # 基站位置信息，假设高度固定为10
        "freq": freq,
        "numerology": numerology,
        "power": power,
        "gain": gain,
        "loss": loss,
        "bandwidth": bandwidth,
        "max_bitrate": max_bitrate
    }]
    for i in range(len(parm)):
        nr_bs2 = env.place_NR_base_station(
            parm[i]["pos"], 
            parm[i]["freq"],
            parm[i]["numerology"], 
            parm[i]["power"], 
            parm[i]["gain"], 
            parm[i]["loss"], 
            parm[i]["bandwidth"], 
            total_bitrate = parm[i]["max_bitrate"])
    bs.append(nr_bs2)
env.initial_timestep();# 初始化模拟时间步长
#print("env.z_beta", env.wardrop_beta)

# util.plot(e, bs, env)
# plt.pause(30)u

total_ue_data = {}  # 初始化累加列表
bs_info_array = []
connected_users_array = []
RA_array =  []
connection_info_array = []
current_bs = 0

# UE连接可用基站
for phone in ue:
    print("-------------------", phone, "-------------------")
    available_bs = env.discover_bs(phone)
    bs_id_list = util.find_ue_by_id(phone).get_the_top_bs(available_bs)
    current_bs =util.find_ue_by_id(phone).connect_to_bs_id(bs_id_list)

env.next_timestep()
max_e = 0 # 初始化最大误差值
user_bs_matrix = []
len_all = 0

# 开始模拟过程，每迭代一次执行以下操作
for i in range(0,ITER):
    if i % 10  ==  0:
        print("-------------------", i, "-------------------")

        # for bsc in rsrp:
        #     sinr[bsc] = util.find_bs_by_id(bsc).compute_sinr(rsrp)
        # # print("SINR: ", sinr)
 
        # for bsi in bs:
                # print("BS ", bsi, " PRB: ", util.find_bs_by_id(bsi).allocated_prb, "/", util.find_bs_by_id(bsi).total_prb, " Bitrate: ", util.find_bs_by_id(bsi).allocated_bitrate, "/", util.find_bs_by_id(bsi).total_bitrate)
                # df = pd.DataFrame.from_dict(bitrates[bsi])
                #       df.to_csv("D:/UUDN/wireless-network-simulator-master/data/bitrate_BS"+str(bsi)+".csv", sep=";")
        for bsi in bs:
            bs_info = "AP " + str(bsi) + "     PRB: " + str(util.find_bs_by_id(bsi).allocated_prb) + "/" + str(util.find_bs_by_id(bsi).total_prb) + "        Bitrate: " + str(util.find_bs_by_id(bsi).allocated_bitrate) + "/" + str(util.find_bs_by_id(bsi).total_bitrate) + "\n"
            bs_info_array.append(bs_info)
            connected_users = util.find_bs_by_id(bsi).get_connected_users()
            # connected_users_array.append(connected_users)

            with open("data/connected_users.txt", "a") as file: 
                file.write(" BS ID: %s    connected_users: %s  "%(bsi,str(connected_users)+'\n'))
            
                       
        with open("data/bs_info.txt", "w") as file:
            combined_info = "".join(bs_info_array)  
            file.write(combined_info)  


    
    # 更新UE与基站的连接状态
    for phone in ue:
        current_bs = util.find_ue_by_id(phone).update_connection()
        with open("data/virtual_cell.txt", "a") as file:
            file.write("虚拟小区id  %s : %s \n" % (phone, current_bs))
            
        rsrp = env.discover_bs(phone)  # 发现基站的RSRP（Reference Signal Received Power）
        if len(RA_array) > 0:
            for bsc in current_bs:
                RA = util.find_bs_by_id(bsc).compute_RA(rsrp)
                RA_array.append(RA)
                connection_info = util.find_bs_by_id(bsc).get_connection_info(phone)
                connection_info_array.append(connection_info)
        RA_avg = sum(RA_array)
        connection_info = sum(connection_info_array)

        with open('D:data/RA_result.csv', "a") as file:
            file.write(str(RA_avg ) + '\n')
        with open('D:data/connection_info.csv', "a") as file:
            file.write(str(connection_info) + '\n')
        phonex = util.find_ue_by_id(phone)
        # for idx, phone in enumerate(ue):
        #     for bs_idx, bsx in enumerate(bs):
        #         if bsx in phonex.current_bs:
        #             user_bs_matrix[idx, bs_idx] = 1#在用户-基站关联矩阵中对应位置标记为1，表示该用户与该基站存在关联关系
        # for idx, user_row in enumerate(user_bs_matrix):
        #     print(f"User {idx}:", user_row)

        len_all += len(current_bs)/ITER
        total_ue_data[phonex]=sum(phonex.current_bs.values())  # 将当前用户实体的基站数据总和添加到 total_bs_data 中
        total_data += total_ue_data[phonex]

        

    #     # 计算该UE在各个基站下的最大和最小延迟
    #     l_max = 0
    #     l_min = float("inf")
    #     latency_phone={}
    #     for bsa in util.find_ue_by_id(phone).bs_bitrate_allocation:
    #         # print("111",util.find_ue_by_id(phone).bs_bitrate_allocation)
    #         l = util.find_bs_by_id(bsa).compute_latency(phone)
            
    #         latency_phone[bsa]=l

    #         if util.find_ue_by_id(phone).bs_bitrate_allocation[bsa] > 0.0001 and l > l_max:
    #             l_max = l
    #         elif util.find_ue_by_id(phone).bs_bitrate_allocation[bsa] < util.find_bs_by_id(bsa).total_bitrate-(env.wardrop_epsilon/(2*env.wardrop_beta)) and l < l_min:
    #             l_min = l
    #     e = l_max - l_min # 计算误差e，并更新最大误差值
    #     if e > max_e:
    #         max_e = e
    #     if phone not in latency:  # 将本次迭代的延迟信息存储到latency字典中
    #         latency[phone] = []
    #     latency[phone].append(latency_phone)
    # error.append(max_e)# 将本次迭代的最大误差值添加到error列表中
    env.next_timestep()

print("total_data = %s  Avg_data  = %s" %(total_data,total_data/N_UE/ITER) )
print("len_all= ", len_all)

util.plot(ue, bs, env)
# plt.pause(10)

# for bsi in bs: # 记录各基站分配的PRB资源和比特率
#     if bsi not in prbs:
#         prbs[bsi] = []
#     if bsi not in bitrates:
#         bitrates[bsi] = []

#     prbs[bsi].append(util.find_bs_by_id(bsi).allocated_prb)
#     bitrates[bsi].append(util.find_bs_by_id(bsi).allocated_bitrate)

# plt.bar(ue, list(total_ue_data.values()))# 绘制柱状图
# plt.xlabel('User  ID')# 添加标题和标签
# plt.ylabel('Total Bitrate')
# plt.title('Total Bitrate Allocation for Each User')
# plt.show()# 显示图形

# bs_total_bitrate= 0
# bs_total_bitrate = sum([sum(bitrates[bsi]) for bsi in bs])
# with open("D:\\UUDN\\wireless-network-simulator-master\\data\\total_bitrate.txt", "a") as file:# 首先打开文件以写入模式
#     total_bitrate_str = str(bs_total_bitrate)

#     file.write(total_bitrate_str+ "\n")

# # 创建一个新的图表
# plt.figure(figsize=(6, 4))
# # 绘制柱状图
# plt.bar(0, total_data, color='skyblue')
# # 设置图表标题和轴标签
# plt.title('Total Bitrate')
# plt.xlabel('N')
# plt.ylabel('Total Bitrate')
# # plt.xticks([])# 隐藏x轴刻度标签
# # 显示图表
# plt.tight_layout()
# plt.show()


# env.next_timestep()
    #print(phone1.bs_bitrate_allocation)

print("\n\n---------------------------------------------------\n\n")
# for phone in ue:
#     print("UE %s: %s" %(phone, util.find_ue_by_id(phone).bs_bitrate_allocation))
print("\n\n---------------------------------------------------\n\n")
#print(latency)
# print(util.find_ue_by_id(3).current_position)

# ue_latency = {}

# for phone in latency:
#     df = pd.DataFrame.from_dict(latency[phone])
#     df.to_csv(".\\data\\latency_UE"+str(phone)+".csv", sep=";")

# df = pd.DataFrame(error)
# df.to_csv(".\\data\\error.csv", sep=";")

# for bsi in bs:
#     df = pd.DataFrame.from_dict(prbs[bsi])
#     df.to_csv(".\\data\\resourceblocks_BS"+str(bsi)+".csv", sep=";")
#     df = pd.DataFrame.from_dict(bitrates[bsi])
#     df.to_csv(".\\data\\bitrate_BS"+str(bsi)+".csv", sep=";")
    
# for bsi in bs:
#     df = pd.DataFrame.from_dict(prbs[bsi])
#     df.to_csv("D:/UUDN/wireless-network-simulator-master/data/resourceblocks_BS"+str(bsi)+".csv", sep=";")
#     df = pd.DataFrame.from_dict(bitrates[bsi])
#     df.to_csv("D:/UUDN/wireless-network-simulator-master/data/bitrate_BS"+str(bsi)+".csv", sep=";")



# x = range(ITER)

# plt.xlabel("Simulation time (ms)")
# plt.ylabel("Error")
# plt.title("Error")
# plt.plot(x,error)
# plt.show()

# for phone in ue:

#     latency_dict = {}
#     for elem in latency[phone]:
#         for bsx in elem:
#             if bsx not in latency_dict:
#                 latency_dict[bsx] = []
#             latency_dict[bsx].append(elem[bsx])

    #print(l_2)

    # x = range(ITER)

    # plt.xlabel("Simulation time (ms)")
    # plt.ylabel("Latency")
    # plt.title("Latency for UE " + str(phone))
    # # for i in latency_dict:
    # #     plt.plot(x,latency_dict[i],label = 'id %s'%i)
    # plt.legend()
    # plt.show()
#print(phone1.current_position)
#print(phone2.bs_bitrate_allocation)
#print(phone2.current_position)