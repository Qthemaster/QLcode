"""
Laser Control with Adaptive PID

Author: Qian Lin

Overview:
This script introduces an adaptive PID control strategy tailored for a specific laser control system. It includes:

1. AdaptivePID Class:
   An implementation of a self-adapting PID controller. This class not only offers the conventional PID algorithm 
   but also adapts the PID parameters based on the system's response over time.

2. Laser Control Methods:
   - get_avg_wavelength: Computes the average wavelength based on readings from a wavelength meter.
   - adjust_motor_scan: Utilizes the adaptive PID to tweak the motor scan position of the laser, aiming to bring 
   the laser's wavelength closer to a target value.
   - adjust_piezo: Employs the adaptive PID to modify the piezoelectric voltage of the laser, ensuring that the 
   laser's wavelength is closer to the desired value.
   - homelaser: A holistic adjustment procedure that first ensures the laser's piezo control is enabled, then 
   adjusts the laser's wavelength in two stages - first via motor scan and subsequently via piezo adjustment.

3. Decorators:
    - signal_connector: 
    A decorator that facilitates the connection of any function it wraps to a specified PyQt5 signal. 
    This ensures the immediate invocation of the decorated function upon the emission of the connected 
    signal, allowing for intuitive event-driven programming within the Qt framework.

    - status_transfer:
    This decorator aids in transferring the status of a given function. It performs by first waiting until 
    the value inside a specified parameter becomes `False`. When a function is about to execute, it emits a signal 
    indicating the current status and an optional target value if provided. Following the function's execution, 
    another signal is emitted, signifying the function's completion. This provides a real-time monitoring capability, 
    which can be beneficial in GUI applications to display the ongoing status or progress.

    Usage:
    The decorators, when combined with the laser control methods, can add an enhanced layer of interactivity 
    and real-time feedback to the laser control system. Especially when the system is integrated into a GUI, 
    it ensures that users are kept informed about the status and progress of various operations.
   
Purpose:
The script delivers a comprehensive solution for laser control, facilitating real-time adjustments to 
the laser's wavelength to ensure it remains within desired bounds. It achieves its main function through 
interactions with a wavelength meter and the laser system.
"""

from types import NoneType
import numpy as np
from toptica.lasersdk.client import Client
import time
from lantz.drivers.bristol import Bristol_771
from PyQt5.QtCore import pyqtSignal


class AdaptivePID:
    def __init__(self, P, I, D, set_point, min_iterations_for_I_adaptation=10, n_errors_for_adaptation=4, integral_limit=0.5):
        # Initialize PID constants
        self.Kp, self.Ki, self.Kd = P, I, D
        self.set_point = set_point
        
        # Integral term and the previous error term for derivative computation
        self.integral = 0
        self.previous_error = 0
        
        # For adapting Ki after a certain number of iterations
        self.min_iterations_for_I = min_iterations_for_I_adaptation
        
        # Count of iterations to decide when to adapt parameters
        self.iteration = 0
        self.n_errors_for_adaptation = n_errors_for_adaptation
        
        # Store the last 'n' errors to evaluate system performance
        self.last_n_errors = np.zeros(n_errors_for_adaptation)
        
        # Limit for integral term to avoid wind-up
        self.integral_limit = np.array([-integral_limit, integral_limit])
        self.derivative = 0

    def adapt_parameters(self):
        """Adjust the PID parameters based on system performance."""
        
        # Compute relative standard deviation of the recent errors
        avg_error = np.mean(np.abs(self.last_n_errors))
        rsd = np.std(self.last_n_errors) / avg_error if avg_error != 0 else 0
        
        # Compute the relative rate of change of error
        relative_derivative = abs(self.derivative) / abs(self.previous_error) if self.previous_error != 0 else 0

        # Adjust for over-tuning: if errors are consistently increasing
        if np.all(np.abs(0.9*self.last_n_errors) < np.abs(self.previous_error)):
            self.Kp *= 0.9
            
            print(f"Detected over-tuning. Adjusting Kp to {self.Kp}")

        # Adjust for under-tuning
        elif np.all(self.last_n_errors < 0) or np.all(self.last_n_errors > 0):
            self.Kp *= 1.1
            print(f"Detected under-tuning. Adjusting Kp to {self.Kp}")

        # Adjust Kd based on system response and noise level
        

        # Adjust Ki based on integral behavior
        if self.iteration >= self.min_iterations_for_I:
            if np.all(self.last_n_errors > 0) or np.all(self.last_n_errors < 0):
                if abs(self.integral) >= self.integral_limit[1]:
                    self.Ki *= 1.1
                    print(f"Consistent error observed. Adjusting Ki to {self.Ki}")
            elif np.count_nonzero(self.last_n_errors > 0) == len(self.last_n_errors) // 2 and np.abs(self.previous_error) > 0.9 * avg_error:
                self.Ki *= 0.9
                print(f"Oscillating error observed. Adjusting Ki to {self.Ki}")

            if relative_derivative < 0.7:  # threshold for slow response
                self.Kd *= 1.1
                print(f"Relative slow response detected. Adjusting Kd to {self.Kd}")
            else:
                if rsd > 3.5 :  # threshold for high noise
                    self.Kd *= 0.9
                print(f"High relative noise detected. Adjusting Kd to {self.Kd}")


    def compute(self, current_value):
        """Compute the PID output for the given current value."""
        
        # Calculate the difference from set_point
        error = self.set_point - current_value
        
        # Update the integral term
        self.integral += error
        self.integral = np.clip(self.integral, *self.integral_limit)
        
        # Calculate the derivative term
        self.derivative = error - self.previous_error
        
        # Compute the PID output
        output = self.Kp * error + self.Ki * self.integral + self.Kd * self.derivative

        # Update the error history
        self.previous_error = error
        self.last_n_errors = np.roll(self.last_n_errors, -1)
        self.last_n_errors[-1] = error
        self.iteration += 1
        
        # Periodically adapt the PID parameters
        if (2*self.iteration) % self.n_errors_for_adaptation == 0:
            self.adapt_parameters()

        return output

    @staticmethod
    def clamp(value, min_value, max_value):
        """Limit the value between min and max values."""
        return np.clip(value, min_value, max_value)


    
