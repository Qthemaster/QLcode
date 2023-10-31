# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 17:30:07 2023

@author: 86150
"""

import pickle
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

def exp_decreasing(t, a, tau, c):
    return a * np.exp(-t / tau) + c 


def filter_outliers(data, threshold=1.5):
    """
    使用箱线图规则过滤离群值。
    返回过滤后的数据和相应的索引。
    """
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)
    IQR = Q3 - Q1
    lower_bound = Q1 - threshold * IQR
    upper_bound = Q3 + threshold * IQR
    
    filtered_indexes = [i for i, val in enumerate(data) if lower_bound <= val <= upper_bound]
    filtered_data = [data[i] for i in filtered_indexes]
    
    return filtered_data, filtered_indexes

def main():
    # 获取用户输入
    file_path = input("请输入pkl文件的路径: ")
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    raw_PL_data_dict = data['Raw PL data']
    all_wlinputs = sorted(list(set(k[0] for k in raw_PL_data_dict.keys())))
    
    # 打印所有可用的wlinputs
    print("All available wlinputs:", all_wlinputs)
    
    n = int(input("请输入您想要选择的wlinput的数量: "))
    start = float(input("请输入起始目标wlinput: "))
    
    stop = float(input("请输入结束目标wlinput: "))
    
    # 选择n个均匀分布的wlinput
    selected_wlinputs = np.linspace(start, stop, n)

    # 初始化lifetime列表
    lifetimes = []
    selected_wlinput_values = []
    lifetimes_errors = []
    c_values = []  # 保存 c 参数的值
    c_errors = []  # 保存 c 参数的标准误差
    lifetimes_errors = [] 
    
    for target_wlinput in selected_wlinputs:
        closest_wlinput = min(all_wlinputs, key=lambda wl: abs(wl - target_wlinput))

        selected_data = {k: v for k, v in raw_PL_data_dict.items() if k[0] == closest_wlinput}

        sorted_data = sorted(selected_data.items(), key=lambda item: item[0][1])
        filtered_data = dict(sorted_data[20:])
        
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
        
        popt, pcov = curve_fit(exp_decreasing, new_x_data, new_y_data, p0=(max(new_y_data), new_x_data.mean(), min(new_y_data)))
        a, tau, c = popt
        lifetimes.append(tau)
        c_values.append(c)
        
        # 提取参数的标准误差
        perr = np.sqrt(np.diag(pcov))
        lifetimes_errors.append(perr[1])
        c_errors.append(perr[2])
        
        # 画出每次拟合的图
        plt.figure()
        plt.plot(new_x_data, new_y_data, 'bo', label='Data')
        plt.plot(new_x_data, exp_decreasing(new_x_data, *popt), 'r-', label=f'Fit: a={a:.3f}, tau={tau:.3f}, c={c:.3f}')
        plt.title(f'Fitting for wlinput = {closest_wlinput}')
        plt.legend()
        plt.show()
        
        selected_wlinput_values.append(closest_wlinput)
    
    filtered_lifetimes, filtered_indexes = filter_outliers(lifetimes)
    filtered_wlinputs = [selected_wlinput_values[i] for i in filtered_indexes]
    filtered_lifetimes_errors = [lifetimes_errors[i] for i in filtered_indexes]
    filtered_c_values = [c_values[i] for i in filtered_indexes]  # 过滤 c_values
    filtered_c_errors = [c_errors[i] for i in filtered_indexes]  # 过滤 c_errors
    
    # 绘制过滤后的lifetime和c的值
    plt.figure()
    plt.errorbar(filtered_wlinputs, filtered_lifetimes, yerr=filtered_lifetimes_errors, fmt='o', color='b', label='Filtered Lifetime')
    plt.title('Filtered Lifetimes for Selected wlinputs')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Lifetime')
    plt.legend()
    plt.show()
    
    plt.figure()
    plt.errorbar(filtered_wlinputs, filtered_c_values, yerr=filtered_c_errors, fmt='o', color='r', label='c values')  # 修改这里
    plt.title('c values for Selected wlinputs')
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('c value')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    main()