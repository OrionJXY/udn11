import matplotlib as mpl
import matplotlib.pyplot as plt

# 设置中文字体为黑体（SimHei），同样可按需换为其他字体
mpl.rc('font', family='SimHei')  
# 解决负号显示问题
mpl.rc('axes', unicode_minus=False)  

# 假设这里是3个用户的数据，你可以按照实际情况进行修改和扩展
# 每个子列表中，第一个元素是用户平均速率列表（Mbps），第二个元素是对应的用户满意率列表
# user_data = [
#     ([0,1, 2, 3, 4, 5], [0.98, 0.96, 0.89, 0.87, 0.85,0.79]),  # 用户1的数据
#     ([0,1, 2, 3, 4, 5], [0.95, 0.92, 0.96, 0.89, 0.82,0.70]),  # 用户2的数据
#     ([0,1, 2, 3, 4, 5], [0.85, 0.85, 0.94, 0.87, 0.73,0.55]) , # 用户3的数据
#     ([0,1, 2, 3, 4, 5], [0.80, 0.76, 0.92, 0.82, 0.61,0.45]),
#     ([0,1, 2, 3, 4, 5], [0.99, 0.99, 0.97, 0.93, 0.86,0.78])
# ]

# user_data = [
#     ([1, 2, 3, 4, 5], [0.98, 0.94, 0.90, 0.86, 0.80]),  # 用户1的数据
#     ([1, 2, 3, 4, 5], [0.95, 0.93, 0.91, 0.89, 0.88]),  # 用户2的数据
#     ([1, 2, 3, 4, 5], [0.85, 0.82, 0.79, 0.77, 0.74]) , # 用户3的数据
#     ([1, 2, 3, 4, 5], [0.80, 0.76, 0.71, 0.67, 0.62]),
#     ([1, 2, 3, 4, 5], [0.97, 0.94, 0.93, 0.91, 0.89])
# ]

user_data = [
    ([0, 10, 20, 30, 40,50], [0, 12.4, 24.4, 36, 45.88,51.16]),  #2
    ([0, 10, 20, 30, 40,50], [0, 12.1, 24.1, 36.295, 42.30,46.67]),     #4
    ([0, 10, 20, 30, 40,50], [0, 12, 24,36.0 ,42 ,46]) , #3
    ([0, 10, 20, 30, 40,50], [0, 13, 24, 36.32,48,54]),  #1
    ([0, 10, 20, 30, 40,50], [0, 12, 24,36.2 ,48 ,54])  #5
]
Model = ['R','RaP','Prediction','RSRP','virtual cell'] 
colors = ['red', 'blue', 'green','black','violet']

for i in range(len(user_data)):
    user_rates, user_satisfaction_rates = user_data[i]
    plt.plot(user_rates, user_satisfaction_rates, color=colors[i], label=Model [i ])

# 添加标题和坐标轴标签
#plt.title('User Satisfaction Rate vs User Average Rate for Multiple Users')
# plt.xlabel('User Average Rate (Mbps)')
plt.xlabel('需求速率(M/s)')
plt.ylabel('平均保证速率')

plt.ylim(0, 100) 

# 显示网格线，方便查看数据分布
plt.grid(True)

# 添加图例，显示每条折线对应的用户
plt.legend()

# 设置坐标轴刻度字体大小等，使图形更美观清晰
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# 显示图形
plt.show()