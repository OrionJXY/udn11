import environment
import math
from scipy import constants
import util
import pandas as pd
import UserEquipment as ue
from collections import ChainMap

#Table 5.3.3-1: Minimum guardband [kHz] (FR1) and Table: 5.3.3-2: Minimum guardband [kHz] (FR2), 3GPPP 38.104
#表 5.3.3-1：最小保护带 [kHz]（FR1）和表 5.3.3-2：最小保护带 [kHz]（FR2），3GPPP 38.104： 5.3.3-2：最小保护带 [kHz] （FR2），3GPPP 38.104
#number of prb depending on the numerology (0,1,2,3), on the frequency range (FR1, FR2) and on the base station bandwidth
#根据数字（0,1,2,3）、频率范围（FR1、FR2）和基站带宽确定的 prb 数量
bandwidth_prb_lookup = {
    0:[{
        5:25,
        10:52,
        15:79,
        20:106,
        25:133,
        30:160,
        40:216,
        50:8
    }, None],
    1:[{
        5:11,
        10:24,
        15:38,
        20:51,
        25:65,
        30:78,
        40:106,
        50:133,
        60:162,
        70:189,
        80:217,
        90:245,
        100:273
    }, None],
    2:[{
        10:11,
        15:18,
        20:24,
        25:31,
        30:38,
        40:51,
        50:65,
        60:79,
        70:93,
        80:107,
        90:121,
        100:135
    },
    {
        50:66,
        100:132,
        200:264
    }],
    3:[None, 
    {
        50:32,
        100:66,
        200:132,
        400:264
    }]
}

    #属性包括基站 ID (bs_id)、总的物理资源块数 (total_prb)、物理资源块带宽大小 (prb_bandwidth_size)、子载波数目 (number_subcarriers)、
    #波形数（numerology）、天线功率 (antenna_power)、天线增益 (antenna_gain)、馈线损耗 (feeder_loss)、载波频率 (carrier_frequency)、
    #总比特率 (total_bitrate)、位置 (position) 等。

