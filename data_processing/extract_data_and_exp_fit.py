# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 15:48:09 2023

@author: 86150
"""

import pickle
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def exp_decreasing(t, a, tau, c):
    return a * np.exp(-t / tau) + c


def main():
    # 获取用户输入
    file_path = input("请输入pkl文件的路径: ")
    
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    raw_PL_data_dict = data['Raw PL data']
    all_wlinputs = set(k[0] for k in raw_PL_data_dict.keys())
    
    # 打印所有可用的wlinputs
    print("All available wlinputs:", all_wlinputs)
    
    target_wlinput = float(input("请输入目标wlinput: "))
    

    # 寻找最接近的wlinput
    all_wlinputs = set(k[0] for k in raw_PL_data_dict.keys())
    closest_wlinput = min(all_wlinputs, key=lambda wl: abs(wl - target_wlinput))

    selected_data = {k: v for k, v in raw_PL_data_dict.items() if k[0] == closest_wlinput}

    # 确保数据是按binpos排序的，然后跳过前20个点
    sorted_data = sorted(selected_data.items(), key=lambda item: item[0][1])
    filtered_data = dict(sorted_data[20:])
    
    # 将键和值分别提取为 numpy array
    x_data = np.array([k[1] for k in filtered_data.keys()])
    y_data = np.array(list(filtered_data.values()))


    # 设定每组的大小
    bin_size = 100
    
    # 计算新的 x_data 和 y_data
    new_x_data = [np.mean(x_data[i:i + bin_size]) for i in range(0, len(x_data), bin_size)]
    new_y_data = [np.sum(y_data[i:i + bin_size]) for i in range(0, len(y_data), bin_size)]
    
    # 转换回 numpy array
    new_x_data = np.array(new_x_data)
    new_y_data = np.array(new_y_data)
    
    # 进行拟合
    popt, pcov = curve_fit(exp_decreasing, new_x_data, new_y_data, p0=(max(new_y_data), new_x_data.mean(), min(new_y_data)))
    
    # 提取寿命（lifetime）
    lifetime = popt[1]
    
    # 输出寿命
    print(f"Extracted lifetime: {lifetime}")
    
    # 绘图
    plt.figure()
    plt.scatter(new_x_data, new_y_data, label='Binned Data')
    plt.plot(new_x_data, exp_decreasing(new_x_data, *popt), 'r-', label=f'Fit: a={popt[0]:.3f}, tau={lifetime:.6f}, c={popt[2]:.3f}')
    plt.title(f'PL Data and Fit at {closest_wlinput:.3f} nm')
    plt.xlabel('Bin coordinate')
    plt.ylabel('Intensity')
    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05))
    plt.show()


if __name__ == "__main__":
    main()