def get_avg_wavelength(wm, measure_time):
    """
    Measures the average wavelength over a specified period of time.
    
    :param wm: Wavelength meter instance for measurement.
    :param measure_time: Number of times to measure.
    :return: The average wavelength measured over the given period.
    """
            
    wls = []
    for _ in range(measure_time):
        wl = wm.measure_wavelength()
        wls.append(wl)
        time.sleep(0.2)  # Wait 200ms to respect the 5Hz measurement rate
    return np.mean(wls)

        

def adjust_motor_scan(laser, wm, target, precision, drift_time, max_iterations,P_m=1.13,I_m=0.5,D_m=0):
    """
    Adjusts the motor scan to achieve a target wavelength with specified precision.
    
    :param laser: Laser controller instance.
    :param wm: Wavelength meter instance for measurement.
    :param target: The target wavelength.
    :param precision: Desired precision for achieving the target wavelength.
    :param drift_time: Time to wait before measuring the wavelength again.
    :param max_iterations: Maximum number of iterations before giving up.
    :param P_m, I_m, D_m: PID controller parameters.
    :return: Number of iterations taken to achieve the target.
    """
    pid = AdaptivePID(P_m, I_m, D_m, target, min_iterations_for_I_adaptation = 10 , integral_limit=0.5)

    with Client(laser) as client:
        iter = 0
        current = wm.measure_wavelength()
        while current < target - precision or current > target + precision:
            iter += 1
            if iter > max_iterations:
                print('Max iteration exceeded.')
                break
            setting = client.get('laser1:ctl:wavelength-set', float)
            adjustment = pid.compute(current)

            new_motor = setting + adjustment
            
            clamped_motor = AdaptivePID.clamp(new_motor, 1490, 1580)

            if clamped_motor != new_motor:
                print(f"Warning: motor was clamped to remain within [1490, 1580] range.")
            client.set('laser1:ctl:wavelength-set', clamped_motor)
            time.sleep(drift_time)
            current = wm.measure_wavelength()
            print(f"{iter} current: {current} target: {target} new wl setting: {setting + adjustment} diff: {current - target}")
        return iter

