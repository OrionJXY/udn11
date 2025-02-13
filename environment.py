import UserEquipment as ue
import NRBaseStation as mbs
import util
from concurrent.futures import ThreadPoolExecutor
import math
import random

# 无线环境类定义
class wireless_environment:
    # 类属性，存储基站和用户设备的列表
    bs_list = []
    virtual_cell_list = []
    ue_list = []
    x_limit = None
    y_limit = None

    # 初始化方法
    def __init__(self, n, m , sampling_time ,connectMode):
        # 初始化环境的X和Y轴限制
        if m is not None:
            self.y_limit = m
        else:
            self.y_limit = n
        self.x_limit = n
        self.cumulative_reward = 0              #用于记录累计奖励
        self.sampling_time = sampling_time  #用于设置采样时间
        self.wardrop_epsilon = 0.5 #TODO  
        self.wardrop_beta = 0
        self.connectMode = connectMode


    # 插入用户设备到环境中
    def insert_ue(self, ue_class, starting_position = None, speed = 0, direction = 0,connectMode = 0):
        # 检查UE服务类别是否有效
        if ue_class not in ue.ue_class:
            raise Exception("Invalid service class for the UE, available service classes are: %s" %(ue.ue_class.keys()))
        ue_id = -1  # 初始化UE ID
        # 为新UE寻找空闲的UE ID
        if None in self.ue_list:
            ue_id = self.ue_list.index(None)
        else:
            ue_id = len(self.ue_list)
        # 根据是否指定了初始位置，创建并初始化新UE对象
        if starting_position is None:
            new_ue = ue.user_equipment(ue.ue_class[ue_class], ue_class, ue_id, (random.randint(0, self.x_limit),random.randint(0, self.y_limit),1), self, speed*self.sampling_time, direction,self.connectMode)
        else: 
            new_ue = ue.user_equipment(ue.ue_class[ue_class], ue_class, ue_id, starting_position, self, speed*self.sampling_time, direction,self.connectMode)
        # 将新UE添加到ue_list中
        if (ue_id == len(self.ue_list)):
            self.ue_list.append(new_ue)
        else:
            self.ue_list[ue_id] = new_ue
        return new_ue.ue_id  
     
    
    # 从环境中移除用户设备
    def remove_ue(self, ue_id):
        self.ue_list[ue_id] = None

    
    def place_NR_base_station(self, position, carrier_frequency, numerology, antenna_power, antenna_gain, feeder_loss, available_bandwidth, total_bitrate):
        # 根据载波频率确定频率范围
        fr = -1
        if (carrier_frequency <= 6000):  # 低于6GHz
            fr = 0
        elif (carrier_frequency >= 24250 and carrier_frequency <= 52600): # 在24.25GHz到52.6GHz之间
            fr = 1
        else:
            raise Exception("频率超出允许范围")
        # 检查可用带宽是否符合标准中的数值
        if available_bandwidth in mbs.bandwidth_prb_lookup[numerology][fr]:
             # 计算PRB（物理资源块）大小
             prb_size = 15*(2**numerology)*12 # 根据数值逻辑计算PRB大小
            #  print("prb_size",prb_size)
             new_bs = mbs.BaseStation(
                 len(self.bs_list), 
                 mbs.bandwidth_prb_lookup[numerology][fr][available_bandwidth] * (10 * 2**numerology), 
                 prb_size, 
                 100, 
                 numerology,
                 antenna_power, 
                 antenna_gain, 
                 feeder_loss, 
                 carrier_frequency, 
                 total_bitrate, 
                 position, self)
        else:
             raise Exception("所选带宽在5G NR标准中与该数值和频率范围不符")
        self.bs_list.append(new_bs)
        return new_bs.bs_id

    def discover_bs(self, ue_id):
    # 发现基站功能：通过UE（用户设备）测量，找出对UE信号最好的基站（Base Station，BS）。
    # 参数:ue_id: UE的唯一标识符，用于在UE列表中找到对应的UE。
    # 返回值:
    # - rsrp: 字典类型，键为基站索引，值为对应的RSRP（Reference Signal Received Power，参考信号接收功率）值。
    # 只包含RSRP值大于最小门限的基站。
       thread_pool = []
       #rsrp = [None]*len(self.bs_list)
       # 初始化一个空字典来存储RSRP值，而不是使用列表。字典的键为基站索引，值为RSRP值。
       rsrp = dict()

       # 创建一个线程池，线程数量与基站列表长度相同。
       with ThreadPoolExecutor(max_workers=len(self.bs_list)) as executor:
            # 提交计算RSRP的任务到线程池中，并将每个任务添加到线程池列表中。
            for i in range(0, len(self.bs_list)):
                thread = executor.submit(util.compute_rsrp, self.ue_list[ue_id], self.bs_list[i], self)
                thread_pool.append(thread)
            # 等待所有线程完成计算，并收集结果。
            for i in range(0, len(self.bs_list)):
                res = thread_pool[i].result() 
                #if res > -1000000:
                # 忽略RSRP值小于最小门限的结果。
                if (res > util.MIN_RSRP):
                    rsrp[i] = res
    #    print(rsrp)
        # 返回包含每个符合条件的基站索引及其RSRP值的字典。
       return rsrp
    
    def initial_timestep(self):
       
        # 计算beta值
        self.wardrop_beta = 0
        for ue in self.ue_list:
            rsrp = self.discover_bs(ue.ue_id)  # 发现基站的RSRP（Reference Signal Received Power）
            for elem in rsrp:
                r = util.find_bs_by_id(elem).compute_r(rsrp)  # 计算数据率r
                # 比较并更新wardrop_beta值
                if util.find_bs_by_id(elem).wardrop_alpha/(r/1000000) > self.wardrop_beta:
                    self.wardrop_beta =  util.find_bs_by_id(elem).wardrop_alpha/(r/1000000)
        
        # 调用每个UE的initial_timestep函数，设置初始条件
        for ue in self.ue_list:
            ue.initial_timestep()
        return
       

    
    def next_timestep(self):
        # 检查epsilon是否小于beta乘以UE类别数乘以UE列表长度
        if self.wardrop_epsilon > self.wardrop_beta*ue.ue_class[0]*len(self.ue_list):
            print("Warning: Epsilon is outside the admissible ranges (", self.wardrop_epsilon, "/", self.wardrop_beta*ue.ue_class[0]*len(self.ue_list), ")")
        
        #  遍历UE列表，调用每个UE的next_timestep方法
        for ues in self.ue_list:
            ues.next_timestep()
        # 遍历BS列表，调用每个BS的next_timestep方法
        for bss in self.bs_list:
            bss.next_timestep()

       
    def compute_reward(self, state, action, bitrate, desired_data_rate, rsrp, ue_id):

        if action in rsrp:
            # 根据动作（基站ID）获取连接信息
            allocated, total = util.find_bs_by_id(action).get_connection_info(ue_id)
            alpha = 0
            # 根据UE的服务类别设置alpha值
            if util.find_ue_by_id(ue_id).service_class == 0:
                alpha = 3
            else:
                alpha = 1
            # 如果当前比特率大于期望数据率，根据资源分配情况进行奖励值折扣
            if bitrate > desired_data_rate:
                return alpha * desired_data_rate / (allocated/total)
            else:
                # 如果分配的资源大于0，根据资源分配情况计算奖励值
                if allocated > 0:
                    return alpha * (desired_data_rate**2) * (bitrate - desired_data_rate) #* (allocated/total) * 100
                else:
                    # 如果未分配任何资源，仅基于期望数据率和当前比特率计算奖励值
                    return alpha * (desired_data_rate**2) * (bitrate - desired_data_rate)
        else:
            # 如果动作非法，返回一个极大的负数作为惩罚
            return -10000


    def reset(self, cycle):
        # 重置所有UE的状态
        for ue in self.ue_list:
            ue.reset(cycle)
        # 重置所有BS的状态
        for bs in self.bs_list:
            bs.reset()
        #重置所有UE和BS的状态。参数:cycle: 重置周期，用于UE的重置。返回值:无