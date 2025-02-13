import random
import util
import math
import matlab.engine
import heapq
import numpy as np
import csv
import NRBaseStation as mbs
import environment as env
from NRBaseStation import BaseStation
from collections import ChainMap


# 指定均值和标准差
# mean_value = 40
# std_dev = 1  # 标准差可根据需要调整


MAX_STEP = 5
P = 0
matching_indices = 1  # 存储符合条件的行的索引

#"class: Mbps"
ue_class = {
    0:1,
    1: 10,
    2: 20,
    3: 30,
    4: 40,
    5: 50,
    6: 60,
    7: 70
}
ue_class_lambda = {
    0: 1/4000,
    1: 1/15
}

class user_equipment:
    MATLAB = 0
    RANDOM = 1
    epsilon = -1

    def __init__ (self, requested_bitrate, service_class, ue_id, starting_position, env, speed, direction, connectMode):
        self.ue_id = ue_id
        self.requested_bitrate = requested_bitrate
        self.current_position = (starting_position[0], starting_position[1])
        self.pridict_position = (starting_position[0], starting_position[1])
        self.starting_position = (starting_position[0], starting_position[1])
        self.h_m = starting_position[2]
        self.env = env
        self.speed = speed 
        self.direction = direction 
        self.old_position = (starting_position[0], starting_position[1])
        self.old_sevice_class = service_class
        self.service_class = service_class
        # self.lambda_exp = ue_class_lambda[self.service_class]
        self.current_bs = {} # 当前服务的基站信息
        self.actual_data_rate = 0
        self.last_action_t = 0
        self.bs_bitrate_allocation = {}
        self.wardrop_sigma = 0# Wardrop准则相关的变量
        self.last_elapsed_time = None
        self.ue_class = ue_class
        self.connected_bs = set()  # 存储已连接的基站
        self.i = 0  # 初始化计数器为0
        self.next_direction = 0
        self.RA = []
        self.connectMode = connectMode
        
    def move(self):
        if self.RANDOM == 1:
            return self.random_move()
        elif self.RANDOM == 2:
            return self.pridict_move()
        else:
            return self.line_move()

    def random_move(self):
        val = random.randint(1, 4)
        size = random.randint(0, MAX_STEP) 
        if val == 1: 
            if (self.current_position[0] + size) > 0 and (self.current_position[0] + size) < self.env.x_limit:
                self.current_position = (self.current_position[0] + size, self.current_position[1])
        elif val == 2: 
            if (self.current_position[0] - size) > 0 and (self.current_position[0] - size) < self.env.x_limit:
                self.current_position = (self.current_position[0] - size, self.current_position[1])
        elif val == 3: 
            if (self.current_position[1] + size) > 0 and (self.current_position[1] + size) < self.env.y_limit:
                self.current_position = (self.current_position[0], self.current_position[1] + size)
        else: 
            if (self.current_position[1] - size) > 0 and (self.current_position[1] - size) < self.env.y_limit:
                self.current_position = (self.current_position[0], self.current_position[1] - size)


        # print("self.current_position",self.current_position)
        return self.current_position

    def line_move(self):
        new_x = self.current_position[0]+self.speed*math.cos(math.radians(self.direction))
        new_y = self.current_position[1]+self.speed*math.sin(math.radians(self.direction))
        
        #90-degrees bumping
        if new_x <= 0 and new_y <= 0:
            #bottom-left corner
            new_x = 0
            new_y = 0
            self.direction -= 180
        elif new_x <= 0 and new_y >= self.env.y_limit:
            #top-left corener
            new_x = 0
            new_y = self.env.y_limit
            self.direction += 180
        elif new_x >= self.env.x_limit and new_y >= self.env.y_limit:
            #top-right corner
            new_x = self.env.x_limit
            new_y = self.env.y_limit
            self.direction += 180
        elif new_x >= self.env.x_limit and new_y <= 0:
            #bottom-right corner
            new_x = self.env.x_limit
            new_y = 0
            self.direction -= 180
        elif new_x >= self.env.x_limit and self.direction != 90 and self.direction != 270:
            #bumping on the right margin
            new_x = self.env.x_limit
            if self.direction < 90 and self.direction > 0:
                self.direction += 90
            elif self.direction > 270 and self.direction < 360:
                self.direction -= 90
        elif new_x <= 0 and self.direction != 90 and self.direction != 270:
            #bumping on the left margin
            new_x = 0
            if self.direction > 180 and self.direction < 270:
                self.direction += 90
            elif self.direction > 90 and self.direction < 180:
                self.direction -= 90
        elif new_y <= 0 and self.direction != 0 and self.direction != 180:
            #bumping on the bottom margin
            new_y = 0
            self.direction = (360 - self.direction) % 360
        elif new_y >= self.env.y_limit and self.direction != 0 and self.direction != 180:
            #bumping on the top margin
            new_y = self.env.y_limit
            self.direction = (360 - self.direction) % 360

        self.direction = self.direction % 360
        self.current_position = (new_x, new_y)
        return self.current_position
    def pridict_move(self):
    
        with open(f'mapped_data_with_speed.csv', 'r') as file:
            lines = file.readlines()  # 读取文件内容到列表中
            lines = lines[1:]# 跳过第一行

            for row in lines:
                # print("row",row)
                parts = row.split(',')
                if (self.ue_id +1) == float(parts[0]) and self.i == float(parts[5]):
                    mapped_latitude = float(parts[1])
                    mapped_longitude = float(parts[2])
                    direction = float(parts[3])
                    speed = float(parts[4])
                    elapsed_time = float(parts[5])
                    self.direction = direction
                    self.speed = speed 
               
                    # print("用户：",mapped_latitude,mapped_longitude,direction, elapsed_time)

                    self.old_position = self.current_position
                    self.current_position = (mapped_latitude, mapped_longitude)
                       
        self.i += 0.01  # 每次迭代后递增计数器
        # print("用户移动：", self.i,self.old_position,self.current_position,self.speed)
        return self.pridict_position,self.direction,self.speed



    # def do_action(self, t):
        
        # 执行动作函数：根据当前时间和上一次执行动作的时间间隔，以及用户当前的服务状况，
        # 决定是否需要更改服务类别或者与基站的连接状态。

        # 计算在服务类别中花费的时间
        delta_t = (t+1) - (self.last_action_t+1)

        # delta_t = 0  #  初始化时间间隔

        # 检查是否需要基于时间间隔进行服务类别的更改或与基站的连接操作
        if self.last_action_t > 0 and t + 1 - self.last_action_t > 40:
            # 如果当前数据速率远低于请求速率的一半，则断开与基站连接
            if self.actual_data_rate < self.requested_bitrate/2:
                print("断开连接")
                self.disconnect_from_bs()
                return
            else:
            # 如果满足条件，断开当前基站连接并尝试连接到另一个基站
                self.disconnect_from_bs()
                self.connect_to_bs() 
                return
        elif self.last_action_t > 0:
        # 在某些情况下，直接断开与基站的连接并尝试连接到另一个基站
            self.disconnect_from_bs()
            self.connect_to_bs()

        # 计算基于时间间隔的随机概率，以决定是否需要更改服务类别
        prob = 1 - (1 - math.exp(-self.lambda_exp * delta_t))
        # 若随机概率高于预设阈值，则执行服务类别更改
        if random.random() > prob:
            
            # it's time to change service class打印服务类别变更信息
            print("CHANGED SERVICE CLASS: User ID %s has now changed to class %s" %(self.ue_id, self.service_class))
            self.disconnect_from_bs()
            if self.service_class == 0:
                self.service_class = 1
            else:
                self.service_class = 0

            # 更新新的服务类别参数：请求的比特率和lambda值
            # apply new class parameters: requested bitrate, lambda, last action time
            self.requested_bitrate = ue_class[self.service_class]
            self.lambda_exp = ue_class_lambda[self.service_class]
            
            # 更新最后一次动作时间并尝试连接到基站
            self.last_action_t = t + 1
            self.connect_to_bs()


        return
    
   
    def connect_to_bs_id(self, bs_id_list):
        available_bs = self.env.discover_bs(self.ue_id) # 发现可用的BS列表

        for bs_id in bs_id_list :
            data_rate = 0
            if bs_id not in available_bs:
                print("[未发现基站]: 用户ID %s 未发现可用(BS %s)" %(self.ue_id, bs_id))
                
                return self.actual_data_rate
            else :
               
                if bs_id not in self.bs_bitrate_allocation:# 检查是否有为指定基站分配的带宽
                    print("[没有基站分配]: 用户ID %s 选定 (BS %s)未分配比特率" %(self.ue_id, bs_id))
                    return self.actual_data_rate
                # 请求与基站建立连接，并获取分配的数据速率
                if len(self.current_bs) > 5 :
                    break
                elif self.actual_data_rate < (self.requested_bitrate*1.2):
                    if  len(self.current_bs) > 3 :
                        len_bs = len(self.current_bs)
                    else :
                        len_bs = 3
                
                    data_rate = util.find_bs_by_id(bs_id).request_connection(self.ue_id, (self.requested_bitrate*1.2)/len_bs, available_bs)
                    self.current_bs[bs_id] = data_rate
                    self.actual_data_rate += data_rate                
                print("[已建立连接]: 用户ID %s 连接到AP %s 速率为 %s/%s Mbps  虚拟小区大小 %s" %(self.ue_id, bs_id, self.actual_data_rate, self.requested_bitrate,len(self.current_bs)),self.current_bs)
                # return self.actual_data_rate
                if self.actual_data_rate >= self.requested_bitrate*1.2:
                        break
                    
            if self.bs_bitrate_allocation[bs_id] == 0  or data_rate == 0:
                self.disconnect_from_bs(bs_id)
                # del available_bs[bs_id]
            # return self.actual_data_rate 

     
         
        
        return self.actual_data_rate
               
    def get_the_top_bs(self,available_bs):
        if self.connectMode == 1:     #1: 基于RSRP；2：基于SINR与负载 ； 3： 基于位置预测 ；4： 基于位置因子与速率因子 5:半径+负载+预测+业务驱动 ；
            sorted_bs = sorted(available_bs.items(), key=lambda x: x[1], reverse=False)
            top_bs = sorted_bs[:15]   
            top_bs_ids = [bs_tuple[0] for bs_tuple in top_bs]
            return top_bs_ids
        
        elif self.connectMode == 2:  
            sinr = []
            top_bs_positions = []
            for elem in available_bs:
                if util.find_bs_by_id(elem).compute_rbur() == 0:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)))
                else:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)/util.find_bs_by_id(elem).compute_rbur())) 
            sorted_r = sorted(sinr, key=lambda x: x[1], reverse=True)[:15]
            top_bs = [item[0] for item in sorted_r[:15]]   
            return top_bs
        
        elif self.connectMode == 3 :
            sinr = []
            top_bs_positions = []
            for elem in available_bs:
                if util.find_bs_by_id(elem).compute_rbur() == 0:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)))
                else:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)/util.find_bs_by_id(elem).compute_rbur()))           
            sorted_r = sorted(sinr, key=lambda x: x[1], reverse=True)[:15]
            top_bs_ids = [item[0] for item in sorted_r[:15]]
            virtual_cell_ids = self.calculate_virtual_cell(self.current_position, top_bs_ids) #距离最近

            with open("data/virtual_cell.txt", "a") as file:
                file.write("虚拟小区id  %s : %s \n" % (self.ue_id, virtual_cell_ids))
            
            return virtual_cell_ids
    
        elif self.connectMode == 4 :
            # sorted_bs = sorted(available_bs.items(), key=lambda x: x[1], reverse=False)
            # print("sorted_bs",sorted_bs)
            # top_bs = sorted_bs[:15]   
            # top_bs_ids = [bs_tuple[0] for bs_tuple in top_bs]
            # # self.predict_position,self.next_direction, self.speed = self.pridict_move()

            # file_path = r'D:\\UUDN\\wireless-network-simulator-master\\data\\base_station_positions.txt'
            # positions = np.loadtxt(file_path)
            # for bs_idx, bsx in enumerate(positions):
            #     if bs_idx in top_bs_ids:
            #         top_bs_positions.append((bs_idx,bsx))  
            #         virtual_cell_ids = self.calculate_virtual_cell(self.current_position, top_bs_positions) 
            # with open("D:\\UUDN\\wireless-network-simulator-master\\data\\virtual_cell.txt", "a") as file:
            #     file.write("虚拟小区id  %s ： %s \n" % (self.ue_id, virtual_cell_ids))
            sinr = []
            top_bs_positions = []
            for elem in available_bs:
                if util.find_bs_by_id(elem).compute_rbur() == 0:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)))
                else:
                    sinr.append((elem,util.find_bs_by_id(elem).compute_sinr(available_bs)/util.find_bs_by_id(elem).compute_rbur()))           
            sorted_r = sorted(sinr, key=lambda x: x[1], reverse=True)[:15]
            top_bs_ids = [item[0] for item in sorted_r[:15]]
            virtual_cell_ids = self.calculate_virtual_cell(self.current_position, top_bs_ids) 

            with open("data/virtual_cell.txt", "a") as file:
                file.write("虚拟小区id  %s : %s \n" % (self.ue_id, virtual_cell_ids))
    
            return virtual_cell_ids
    # 获取当前位置的向量和角度
    def get_vector_and_angle(self,current_position, bs_position):
        vector = np.array(bs_position) - np.array(current_position)
        distance = np.linalg.norm(vector)
        angle_cos = np.dot([1, 0], vector) / (np.linalg.norm([1, 0]) * distance)
        return distance, angle_cos
    
    # 计算虚拟小区的位置因子和速率因子
    def calculate_virtual_cell(self,current_position, top_bs_ids):
        top_bs_positions = []
        position_factors = []
        record_table = {}
        # file_path = r'data/base_station_positions.txt'
        file_path = r'D:data/base_road.txt' #十字路口
        positions = np.loadtxt(file_path)
        for bs_idx, bsx in enumerate(positions):
            if bs_idx in top_bs_ids:
                top_bs_positions.append((bs_idx,bsx)) 
        for idx,bs_position in top_bs_positions:
            distance, angle_cos = self.get_vector_and_angle(current_position, bs_position)
            position_factors.append((idx,angle_cos, distance))
        sum_distance = np.sum([distance for idx, _,distance in position_factors])
        sum_cos = np.sum([abs(cos) for idx,cos, _ in position_factors])
        
             
        if self.connectMode == 3:
            sorted_indices = sorted(range(len(position_factors)), key=lambda i: position_factors[i][2], reverse=True)
            sorted_position_factors = [position_factors[i] for i in sorted_indices]
            sorted_idx = [idx for idx, _ ,_ in sorted_position_factors]
            return sorted_idx 
 
        elif self.connectMode == 4:
            position_factors = [(idx,(angle_cos / sum_cos) * (np.log(sum_distance / distance))) for idx,angle_cos, distance in position_factors]
            sorted_indices = sorted(range(len(position_factors)), key=lambda i: position_factors[i][1], reverse=True)
            sorted_position_factors = [position_factors[i] for i in sorted_indices]
            sorted_idx = [idx for idx, _ in sorted_position_factors]
            return sorted_idx 
    def disconnect_from_bs(self, bs_id):
        if bs_id in self.current_bs:
            util.find_bs_by_id(bs_id).request_disconnection(self.ue_id)# 向指定的基站请求断开连接
            print("[连接终止]: 用户 ID %s 从基站 %s 断开" %(self.ue_id, bs_id))
            # 更新实际数据速率和删除当前基站记录
            self.actual_data_rate -= self.current_bs[bs_id]
            del self.current_bs[bs_id]
        return
    def disconnect_from_all_bs(self):
        for bs in self.current_bs:
            util.find_bs_by_id(bs).request_disconnection(self.ue_id)
            # print("[连接终止]: 用户 ID %s 从基站 %s 断开" %(self.ue_id, bs))
        self.actual_data_rate = 0
        self.current_bs.clear()

    def update_connection(self):
        available_bs = self.env.discover_bs(self.ue_id) # 发现可用的BS列表
        if len(available_bs) == 0:# 若无可用BS，则记录信息并返回
            print("用户ID %s无可用基站" %(self.ue_id))
            return 0
        
        for elem in self.current_bs: # 如果当前BS仍可用，则更新连接
            if elem in available_bs:
                # print("self.current_bs",elem,self.current_bs[elem])
                if self.current_bs[elem] == 0:
                    print("self.current_bs[elem]",self.current_bs[elem])
                    self.disconnect_from_bs(elem)
                    continue
                if self.current_bs[elem] > (self.requested_bitrate*1.2)/len(self.current_bs):
                   data_rate = util.find_bs_by_id(elem).update_connection(self.ue_id, self.current_bs[elem], available_bs)
                else:
                   data_rate = util.find_bs_by_id(elem).update_connection(self.ue_id, (self.requested_bitrate*1.2)/len(self.current_bs), available_bs)
                self.actual_data_rate -= self.current_bs[elem]
                self.current_bs[elem] = data_rate
                self.actual_data_rate += self.current_bs[elem]

                if self.actual_data_rate < (self.requested_bitrate)*1.1:# 更新与BS的数据速率
                    self.actual_data_rate -= self.current_bs[elem]
                    self.current_bs[elem] = data_rate
                    self.actual_data_rate += self.current_bs[elem]
                    print("[当前AP 速率低]:用户 ID %s 在连接更新期间未找到其基站" %(self.ue_id))
            else:
                print("[当前AP不再可用]:用户 ID %s 在连接更新期间未找到其基站" %(self.ue_id))
                self.disconnect_from_bs(elem)# 如果当前AP不再可用，则断开连接并尝试连接到其他AP
            print("[更新连接]: 用户ID %s连接到AP %s 速率为 %s/%s Mbps  负载: %s" %(self.ue_id, elem, self.current_bs[elem], self.requested_bitrate*1.2,util.find_bs_by_id(elem).compute_rbur()))

                #TODO update the connections according to the newly computed requested bitrates coming from the next_timestep() function
        if self.actual_data_rate < 1.1*(self.requested_bitrate) and len(self.current_bs) < 6:
            bs_list = []
            bs_id_list = self.get_the_top_bs(available_bs)
            # self.disconnect_from_all_bs()
            for bs_id in bs_id_list:
                if bs_id not in self.current_bs and len(self.current_bs) < 5:
                    if len(self.current_bs) >3:
                        len_bs = len(self.current_bs)
                    else :
                        len_bs = 3
                    if self.actual_data_rate < (self.requested_bitrate)*1.2:
                        print("【信号弱的基站】：用户 ID %s 连接质量差（实际 速率为 %s/%s Mbps）")
                        
                        self.connect_to_bs_id(bs_list)

                    else :
                        break 

                if len(self.current_bs) > 5 and self.actual_data_rate < (self.requested_bitrate)*1.1:
                    print("【信号弱的基站】：用户 ID %s 连接质量差（实际 速率为 %s/%s Mbps）" %(self.ue_id, self.actual_data_rate, self.requested_bitrate*1.2))
                   

                    # bitrate_per_bs = self.requested_bitrate / len(self.current_bs)# 计算每个基站的比特率分配
                    # for bs_id in self.current_bs:
                    #     self.bs_bitrate_allocation[bs_id] = bitrate_per_bs
                    #     util.find_bs_by_id(bs_id).request_connection(self.ue_id, self.bs_bitrate_allocation[bs_id], available_bs)
                    #     util.find_bs_by_id(elem).update_connection(self.ue_id, self.bs_bitrate_allocation[bs_id], available_bs)       
                   
        
        # with open("D:\\UUDN\\wireless-network-simulator-master\\data\\dataconnection_logs.txt", "a") as file:
        #     for elem in self.current_bs:
        # print("[更新连接]: 用户ID %s连接到AP %s 速率为 %s/%s Mbps" %(self.ue_id, elem, self.current_bs[elem], self.bs_bitrate_allocation[elem]))
        
        #         connection_info = "[更新连接]: 用户ID %s连接到AP %s 速率为 %s/%s Mbps\n" %(self.ue_id, elem, self.current_bs[elem], self.bs_bitrate_allocation[elem])
        #         file.write(connection_info)
        
        return self.current_bs

    def initial_timestep(self):
        self.move()  # 移动到下一个位置
        rsrp = self.env.discover_bs(self.ue_id)# 从环境中发现UE所在的基站，并获取其RSRP值
    
        # print("len(self.current_bs):",len(self.current_bs))
        for elem in rsrp:
            if len(self.current_bs) == 0 :
                self.bs_bitrate_allocation[elem] = self.requested_bitrate/3
            if len(self.current_bs) != 0 :
                self.bs_bitrate_allocation[elem] = self.requested_bitrate/len(self.current_bs)
            if elem not in self.bs_bitrate_allocation:
                self.bs_bitrate_allocation[elem] = 0   #/(n-1)# 遍历所有RSRP值，为未分配比特率的基站初始化分配值为0
        
        # compute wardrop sigma 用于平衡负载
        self.wardrop_sigma = (self.env.wardrop_epsilon)/(2*self.env.sampling_time*self.env.wardrop_beta*self.requested_bitrate*(len(rsrp)-1)*len(self.env.ue_list))
        return

    def next_timestep(self):
        # self.old_position = self.current_position  # 保存当前位置为旧位置
        self.move()  # 移动到下一个位置
        rsrp = self.env.discover_bs(self.ue_id) # 根据当前UE的位置，计算下一个时间步长的可见基站RSRP值

        for elem in rsrp:
            if elem not in self.bs_bitrate_allocation:
                self.bs_bitrate_allocation[elem] = 0 # 添加新的基站

        # 使用Wardrop算法优化比特率分配
        for p in self.bs_bitrate_allocation:
            for q in self.bs_bitrate_allocation:
                if p != q:
                    # 计算基站p和q到UE的延迟
                    bs_p = util.find_bs_by_id(p)
                    l_p = bs_p.compute_latency(self.ue_id)

                    bs_q = util.find_bs_by_id(q)
                    l_q = bs_q.compute_latency(self.ue_id)
                    
                    # 根据延迟差异和基站状态更新比特率分配
                    mu_pq = 1
                    if (l_p - l_q) < self.env.wardrop_epsilon or bs_q.allocated_bitrate >= bs_q.total_bitrate - (self.env.wardrop_epsilon/(2*self.env.wardrop_beta)):
                        mu_pq = 0
                    
                    mu_qp = 1
                    if (l_q - l_p) < self.env.wardrop_epsilon or bs_p.allocated_bitrate >= bs_p.total_bitrate - (self.env.wardrop_epsilon/(2*self.env.wardrop_beta)):
                        mu_qp = 0

                    # 根据更新系数调整比特率分配
                    r_pq = self.bs_bitrate_allocation[p]*mu_pq*self.wardrop_sigma
                    r_qp = self.bs_bitrate_allocation[q]*mu_qp*self.wardrop_sigma

                    # 更新p基站的比特率分配
                    
                    self.bs_bitrate_allocation[p] += self.env.sampling_time * (r_qp - r_pq)  

        return

    def reset(self, t):
        self.disconnect_from_all_bs()
        self.actual_data_rate = 0
        self.current_position = self.starting_position
        self.service_class = self.old_sevice_class
        self.lambda_exp = ue_class_lambda[self.service_class]
        self.requested_bitrate = ue_class[self.service_class]
        self.last_action_t = t