class BaseStation:
   
    def __init__(self, bs_id, total_prb, prb_bandwidth_size, number_subcarriers, numerology, antenna_power, antenna_gain, feeder_loss, carrier_frequency, total_bitrate, position, env):
        self.prb_bandwidth_size = prb_bandwidth_size
        self.total_prb = total_prb
        self.total_bitrate = total_bitrate #Mbps
        self.allocated_prb = 0
        self.allocated_bitrate = 0
        self.antenna_power = antenna_power
        self.antenna_gain = antenna_gain
        self.feeder_loss = feeder_loss
        self.bs_id = bs_id
        self.carrier_frequency = carrier_frequency
        self.fr = -1
       
        
        self.position = (position[0],position[1])
        self.h_b = position[2]
        self.number_subcarriers = number_subcarriers
        self.env = env
        self.numerology = numerology
        self.ue_pb_allocation = {}
        self.ue_bitrate_allocation = {}
        self.T = 10
        self.resource_utilization_array = [0] * self.T
        self.resource_utilization_counter = 0
        if (carrier_frequency <= 6000):  #below 6GHz
            self.fr = 0
        elif (carrier_frequency >= 24250 and carrier_frequency <= 52600): #between 24.25GHz and 52.6GHz
            self.fr = 1
        if(self.antenna_power < 5):
            self.wardrop_alpha = 0.1
        else:
            self.wardrop_alpha = 0.2

    #用于计算基站的资源利用率（Resource Block Utilization，RBUR）。
    def compute_rbur(self):
        # print("compute_rbur = ", sum(self.resource_utilization_array)/(self.T*self.total_prb))
        return sum(self.resource_utilization_array)/(self.T*self.total_prb)
    
   

    #用于根据NR网络的信噪比（SINR）计算需要分配的物理资源块数和传输速率。计算干扰项、热噪声等，最终得到了传输速率 r 和需要的物理资源块数 N_prb
    def compute_r(self, rsrp):#compute SINR
        interference = 0
        for elem in rsrp:
            if elem != self.bs_id and util.find_bs_by_id(elem).carrier_frequency == self.carrier_frequency:
                total, used = util.find_bs_by_id(elem).get_state()
                interference = interference + (10 ** (rsrp[elem]/10))*(used/total)*(self.allocated_prb/self.total_prb) 
        #热噪声的计算公式为 k_b*T*delta_f，其中 k_b 为波尔兹曼常数，T 为开尔文温度，delta_f 为带宽
        thermal_noise= constants.Boltzmann*293.15*list(bandwidth_prb_lookup[self.numerology][self.fr].keys())[list(bandwidth_prb_lookup[self.numerology][self.fr].values()).index(self.total_prb / (10 * 2**self.numerology))]*1000000*(self.compute_rbur()+0.001)      
        # thermal_noise = constants.Boltzmann*293.15*15*(2**self.numerology)*1000 # delta_F = 15*2^mu KHz each subcarrier since we are considering measurements at subcarrirer level (like RSRP)
        sinr = (10**(rsrp[self.bs_id]/10))/(thermal_noise + interference)
        r = self.prb_bandwidth_size*1000*math.log2(1+sinr) #bandwidth is in kHz
        '''假设一个帧的总时长为10毫秒（ms），对于不同子载波间隔参数mu：当mu = 0时，每个PRB在每10ms内占用1ms的时间；当mu = 1时，每个PRB占用0.5ms；当mu = 2时，每个PRB占用0.25ms；当mu = 3时，每个PRB占用0.125ms。'''
        r = r / (10 * (2**self.numerology))
        # with open("D:\\UUDN\\wireless-network-simulator-master\\data\\r.txt", "a") as f:
        #     f.write(str(r) + '\n')
        
        # print("data_rate = ",((self.total_prb - self.allocated_prb)* self.prb_bandwidth_size)*1000*math.log2(1+sinr) / (10 * (2**self.numerology)) /1000000,data_rate)
        return r
    def compute_nprb(self,data_rate, r):
        N_prb = math.ceil(data_rate*1000000 / r) #data rate is in Mbps
        return N_prb
    
    #用于计算基站的信噪比（SINR）
    def compute_sinr(self, rsrp):
        interference = 0
    
        for elem in rsrp:
            if elem != self.bs_id and util.find_bs_by_id(elem).carrier_frequency != self.carrier_frequency:
                interference = interference + (10 ** (rsrp[elem]/10))*util.find_bs_by_id(elem).compute_rbur()
    
        #thermal noise is computed as k_b*T*delta_f, where k_b is the Boltzmann's constant, T is the temperature in kelvin and delta_f is the bandwidth
        thermal_noise = constants.Boltzmann*293.15*list(bandwidth_prb_lookup[self.numerology][self.fr].keys())[list(bandwidth_prb_lookup[self.numerology][self.fr].values()).index(self.total_prb / (10 * 2**self.numerology))]*1000000*(self.compute_rbur()+0.001)
        # thermal_noise = constants.Boltzmann*293.15*15*(2**self.numerology)*1000 # delta_F = 15*2^mu KHz each subcarrier since we are considering measurements at subcarrirer level (like RSRP)
        sinr = (10**(rsrp[self.bs_id]/10))/(thermal_noise + interference)
        
        return sinr
    
    
    

   
    #该方法将由尝试连接该 BS 的 UE 调用。返回值将是分配给用户的实际带宽
    
    def request_connection(self, ue_id, data_rate, rsrp):
        r = self.compute_r(rsrp)
        N_prb= self.compute_nprb(data_rate, r)
        if N_prb > self.total_bitrate/2:
            N_prb = 0
        print("-1  Allocated %s/%s PRB" %(N_prb, self.allocated_prb)) 
        #检查比特率是否足够，如果不够，则不分配给用户
        if self.total_bitrate - self.allocated_bitrate < r*N_prb/1000000:
            dr = self.total_bitrate - self.allocated_bitrate
            N_prb = self.compute_nprb(dr, r)
        if ue_id not in self.ue_bitrate_allocation:
            self.ue_bitrate_allocation[ue_id] = r * N_prb / 1000000  
            self.allocated_bitrate += r * N_prb / 1000000
        else:
            self.allocated_bitrate -= self.ue_bitrate_allocation[ue_id]
            self.ue_bitrate_allocation[ue_id] = r * N_prb / 1000000
            self.allocated_bitrate += r * N_prb / 1000000
            
        #检查是否有足够的 PRB
        if self.total_prb - self.allocated_prb < N_prb:
            N_prb = self.total_prb - self.allocated_prb

        # 分配PRB资源给UE，并更新累计分配的PRB和比特率
        if  ue_id not in self.ue_pb_allocation :
            self.ue_pb_allocation[ue_id] = N_prb
            self.allocated_prb += N_prb
        else :
            self.allocated_prb -= self.ue_pb_allocation[ue_id]
            self.ue_pb_allocation[ue_id] = N_prb
            self.allocated_prb += N_prb 
        
        # print("0  Allocated %s/%s PRB" %(N_prb, self.allocated_prb)) 
        # 返回用户设备的实际数据速率（Mbps）  
        return r*N_prb/1000000 # data rate in Mbps

    #用户请求断开连接，释放已分配的物理资源块数。
    def request_disconnection(self, ue_id):
        N_prb = self.ue_pb_allocation[ue_id]
        self.allocated_prb -= N_prb
        del self.ue_pb_allocation[ue_id]
        # print("断开连接")

    def update_connection(self, ue_id, data_rate, rsrp):
        r = self.compute_r(rsrp)
        N_prb= self.compute_nprb(data_rate, r)
        diff = N_prb - self.ue_pb_allocation[ue_id]
        # print("分配0",ue_id, data_rate,r,N_prb,diff,self.allocated_prb,self.ue_pb_allocation[ue_id],self.allocated_bitrate)

          #检查是否有足够的 PRB
        
        # if diff >= 0 and self.total_prb - self.allocated_prb < diff :
        #     N_prb = self.total_prb - self.allocated_prb

        if  ue_id not in self.ue_pb_allocation and self.total_prb - self.allocated_prb >= N_prb:
            # print("分配1")
            self.ue_pb_allocation[ue_id] = N_prb
            self.allocated_prb += N_prb

        # 检查是否有足够的比特率进行分配
        if  diff > 0 and self.total_bitrate - self.allocated_bitrate  < diff * r / 1000000:
            # print("分配2")
            # 没有足够的比特率
            dr = self.total_bitrate - self.allocated_bitrate
            # N_prb= self.compute_nprb(self.ue_bitrate_allocation[ue_id]+ dr, r)
            N_prb_remain= self.compute_nprb( dr, r)
            diff = N_prb - N_prb_remain - self.ue_pb_allocation[ue_id]
        
       

        if diff > 0 and self.total_prb - self.allocated_prb < diff:
            # print("分配3",ue_id,N_prb,diff)
            # 如果不能分配更多PRB，只能分配可用的最大数量
            diff_remain = self.total_prb - self.allocated_prb
            self.allocated_prb += diff_remain
            self.ue_pb_allocation[ue_id] += diff_remain
            self.allocated_bitrate += diff_remain * r / 1000000
            self.ue_bitrate_allocation[ue_id] += diff_remain * r / 1000000
            diff = diff - diff_remain

        if diff > 0 and self.total_prb - self.allocated_prb >= diff:
            
            # 更新分配的PRB数量和比特率
            self.allocated_prb += diff
            self.ue_pb_allocation[ue_id] += diff
            self.allocated_bitrate += diff * r / 1000000
            self.ue_bitrate_allocation[ue_id] += diff * r / 1000000
            
            print("分配4",ue_id,N_prb,diff,self.allocated_prb,self.ue_pb_allocation[ue_id],self.allocated_bitrate)
            diff = 0 

        # print("2   Allocated %s/%s PRB  diff %s" %(N_prb, self.allocated_prb,diff))  
        return N_prb*r/1000000 # 返回调整后的数据速率（Mbps）
    def next_timestep(self):
      
        # 更新资源利用数组，将当前分配的PRB值记录到数组的下一个位置
        self.resource_utilization_array[self.resource_utilization_counter] = self.allocated_prb
        # print("resource_utilization_array",self.resource_utilization_array)
        self.resource_utilization_counter += 1
        # 检查资源利用计数器是否达到预设的时间间隔T，若是，则重置计数器
        if self.resource_utilization_counter % self.T == 0:
            self.resource_utilization_counter = 0

    def new_state(self):
        return (sum(self.resource_utilization_array) - self.resource_utilization_array[self.resource_utilization_counter] + self.allocated_prb)/(self.total_prb*self.T)
    def get_state(self):
        return self.total_prb, self.allocated_prb
    def get_connection_info(self, ue_id):
        return self.ue_pb_allocation[ue_id]
    def get_connected_users(self):
        return list(self.ue_pb_allocation.keys())
    def reset(self):
        self.resource_utilization_array = [0] * self.T
        self.resource_utilization_counter = 0
    def compute_latency(self, ue_id):
        if ue_id in self.ue_pb_allocation:
            return self.wardrop_alpha * self.ue_pb_allocation[ue_id]
            #return self.wardrop_alpha * self.allocated_prb
        return 0

    def compute_RA(self, rsrp):
        sinr = self.compute_sinr(rsrp)
        user_num = len(self.get_connected_users())
        RA = ((self.total_prb - self.allocated_prb)* self.prb_bandwidth_size)*1000*math.log2(1+sinr) / (10 * (2**self.numerology)) /1000000  /user_num
        
       
        return RA

