from enum import Enum
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import environment


MIN_RSRP = -85 # -140 dB
c = 3.0*100000000 # speed of the llght
def compute_rsrp(ue, bs, env):
    # 计算路径损耗
    path_loss = Pass_Loss_UMi_LOS_and_NLOS(ue, bs)
    subcarrier_power = 0  # 初始化子载波功率

    # 计算子载波功率
    subcarrier_power = 10*math.log10(bs.antenna_power*1000 / ((bs.total_prb/10)*bs.number_subcarriers))

    # 计算并返回RSRP
    return subcarrier_power + bs.antenna_gain - bs.feeder_loss - path_loss


def Pass_Loss_UMi_LOS_and_NLOS(ue,bs):
    f_c = 3.5
    h_BS = 10
    h_UT = 1.5
    d_2D = math.sqrt((ue.current_position[0]-bs.position[0])**2 + (ue.current_position[1]-bs.position[1])**2)
    if d_2D == 0:   # 避免除以0
        d_2D = 0.01  
    P_LOS = 0.0
    P_L = 0.0
    path_loss = 0.0
    PL_UMi_LOS = 0.0
    PL_UMi_NLOS = 0.0
    h_E = 1.0 #UMi
    g_d2D = 0
    if g_d2D <= 18:
        g_d2D = 0
    if g_d2D <= d_2D:
        g_d2D = 1.25*math.pow((d_2D/100),3)*np.exp(-d_2D/150)
    
    if h_UT < 13:
        C_d2d_and_hUT = 0
    if 13<=h_UT and h_UT<=23:
        C_d2d_and_hUT = math.pow(((h_UT-13)/10),1.5)*g_d2D


        
    probability = 1/(1 + C_d2d_and_hUT)  #TODO need to verify this
    p =  np.random.uniform() # np.random.uniform(0,1) 0-1之间按照均匀分布采样： 0-1 之间的小数
    if p < probability:
        h_E = 1.0 
    else: # a discrete uniform distribution uniform(12,15,…,(hUT-1.5)) ???????????????
        h_E = h_UT - 1.5 
    h_BS_2 = h_BS - h_E
    h_UT_2 = h_UT - h_E
    d_BP_2 = 2*math.pi*h_BS_2*h_UT_2*f_c*c
    d_3D = math.sqrt(math.pow(d_2D, 2)+math.pow(abs(h_BS-h_UT), 2))
    PL_1 = 32.4 + 21*math.log10(d_3D) + 20*math.log10(f_c) 
    PL_2 = 32.4 + 40*math.log10(d_3D) + 20*math.log10(f_c) - 9.5*math.log10(math.pow(d_BP_2,2) + math.pow((h_BS - h_UT),2))
    
    if  10 < d_2D and d_2D <= d_BP_2:
        PL_UMi_LOS = PL_1 + 4
    
    if  d_BP_2 < d_2D and d_2D <= 5*1000:
        PL_UMi_LOS = PL_2 + 4
    
    
    PL_UMi_NLOS_2 = 22.4 + 35.3*math.log10(d_3D) + 21.3*math.log10(f_c) - 0.3*(h_UT - 1.5)
    if 10 < d_2D and d_2D <= 5*1000:
        PL_UMi_NLOS = max(PL_UMi_LOS, PL_UMi_NLOS_2) + 7.82
    
    if d_2D <= 18:
        P_LOS = 1
    if 18 < d_2D:
        P_LOS = 18/d_2D + np.exp(-d_2D/36)*(1-18/d_2D )

    # print("PL_UMi_LOS:", PL_UMi_LOS, "PL_UMi_NLOS:", PL_UMi_NLOS)
    if P_LOS > 0.5:
        P_L = PL_UMi_LOS
    else:
        P_L = PL_UMi_NLOS
    # print("P_L:", P_L)

    if P_L != 0:
        path_loss = 1 / P_L
    else:
    # 处理除以零的情况
        path_loss = 0.1  # 或者其他适当的值

        
    return path_loss


def find_bs_by_id(bs_id):

     return environment.wireless_environment.bs_list[bs_id]
    

def find_ue_by_id(ue_id):
    
    return environment.wireless_environment.ue_list[ue_id]




def plot(ue, bs, env):
    """
    绘制UE（用户设备）和BS（基站）在环境中的位置图。

    参数:
    ue: list，包含UE的ID列表。
    bs: list，包含BS的ID列表。
    env: 环境对象，包含地图限制和其他环境信息。

    无返回值。
    """
    global ax  # 提供对图表子区域的全局访问
    global fig # 提供对图表的全局访问
    global run # 标记图表是否已初始化

    # 初始化图表
    run = 0
    if run == 0:
        plt.ion() # 开启交互模式
        fig, ax = plt.subplots() # 创建子图
        run = 1
    
    x_ue = []
    y_ue = []
    x_bs = []
    y_bs = []
    # 清空当前图表内容
    plt.cla()

    # 定义颜色方案
    colors = cm.rainbow(np.linspace(0, 1, len(bs)))

    # 收集BS和UE的位置信息
    for j in bs:
       

        x_bs.append(find_bs_by_id(j).position[0])
        y_bs.append(find_bs_by_id(j).position[1])

    for i in range(0, len(ue)):
        x_ue.append(find_ue_by_id(ue[i]).current_position[0])
        y_ue.append(find_ue_by_id(ue[i]).current_position[1])

    for j in bs:
        bs_obj = find_bs_by_id(j)

        if bs_obj is not None:
            x_bs.append(bs_obj.position[0])
            y_bs.append(bs_obj.position[1])
        else:
            print("错误: 基站ID {} 未发现.".format(j))

    for i in range(len(ue)):
        ue_obj = find_ue_by_id(ue[i])
        if ue_obj is not None:
            x_ue.append(ue_obj.current_position[0])
            y_ue.append(ue_obj.current_position[1])
        else:
            print("错误: 基站ID {} 未发现.".format(ue[i]))

    # 根据UE当前连接的BS绘制不同颜色的点
    for i in range(0, len(ue)):
        for j in range(0, len(bs)):
            if find_ue_by_id(ue[i]).current_bs == j:
                ax.scatter(x_ue[i], y_ue[i], color = colors[j])
                break
        else:
            # 如果UE没有连接到任何BS，绘制为灰色
            ax.scatter(x_ue[i], y_ue[i], color = "tab:grey")

     # 在UE位置上添加UE的ID
    for i in range(0, len(ue)):
        ax.annotate(str(ue[i]), (x_ue[i], y_ue[i]))

    # 根据BS类型绘制不同标记的BS
    for j in range(0, len(bs)):
        if j < len(x_bs) and j < len(y_bs):
            # 传统基站
            ax.scatter(x_bs[j], y_bs[j], color = colors[j], label = "BS", marker = "s", s = 400)
        else:
            print("Error: Insufficient data to plot base station with ID {}.".format(j))
    
    # 在BS位置上添加BS的ID
    for j in range(0, len(bs)):
        if j < len(x_bs) and j < len(y_bs):
            ax.annotate("BS"+str(j), (x_bs[j], y_bs[j]))
        else:
            print("Error: Insufficient data to plot base station label with ID {}.".format(j))


    # 开启网格线
    ax.grid(True)
    ax.set_ylabel("[m]")
    ax.set_xlabel("[m]")
    # 更新图表显示
    fig.canvas.draw()


    