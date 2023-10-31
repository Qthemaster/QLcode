# -*- coding: utf-8 -*-
"""
Created on Wed Oct  4 18:05:16 2023

@author: 86150
"""


from scipy.optimize import minimize, curve_fit
import pickle
import matplotlib.pyplot as plt
import numpy as np

def exp_decreasing(t, a, tau, c):
    return a * np.exp(-t / tau) + c

def objective(params, x_data_list, y_data_list):
    global_c = params[-1]  # 最后一个参数是共享的 c
    error_sum = 0
    
    for i in range(len(x_data_list)):
        a = params[i*2]
        tau = params[i*2 + 1]
        error = y_data_list[i] - exp_decreasing(x_data_list[i], a, tau, global_c)
        error_sum += np.sum(error**2)
    
    return error_sum

def main():
    # 获取用户输入
    file_path = input("请输入pkl文件的路径: ")
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)

    raw_PL_data_dict = data['Raw PL data']
    total_PL_data_dict = data['Total PL data']
    all_wlinputs = sorted(list(set(k[0] for k in raw_PL_data_dict.keys())))
    
    print("All available wlinputs:", all_wlinputs)
    
    n = int(input("请输入您想要选择的wlinput的数量: "))
    start = float(input("请输入起始目标wlinput: "))
    stop = float(input("请输入结束目标wlinput: "))
    
    selected_wlinputs = np.linspace(start, stop, n)
    
    initial_guess = []
    x_data_list = []
    y_data_list = []
    selected_wlinput_values = []

    for target_wlinput in selected_wlinputs:
        closest_wlinput = min(all_wlinputs, key=lambda wl: abs(wl - target_wlinput))
        selected_data = {k: v for k, v in raw_PL_data_dict.items() if k[0] == closest_wlinput}
        sorted_data = sorted(selected_data.items(), key=lambda item: item[0][1])
        filtered_data = dict(sorted_data[20:])
        x_data = np.array([k[1] for k in filtered_data.keys()])
        y_data = np.array(list(filtered_data.values()))
        bin_size = 100
        new_x_data = [np.mean(x_data[i:i + bin_size]) for i in range(0, len(x_data), bin_size)]
        new_y_data = [np.sum(y_data[i:i + bin_size]) for i in range(0, len(y_data), bin_size)]
        new_x_data = np.array(new_x_data)
        new_y_data = np.array(new_y_data)
        
        x_data_list.append(new_x_data)
        y_data_list.append(new_y_data)
        initial_guess.extend([max(new_y_data), new_x_data.mean()])
        selected_wlinput_values.append(closest_wlinput)
    
    initial_guess.append(min(min(y) for y in y_data_list))
    result = minimize(objective, initial_guess, args=(x_data_list, y_data_list), method='BFGS')
    final_params = result.x

    # Extract the optimized parameters and plot
    global_c = final_params[-1]
    lifetimes = []
    wlinputs = []
    tau_errors = []
    PL_data = []
    
    for i in range(len(x_data_list)):
        a_init = final_params[i*2]
        tau_init = final_params[i*2 + 1]
        popt, pcov = curve_fit(lambda t, a, tau: exp_decreasing(t, a, tau, global_c), 
                               x_data_list[i], y_data_list[i], p0=[a_init, tau_init])
        a, tau = popt
        lifetimes.append(tau)
        wlinputs.append(selected_wlinput_values[i])
        tau_error = np.sqrt(np.diag(pcov))[1]  # 提取tau参数的标准误差
        tau_errors.append(tau_error)
        
    # Now plot lifetimes against wlinputs with error bars
    fig, ax1 = plt.subplots()
    ax1.errorbar(wlinputs, lifetimes, yerr=tau_errors, fmt='o', color='b', label='Filtered Lifetime')
    ax1.set_title('Lifetime and PL vs Wavelength')
    ax1.set_xlabel('Wavelength (nm)')
    ax1.set_ylabel('Lifetime', color='b')
    ax1.tick_params('y', colors='b')

    # Extract and plot PL data
    ax2 = ax1.twinx()  # instantiate a second y-axis sharing the same x-axis

    for wlinput in wlinputs:
        closest_wlinput = min(all_wlinputs, key=lambda wl: abs(wl - wlinput))
        PL_value = total_PL_data_dict.get(closest_wlinput)  # Assuming the keys are tuples of (wlinput, wlinput)
        PL_data.append(PL_value)

    ax2.plot(wlinputs, PL_data, 'r-', label='PL Data')
    ax2.set_ylabel('PL Data', color='r')
    ax2.tick_params('y', colors='r')

    fig.tight_layout()  # to ensure the right y-label is not slightly clipped
    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.show()
    
    for i in range(len(x_data_list)):
        plt.figure()
        x_data = x_data_list[i]
        y_data = y_data_list[i]
        a = final_params[i*2]
        tau = final_params[i*2 + 1]
        plt.scatter(x_data, y_data, label='Data')
        plt.plot(x_data, exp_decreasing(x_data, a, tau, global_c), label='Fit', color='r')
        plt.title(f'Fit for Wavelength {wlinputs[i]:.1f} nm')
        plt.xlabel('X Data')
        plt.ylabel('Y Data')
        plt.legend()
        plt.show()
        
    print(f'The background value is : {global_c:.2f}')

if __name__ == "__main__":
    main()