def adjust_piezo(laser, wm, target, precision, measure_time, drift_time, max_iterations,P_p=0.9,I_p=0.4,D_p=0, iter_limit =0):
    """
    Adjusts the piezo voltage to achieve a target wavelength with specified precision.
    
    :param laser: Laser controller instance.
    :param wm: Wavelength meter instance for measurement.
    :param target: The target wavelength.
    :param precision: Desired precision for achieving the target wavelength.
    :param measure_time: Time interval for average wavelength measurement.
    :param drift_time: Time to wait before measuring the wavelength again.
    :param max_iterations: Maximum number of iterations before giving up.
    :param P_p, I_p, D_p: PID controller parameters.
    :param iter_limit: Limit of iterations regardless of precision.
    :return: Number of iterations taken to achieve the target.
    """
    pid = AdaptivePID(P_p, I_p, D_p, target, min_iterations_for_I_adaptation = 10, integral_limit = 0.0005)
    with Client(laser) as client:
        iter = 0
        avg = get_avg_wavelength(wm, measure_time)
        
        while iter < iter_limit or (avg < target - precision or avg > target + precision):
            iter += 1
            if iter > max_iterations:
                print('Max iteration exceeded for piezo adjustment.')
                break

            piezo = client.get('laser1:dl:pc:voltage-set')
            # The adaptive PID computes the adjustment
            adjustment = pid.compute(avg)
            new_piezo = piezo - round(adjustment / 0.001338, 3)
            
            clamped_piezo_voltage = AdaptivePID.clamp(new_piezo, 30, 110)

            if clamped_piezo_voltage != new_piezo:
                print(f"Warning: Piezo voltage was clamped to remain within [0, 140]V range.")
                        
            client.set('laser1:dl:pc:voltage-set', clamped_piezo_voltage)
            print(f'New piezo voltage: {clamped_piezo_voltage}V.')

            
            time.sleep(np.maximum(drift_time - 0.2 * measure_time, 2))
            avg = get_avg_wavelength(wm, measure_time)
            print(f'{iter} current: Average Wavelength during piezo scan: {avg}nm, target: {target}nm, diff: {avg-target}nm')
        return iter


def homelaser(laser, wm, target, measure_time=15, motor_scan_precision=0.001, precision=0.00002, drift_time=4,P_m=1.13,I_m=0.5,D_m=0,P_p=0.9,I_p=0.4,D_p=0):
    """
    Controls the laser to home in on a target wavelength, adjusting both motor and piezo as needed.
    
    :param laser: Laser controller instance.
    :param wm: Wavelength meter instance for measurement.
    :param target: The target wavelength.
    :param measure_time: Time interval for average wavelength measurement.
    :param motor_scan_precision: Desired precision for motor scan adjustment.
    :param precision: Desired precision for achieving the target wavelength with piezo adjustment.
    :param drift_time: Time to wait before measuring the wavelength again.
    :param P_m, I_m, D_m, P_p, I_p, D_p: PID controller parameters for motor and piezo adjustments respectively.
    :return: Number of iterations taken for both motor and piezo adjustments.
    """
    # Ensure laser's piezo control is enabled
    with Client(laser) as client:
        client.set('laser1:dl:pc:enabled', True)
        piezo = client.get('laser1:dl:pc:voltage-set')
        if abs(piezo - 70) > 2:
            client.set('laser1:dl:pc:voltage-set', 70)
            time.sleep(5)

    avg = get_avg_wavelength(wm, measure_time)
    print(f'Average Wavelength before adjustments: {avg}nm, target: {target}nm, diff: {avg-target}nm')

    motor_iterations = 0
    piezo_iterations = 0

    if abs(avg - target) > motor_scan_precision:
        motor_iterations = adjust_motor_scan(laser, wm, target, motor_scan_precision, drift_time, max_iterations=30,P_m=P_m,I_m=I_m,D_m=D_m)
        avg = get_avg_wavelength(wm, measure_time)
        print(f'Average Wavelength after motor scan: {avg}nm, target: {target}nm, diff: {avg-target}nm')

    piezo_iterations = adjust_piezo(laser, wm, target, precision, measure_time, drift_time, max_iterations=30,P_p=P_p,I_p=I_p,D_p=D_p,iter_limit = 2)
    avg = get_avg_wavelength(measure_time)
    print(f'Final Average Wavelength after piezo adjustment: {avg}nm, target: {target}nm, diff: {avg-target}nm')
    return motor_iterations, piezo_iterations


def signal_connector(signal):
    
    def decorator(func):
        signal.connect(func)
        return func
    return decorator

def status_transfer(param, target_slot, target = None):
    """
    A decorator function to transfer the status of a given function. 
    
    This decorator will:
    1. Wait until the value inside `param` becomes `False`.
    2. Once the function is about to be executed, it emits a signal 
       indicating the function's current status as well as any target value if provided.
    3. After the function finishes its execution, emits another signal 
       indicating the end of its execution.
    
    :param param: A list containing a boolean value. 
                  The function will wait as long as this value remains `True`.
    :param target_slot: The PyQt slot that the signal will connect to.
    :param target: Optional. An initial value to emit before the function execution. 
                   Default is None.
    
    :return: The decorated function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            while param[0]:
                time.sleep(0.1)  

            signal = pyqtSignal(object)
            signal.connect(target_slot)
            if target is not None:
                signal.emit(target)
            signal.emit(True)
            result = func(*args, **kwargs)
            signal.emit(False)
            signal.disconnect()
            del signal 
            return result
        return wrapper
    return decorator

