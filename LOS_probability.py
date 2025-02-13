#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   LOS_probability.py
@Time    :   2022/06/13
@Author  :   LuDaYong
@Version :   1.0
@parameter: 
'''


import numpy as np
import math
import cmath


c = 3.0*100000000 # speed of the llght

#LOS probability (distance is in meters)
def Pr_LOS_UMi(d_2D_out): # d_2D_out,d_2D,f_c,h_BS = 25,h_UT = 1.5,h = 5,W = 20

    if d_2D_out <= 18:
        Pr_LOS = 1
    if 10 < d_2D_out:
        Pr_LOS = 18/d_2D_out + np.exp(-d_2D_out/36)*(1-18/d_2D_out )
    return Pr_LOS


def Pr_LOS_UMa(d_2D_out,h_UT = 1.5):
    
    C_h_UT = 0
    if h_UT <= 13:
        C_h_UT = 0
    if 13 < h_UT and h_UT <= 23:
        C_h_UT = math.pow((h_UT-13)/100,1.5)

    if d_2D_out <= 18:
        Pr_LOS = 1
    if 10 < d_2D_out:
        Pr_LOS = (18/d_2D_out + np.exp(-d_2D_out/63)*(1-18/d_2D_out))*(1 + 1.25*C_h_UT*math.pow(d_2D_out/100,3)*np.exp(-d_2D_out/150))
    return Pr_LOS


#Note:	The LOS probability is derived with assuming antenna heights of 3m for indoor, 10m for UMi, and 25m for UMa
    
    

if __name__=='__main__':
    pass