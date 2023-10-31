import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle  # for saving large arrays
import math

from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5 import QtCore, QtWidgets
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
import matplotlib.pyplot as plt

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_
import datetime

from lantz.drivers.bristol import Bristol_771
# from lantz.drivers.burleigh import WA7600  # Wavelength meter
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
# from lantz.drivers.agilent import N5181A
from lantz.drivers.windfreak import SynthNV
from lantz.drivers.windfreak import SynthNVPro
# import nidaqmx
# from nidaqmx import AnalogInputTask
from lantz.drivers.thorlabs.pm100d import PM100D
# from lantz.drivers.keysight import Arbseq_Class_MW
from lantz.drivers.keysight import Keysight_33622A
from lantz.drivers.stanford.srs900 import SRS900
# from lantz.drivers.attocube import ANC350

import Pyro5.api
import Pyro5.errors
#import random
from lantz.log import log_to_screen, DEBUG

volt = Q_(1, 'V')
milivolt = Q_(1, 'mV')
Hz = Q_(1, 'Hz')
kHz = Q_(1, 'kHz')
MHz = Q_(1.0, 'MHz')
dB = Q_(1, 'dB')
dBm = Q_(1, 'dB')
s = Q_(1, 's')

class SignalHolder(QObject):
    '''
    This class is used to hold signals. These defination should not be in any spyrelet classes since the signals will not be instantiated
      '''
    update_reference_measurement = pyqtSignal(object)
    #update_temp_reference_measurement = pyqtSignal(object)
    update_transmission_measurement = pyqtSignal(object)
    #update_temp_transmission_measurement = pyqtSignal(object)
    check_the_scanning = pyqtSignal(object)
    update_temp_measurement = pyqtSignal(object)


class Spectrum_Scan(Spyrelet):
    requires = {
        'wm': Bristol_771,
        'pmd':PM100D,
        'fungen': Keysight_33622A,
        # 'SRS': SRS900,
        # 'source': N5181A,
        'windfreak': SynthNVPro
    }
    
    laser = NetworkConnection('169.254.21.75')
    signalholder=SignalHolder()


    #The following objects are use to transmiss different signals between the functions since the Spyrelet Class only defined one signal 

    # update_reference_measurement = pyqtSignal(object)
    # update_temp_reference_measurement = pyqtSignal(object)
    # update_transmission_measurement = pyqtSignal(object)
    # update_temp_transmission_measurement = pyqtSignal(object)


    def homelaser(self, target, measure_time=15, motor_scan_precision=0.0003, precision=0.00004, drift_time=4 * s):
        """
        Motor scan of the Toptica CTL is suitable for large range wavelength adjustments.
        Using motor scan to move wavelength up to plus minus 0.0003nm, beyond this a bit hard, corrections may overshoot
        the wavelength target.
        So we adjust piezo voltage to fine tune wavelength beyond this point.
        In the neighborhood of 70V, 1V increase in piezo voltage changes wavelength by -0.001338nm.
        """
        # with Client(self.laser) as client:
        #     client.set('laser1:dl:pc:enabled', True)
        #     piezo = client.get('laser1:dl:pc:voltage-set')
        #     print('Piezo is at', piezo, 'V.')
        #     if abs(piezo - 70) > 2:
        #         client.set('laser1:dl:pc:voltage-set', 70)
        #         print('Piezo Voltage changed to 70V.')
        #         time.sleep(5)
        # wls = []
        # for i in range(measure_time):
        #     wl = self.wm.measure_wavelength()
        #     wls.append(wl)
        #     time.sleep(1)
        # avg = np.mean(wls)
        # print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)
        #
        # motor_scan = False
        # if abs(avg - target) > motor_scan_precision:
        #     motor_scan = True
        #     with Client(self.laser) as client:
        #         piezo = client.get('laser1:dl:pc:voltage-set')
        #         if piezo != 70:
        #             client.set('laser1:dl:pc:voltage-set', 70)
        #             print('Piezo Voltage changed to 70V.')
        #             time.sleep(5)
        #     current = self.wm.measure_wavelength()
        #     iter = 0
        #     with Client(self.laser) as client:
        #         while current < target - motor_scan_precision or current > target + motor_scan_precision:
        #             # print('here1')
        #             iter = iter + 1
        #             if iter > 6:
        #                 print('Max iteration exceeded.')
        #                 break
        #             setting = client.get('laser1:ctl:wavelength-set', float)
        #             offset = current - target
        #             client.set('laser1:ctl:wavelength-set', setting - offset)  # this uses motor scan.
        #             time.sleep(drift_time.magnitude)
        #             current = self.wm.measure_wavelength()
        #             print(str(iter) + " current: {} target: {} new wl setting: {} diff: {}".format(current, target,
        #                                                                                            round(
        #                                                                                                setting - offset,
        #                                                                                                6), round(
        #                     current - target, 6)))
        #     if iter <= 6:
        #         print("Laser homed to within", motor_scan_precision, 'nm with motor scan.')
        #     else:
        #         print("Laser NOT homed to within", motor_scan_precision, 'nm with motor scan.')
        # if motor_scan:
        #     print('Piezo scan to fine tune wavelength.')
        #     wls = []
        #     for i in range(measure_time):
        #         wl = self.wm.measure_wavelength()
        #         wls.append(wl)
        #         time.sleep(1)
        #     avg = np.mean(wls)
        #     print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)
        # with Client(self.laser) as client:
        #     while avg < target - precision or avg > target + precision:
        #         piezo_adjust = round((avg - target) / 0.001338, 3)
        #         piezo = client.get('laser1:dl:pc:voltage-set')
        #         new_piezo = piezo + piezo_adjust
        #         client.set('laser1:dl:pc:voltage-set', new_piezo)
        #         print('New piezo voltage:', new_piezo, 'V.')
        #         time.sleep(5)
        #         wls = []
        #         for i in range(measure_time):
        #             wl = self.wm.measure_wavelength()
        #             wls.append(wl)
        #             time.sleep(1)
        #         avg = np.mean(wls)
        #         print('Average Wavelength:', avg, 'target:', target, 'diff:', avg - target)
        # return avg

        current = self.wm.measure_wavelength()
        print(current, target, abs(current-target))
        iter = 0
        while current < target - precision or current > target + precision:
            # print('here1')
            iter = iter+1
            if iter > 30:
                print('Max iteration exeeded.')
                break
            with Client(self.laser) as client:
                setting = client.get('laser1:ctl:wavelength-set', float)
                offset = current - target
                client.set('laser1:ctl:wavelength-set', setting - offset)
                time.sleep(drift_time.magnitude)
                current = self.wm.measure_wavelength()
                print(str(iter)+" current: {} target: {} new wl setting: {} diff: {}".format(current, target, round(setting - offset,6), round(current-target,6)))
        print("Laser homed.")
        return current, iter

    def check_laser_lock(self, target, freqs, sample_size=50, precision=5):

        if len(freqs) < 50:
            print('\nLaser lock check: Accumulating statistics')
        else:
            avg = sum(freqs[-sample_size:]) / sample_size
            print("\nLaser lock check: Average: ", avg)
            if precision < abs(avg - target) * 1e3 < 10:
                diff = int((avg - target) * 1e3)  # just correct to 1 MHz
                step = diff / abs(diff)
                print("Diff: {} MHz, Step: {} MHz".format(diff, step))
                with SynthNV('ASRL11::INSTR') as inst:
                    curr_rf = inst.frequency * 1e-3
                    if 300 < curr_rf.magnitude < 600:
                        print("Current synthNV freq: ", curr_rf)
                        for i in range(int(abs(diff))):
                            new_rf = (curr_rf.magnitude - step) * MHz
                            inst.frequency = new_rf
                            time.sleep(1)
                            curr_rf = inst.frequency * 1e-3
                            print("New synthNV freq: ", new_rf, curr_rf)
                        freqs = []
                # actually the adjustment in laser frequency is pretty accurate
                # error signal is shifted by a few MHz and the locking should allow the laser to follow
                # so after adjustment, just get some new statistics so that the average isn't affected
                # by the old data
                # doesn't need to do a while loop and keep adjusting until the wavelength is correct
        return freqs
    
    def lineplot_save(self,x,y,title,xlabel,ylabel,PATH,file_name):

        fig, ax = plt.subplots()


        ax.plot(x, y, color='blue', linestyle='-', marker='o')


        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()

        fig_path = os.path.join(PATH, file_name + ".png")
                
        fig.savefig(fig_path, facecolor='white')

        plt.close(fig)


    def createHistogram(self, stoparray, timebase, bincount, period, index, wls, out_name, extra_data=False):
        print('creating histogram')

        hist = [0] * bincount

        tstart = 0
        for k in range(len(stoparray)):
            tdiff = stoparray[k]

            binNumber = int(tdiff * timebase * bincount / (period))
            """
                print('tdiff: '+str(tdiff))
                print('binNumber: '+str(binNumber))
                print('stoparray[k]: '+str(stoparray[k]))
                print('tstart: '+str(tstart))
                """
            if binNumber >= bincount:
                continue
            else:
                # print('binNumber: '+str(binNumber))
                hist[binNumber] += 1

        if extra_data == False:
            np.savez(os.path.join(out_name, str(index)), hist, wls)
        if extra_data != False:
            np.savez(os.path.join(out_name, str(index)), hist, wls, extra_data)

        # np.savez(os.path.join(out_name,str(index+40)),hist,wls)
        print('Data stored under File Name: ' + out_name + '\\' + str(index) + '.npz')

    def lagrange_interpolation(self, x, y, x_val):
        """
        Second-order Lagrange interpolation for a given x value.
        
        Parameters:
        - x: List of x values for known data points.
        - y: List of corresponding y values for known data points.
        - x_val: The x value at which we want to interpolate the y value.
        
        Returns:
        - Interpolated y value at x_val.
        """
        
        # Calculate and return the interpolated value using the Lagrange interpolation formula
        return y[0] * (x_val - x[1]) * (x_val - x[2]) / ((x[0] - x[1]) * (x[0] - x[2])) + \
            y[1] * (x_val - x[0]) * (x_val - x[2]) / ((x[1] - x[0]) * (x[1] - x[2])) + \
            y[2] * (x_val - x[0]) * (x_val - x[1]) / ((x[2] - x[0]) * (x[2] - x[1]))

    def closest_points(self, x_cor, y_cor, x_val, n=3):
        """
        Find the n closest points to x_val from the given x, y pairs.
        
        Parameters:
        - x: List of x values.
        - y: List of corresponding y values.
        - x_val: The x value to which we want to find the closest points.
        - n: Number of closest points we want to find.
        
        Returns:
        - Tuple of two lists: closest x values, and their corresponding y values.
        """
       
        
        # Compute the absolute distance of each x value from x_val
        distances = np.abs(np.array(x_cor) - x_val)
        # Get the indices of the sorted distances
        indices = np.argsort(distances)[:n]
        return [x_cor[i] for i in indices], [y_cor[i] for i in indices]

   
    @Task()
    def startreferencemeasurement(self, timestep=100e-9):
        log_to_screen(DEBUG)

        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'
        # # some initialization of the function generator
        self.fungen.clear_mem(1)
        self.fungen.clear_mem(2)
        self.fungen.wait()
        # self.fungen.output[2]='OFF'

        # self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
        # time.sleep(3)  ##wait 1s to turn on the SNSPD
        
        time.sleep(1)  # Wait 1s to turn on SNSPD

        expparams = self.exp_parameters.widget.get()
        wlparams = self.wl_parameters.widget.get()

        input_freq_start = wlparams['Laser WL Start']
        input_freq_stop = wlparams['Laser WL Stop']
        input_freq_points = wlparams['Number of Laser WL Point']
        number_of_repeating = expparams['Number of Repeating']
        pulse_channel = expparams['Pulse Channel']
    
        num_AOMs = expparams['# of AOMs']
        WindfreakFreq = expparams['Windfreak frequency'].magnitude  # rf freq to AOMs
        # rf_power = expparams['RF source power']  # replaced by synthNVP_rf_power

        path_name = expparams['File Name']
        c = 299792458  # speed of light, unit: m/s

        '''
        If signal voltage is HIGH, TTL is ON, then RF is sent to fiber AOM's in low insertion loss mode,
        we have excitation laser pulse.
        Frequency of this signal controls the frequency of turning on excitation pulses.
        Length of signal crossing TTL ON threshold determines length of pulse.
        If signal voltage is LOW, TTL is OFF, or isolation state, RF signal does not go through. No laser pulse.
        '''
        # self.fungen.voltage[pulse_channel] = 3.5 * volt  # If don't specify unit fine will just give warning saying it assumed the unit is in Volts.
        self.fungen.offset[pulse_channel] = 1.75 * volt
        self.fungen.phase[pulse_channel] = 0

        # self.fungen.pulse_width[Pulsechannel] = Pulsewidth

        self.fungen.waveform[pulse_channel] = 'DC'
        # self.fungen.output[Pulsechannel] = 'ON'
        self.windfreak.frequency = WindfreakFreq  # set the windfreak frequency to the windfreak frequency
        self.windfreak.output = 1  # turn on the windfreak
        time.sleep(5)  ## wait 5s to turn on the windfreak

        # PATH = path_name + '_' + curr.strftime("%Y-%m-%d_%H-%M-%S")
        # os.mkdir(PATH)
        PATH = path_name
        print('pkl file stored under PATH: ' + str(PATH))

        wl_input_Targets = np.linspace(input_freq_start, input_freq_stop, input_freq_points)
        
        
        pulse_widthTargets=[100e-6]
        laser_power = [100]  # nW; pulse power
        synthNVP_rf_powers = [14.40]  # dBm, controls pulse power
        
        len_wlTargets = len(wl_input_Targets)
        

        for l, power in enumerate(laser_power):
            # with Client(self.laser) as client:
            #     client.set('laser1:power-stabilization:setpoint', power)
            #     power_now = client.get('laser1:power-stabilization:setpoint')
            #     print(l, power_now)

            # use synthNVP to change power of laser while fixing laser output to max
            synthNVP_rf_power = synthNVP_rf_powers[l]
            self.windfreak.power = synthNVP_rf_power  # set the windfreak power
            
            start_time=datetime.datetime.now()
            self.true_laser_wavelength=np.zeros(len_wlTargets)
            self.true_power=np.zeros(len_wlTargets)

            for i, wlinput in enumerate(wl_input_Targets):
                    
                _ = self.homelaser(wlinput, precision=0.0005, drift_time=4 * s)  # home laser to new wl with more precision the first time
                print('Laser set to:' + str(wlinput))

                time.sleep(0.1)    
                coordinate = np.linspace(1,number_of_repeating,number_of_repeating) 
                temp_laser_wavelength_data=np.zeros(number_of_repeating)
                temp_power_data=np.zeros(number_of_repeating)
                self.fungen.output[pulse_channel] = 'ON' 
                for j in range(number_of_repeating):
                        temp_laser_wavelength_data[j]=self.wm.measure_wavelength()
                        # temp_laser_wavelength_data[j]=wlinput+random.random()

                        temp_power_data[j]=self.pmd.power.magnitude*1000000
                        values={
                            'coordinate':coordinate[:j+1],
                            'laser':temp_laser_wavelength_data[:j+1],
                            'power':temp_power_data[:j+1]
                        }
                        self.signalholder.update_temp_measurement.emit(values)
                        time.sleep(0.01)

                self.fungen.output[pulse_channel] = 'OFF'
                self.true_laser_wavelength[i]=c/(c/np.mean(temp_laser_wavelength_data)+num_AOMs * WindfreakFreq / 1e3)
                self.true_power[i]=np.mean(temp_power_data)
                

                results={
                    'wavelength':self.true_laser_wavelength[:i+1],
                    'true_power':self.true_power[:i+1]
                }
                self.signalholder.update_reference_measurement.emit(results)

                wavelength_check={
                    'expect' : wl_input_Targets[:i+1],
                    'real' : self.true_laser_wavelength[:i+1]
                }

                self.signalholder.check_the_scanning.emit(wavelength_check)

                time.sleep(0.1)

                print('Actual wavelength to the sample is:' + str(self.true_laser_wavelength[i]))

                
           
            experiment_setting={"Laser Power" : power,"Input Resolution" : input_freq_points, "Input Start" : input_freq_start, "Input End" : input_freq_stop, "Number of Repeating Measurement": number_of_repeating
                                }
                
            if not (os.path.exists(PATH)):
                print('making new directory...')
                Path(PATH).mkdir(parents=True, exist_ok=True)



            file_name = 'reference_power_measurement_at_' + str(start_time).replace(' ', '_').replace(':', '-')
            full_path = os.path.join(PATH, file_name + ".pkl")

                
            with open(full_path, 'wb') as f:
                pickle.dump({"Laser wavelength":self.true_laser_wavelength,"Power":self.true_power,
                             "Experiment Setup" : experiment_setting}, f)
            print("Data is saved at", full_path)

            self.lineplot_save(x=self.true_laser_wavelength,
                               y=self.true_power,
                               title='Reference Power',
                               xlabel='Wavelength',
                               ylabel='Power',
                               PATH=PATH,
                               file_name=file_name)
            
            self.lineplot_save(x=wl_input_Targets,
                               y=self.true_laser_wavelength,
                               title='Scanning wavelength check',
                               xlabel='Expected',
                               ylabel='Actual',
                               PATH=PATH,
                               file_name='wavelength_check_of_' + file_name)


            time.sleep(2) 
                    
        self.fungen.output[pulse_channel] = 'OFF'
        self.windfreak.output = 0
        #self.SRS.SIM928_on_off[SNSPD_power] = 'OFF'

    @Task()
    def starttransmissionmeasurement(self, timestep=100e-9):
        log_to_screen(DEBUG)

        self.fungen.output[1] = 'OFF'
        self.fungen.output[2] = 'OFF'
        # # some initialization of the function generator
        self.fungen.clear_mem(1)
        self.fungen.clear_mem(2)
        self.fungen.wait()
        # self.fungen.output[2]='OFF'

        # self.SRS.SIMmodule_on[6] ##Turn on the power supply of the SNSPD
        # time.sleep(3)  ##wait 1s to turn on the SNSPD
        
        time.sleep(1)  # Wait 1s to turn on SNSPD

        expparams = self.exp_parameters.widget.get()
        wlparams = self.wl_parameters.widget.get()

        input_freq_start = wlparams['Laser WL Start']
        input_freq_stop = wlparams['Laser WL Stop']
        input_freq_points = wlparams['Number of Laser WL Point']
        number_of_repeating = expparams['Number of Repeating']
        pulse_channel = expparams['Pulse Channel']
    
        num_AOMs = expparams['# of AOMs']
        WindfreakFreq = expparams['Windfreak frequency'].magnitude  # rf freq to AOMs
        # rf_power = expparams['RF source power']  # replaced by synthNVP_rf_power

        path_name = expparams['File Name']
        reference_file_name = expparams['Reference File Name']
        c = 299792458  # speed of light, unit: m/s

        '''
        If signal voltage is HIGH, TTL is ON, then RF is sent to fiber AOM's in low insertion loss mode,
        we have excitation laser pulse.
        Frequency of this signal controls the frequency of turning on excitation pulses.
        Length of signal crossing TTL ON threshold determines length of pulse.
        If signal voltage is LOW, TTL is OFF, or isolation state, RF signal does not go through. No laser pulse.
        '''
        # self.fungen.voltage[pulse_channel] = 3.5 * volt  # If don't specify unit fine will just give warning saying it assumed the unit is in Volts.
        self.fungen.offset[pulse_channel] = 1.75 * volt
        self.fungen.phase[pulse_channel] = 0

        # self.fungen.pulse_width[Pulsechannel] = Pulsewidth

        self.fungen.waveform[pulse_channel] = 'DC'
        # self.fungen.output[Pulsechannel] = 'ON'
        self.windfreak.frequency = WindfreakFreq  # set the windfreak frequency to the windfreak frequency
        self.windfreak.output = 1  # turn on the windfreak
        time.sleep(5)  ## wait 5s to turn on the windfreak

        # PATH = path_name + '_' + curr.strftime("%Y-%m-%d_%H-%M-%S")
        # os.mkdir(PATH)
        PATH = path_name
        print('pkl file stored under PATH: ' + str(PATH))

        wl_input_Targets = np.linspace(input_freq_start, input_freq_stop, input_freq_points)
        
        if os.path.exists(reference_file_name):
            try:
                print("Loading from reference file")
                with open(reference_file_name, 'rb') as file:
                    data = pickle.load(file)
                    reference_wavelength = data["Laser wavelength"]
                    reference_power = data["Power"]
                    if reference_wavelength.shape != reference_power.shape:
                        print("Dimensions of reference_wavelength and reference_power mismatch.")
                        raise InvalidDataFormat()
                    
            except:
                print("Reference file has an incorrect format, please check whether the correct file is loaded!")
                raise InvalidDataFormat()
            results={
                'wavelength' : reference_wavelength,
                'true_power' : reference_power
            }
            self.signalholder.update_reference_measurement.emit(results)          
        else:
            try:
                print("Loading from reference measurement")
                reference_wavelength = self.true_laser_wavelength
                reference_power = self.true_power
            except:
                print("Reference measurement not found, please do reference measurement first!")
                raise MeasureSequenceError()                
                
        
        laser_power = [100]  # nW; pulse power
        synthNVP_rf_powers = [14.40]  # dBm, controls pulse power
        
        len_wlTargets = len(wl_input_Targets)
        

        for l, power in enumerate(laser_power):
            # with Client(self.laser) as client:
            #     client.set('laser1:power-stabilization:setpoint', power)
            #     power_now = client.get('laser1:power-stabilization:setpoint')
            #     print(l, power_now)

            # use synthNVP to change power of laser while fixing laser output to max
            synthNVP_rf_power = synthNVP_rf_powers[l]
            self.windfreak.power = synthNVP_rf_power  # set the windfreak power
            
            start_time = datetime.datetime.now()
            self.true_laser_wavelength_trans = np.zeros(len_wlTargets)
            self.true_power_trans = np.zeros(len_wlTargets)
            self.transmission_rate = np.zeros(len_wlTargets)

            for i, wlinput in enumerate(wl_input_Targets):
                    
                _ = self.homelaser(wlinput, precision=0.0005, drift_time=4 * s)  # home laser to new wl with more precision the first time
                print('Laser set to:' + str(wlinput))

                time.sleep(0.1)    
                coordinate = np.linspace(1,number_of_repeating,number_of_repeating) 
                temp_laser_wavelength_data=np.zeros(number_of_repeating)
                temp_power_data=np.zeros(number_of_repeating)
                self.fungen.output[pulse_channel] = 'ON' 
                for j in range(number_of_repeating):
                        temp_laser_wavelength_data[j]=self.wm.measure_wavelength()
                        #temp_laser_wavelength_data[j]=wlinput+random.random()


                        temp_power_data[j]=self.pmd.power.magnitude*1000000
                        trans_values={
                            'coordinate':coordinate[:j+1],
                            'laser':temp_laser_wavelength_data[:j+1],
                            'power':temp_power_data[:j+1]
                        }
                        self.signalholder.update_temp_measurement.emit(trans_values)
                        time.sleep(0.01)

                self.fungen.output[pulse_channel] = 'OFF'
                self.true_laser_wavelength_trans[i]=c/(c/np.mean(temp_laser_wavelength_data)+num_AOMs * WindfreakFreq / 1e3)
                self.true_power_trans[i]=np.mean(temp_power_data)

                closest_wavelength, closest_power = self.closest_points(reference_wavelength, reference_power, self.true_laser_wavelength_trans[i])
                estimated_power = self.lagrange_interpolation(closest_wavelength, closest_power, self.true_laser_wavelength_trans[i])
                self.transmission_rate[i] = self.true_power_trans[i] / estimated_power
                
                trans_results={
                    'wavelength' : self.true_laser_wavelength_trans[:i+1],
                    'true_power' : self.true_power_trans[:i+1],
                    'transmission_rate' : self.transmission_rate[:i+1]
                }
                self.signalholder.update_transmission_measurement.emit(trans_results)

                wavelength_check={
                    'expect' : wl_input_Targets[:i+1],
                    'real' : self.true_laser_wavelength_trans[:i+1]
                }

                self.signalholder.check_the_scanning.emit(wavelength_check)

                time.sleep(0.1)

                print('Actual wavelength to the sample is:' + str(self.true_laser_wavelength_trans[i]))

                
           
            experiment_setting={"Laser Power" : power,"Input Resolution" : input_freq_points, "Input Start" : input_freq_start, "Input End" : input_freq_stop, "Number of Repeating Measurement": number_of_repeating
                                }
                
            if not (os.path.exists(PATH)):
                print('making new directory...')
                Path(PATH).mkdir(parents=True, exist_ok=True)

            file_name = 'transmission_power_measurement_at_' + str(start_time).replace(' ', '_').replace(':', '-')
            file_name_spectrum = 'transmission_spectrum_at_' + str(start_time).replace(' ', '_').replace(':', '-')
            full_path = os.path.join(PATH, file_name + '.pkl')
                
            with open(full_path, 'wb') as f:
                pickle.dump({"Laser wavelength":self.true_laser_wavelength_trans,"Power":self.true_power_trans,"transmission_rate" : self.transmission_rate,
                             "Experiment Setup" : experiment_setting}, f)
            print("Data is saved at", full_path)

        

            self.lineplot_save(x=self.true_laser_wavelength_trans,
                               y=self.true_power_trans,
                               title='Transmission Power',
                               xlabel='Wavelength',
                               ylabel='Power',
                               PATH=PATH,
                               file_name=file_name)
            
            self.lineplot_save(x=wl_input_Targets,
                               y=self.true_laser_wavelength_trans,
                               title='Scanning wavelength check',
                               xlabel='Expected',
                               ylabel='Actual',
                               PATH=PATH,
                               file_name='wavelength_check_of_' + file_name)
            
            self.lineplot_save(x=self.true_laser_wavelength_trans,
                               y=self.transmission_rate,
                               title='Transmission Spectrum',
                               xlabel='Wavelength',
                               ylabel='Transmission',
                               PATH=PATH,
                               file_name=file_name_spectrum)
            
            time.sleep(2) 
                    
        self.fungen.output[pulse_channel] = 'OFF'
        self.windfreak.output = 0
        #self.SRS.SIM928_on_off[SNSPD_power] = 'OFF'

   



    @Element(name='Wavelength parameters')
    def wl_parameters(self):
        params = [
            
            ('Laser WL Start', {'type': float, 'default': 1500}),
            ('Laser WL Stop',{'type': float, 'default': 1550}),
            ('Number of Laser WL Point', {'type': int, 'default': 3}),
            
        ]
        w = ParamWidget(params)
        return w

    @Element(name='Experiment Parameters')
    def exp_parameters(self):
        params = [
            ('Windfreak frequency', {'type': float, 'default': 200, 'units': 'MHz'}),
            ('# of AOMs', {'type': int, 'default': 3}),
            ('Number of Repeating', {'type': int, 'default': 1000}),
            ('Pulse Channel', {'type': int, 'default': 1}),
            ('File Name', {'type': str, 'default': "E:\\PL on resonant\\transmission test\\test"}),
            ('Reference File Name', {'type': str, 'default': ''})
        ]
        w = ParamWidget(params)
        return w
    

    @startreferencemeasurement.initializer
    def initialize(self):
        self.wm.start_data()
        return

    @startreferencemeasurement.finalizer
    def finalize(self):
        self.fungen.output[1] = 'OFF'  ##turn off the AWG for both channels
        self.fungen.output[2] = 'OFF'
        self.windfreak.output = 0
        self.wm.stop_data()
        print('Lifetime measurements complete.')
        return

    @starttransmissionmeasurement.initializer
    def initialize(self):
        self.wm.start_data()
        return

    @starttransmissionmeasurement.finalizer
    def finalize(self):
        self.fungen.output[1] = 'OFF'  ##turn off the AWG for both channels
        self.fungen.output[2] = 'OFF'
        self.windfreak.output = 0
        self.wm.stop_data()
        print('Lifetime measurements complete.')
        return

    
class Graph(Spyrelet):
    requires_spyrelet = {
        'transmission_spectrum':Spectrum_Scan
     } 
    # Format is spyrelet_name : class_name
     # the 1D plot widget for both the wavelength and power measurement ongoing

    @Element(name="ongoing wavelength measurement")
    def wavelength_measurement(self):
        p = LinePlotWidget()
        p.plot('wavelength measurement',pen=pg.mkPen(color=(255, 0, 0), width=1))
        
        return p

    # update the previous plot
    @wavelength_measurement.on(Spectrum_Scan.signalholder.update_temp_reference_measurement)
    def _wavelength_measurement_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        # xs = np.array(self.bins)[self.cutoff:]
        # ys = np.array(self.hist)[self.cutoff:]
        values = ev.event_args[0]
        coordinate = values['coordinate']
        laser = values['laser']
        
        w.set('wavelength measurement', xs=coordinate, ys=laser)
        
        return

    @Element(name="ongoing power measurement")
    def power_measurement(self):
        p = LinePlotWidget()
        
        p.plot('power measurement',pen=pg.mkPen(color=(0, 0, 255), width=1))
        return p

    # update the previous plot
    @power_measurement.on(Spectrum_Scan.signalholder.update_temp_reference_measurement)
    def _power_measurement_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        # xs = np.array(self.bins)[self.cutoff:]
        # ys = np.array(self.hist)[self.cutoff:]
        values = ev.event_args[0]
        coordinate = values['coordinate']
        
        power = values['power']
       
        w.set('power measurement', xs=coordinate, ys=power)
        return


    
    @Element(name='Reference Power Spectrum')
    def reference_power_spectrum(self):
        p = LinePlotWidget()
        p.plot('Reference Power Spectrum')
        return p

    # update the previous plot
    @reference_power_spectrum.on(Spectrum_Scan.signalholder.update_reference_measurement)
    def _reference_power_spectrum_update(self, ev):
        w = ev.widget
        values = ev.event_args[0]
        laser = values['wavelength']
        power = values['true_power']
        w.set('Reference Power Spectrum', xs=laser, ys=power)
        return

    
    @Element(name='Transmission Power Spectrum')
    def transmission_power_spectrum(self):
        p = LinePlotWidget()
        p.plot('Transmission Power Spectrum')
        return p

    # update the previous plot
    @transmission_power_spectrum.on(Spectrum_Scan.signalholder.update_transmission_measurement)
    def _transmission_power_spectrum_update(self, ev):
        w = ev.widget
        values = ev.event_args[0]
        laser = values['wavelength']
        power = values['true_power']
        w.set('Transmission Power Spectrum', xs=laser, ys=power)
        return

    #the 1D plot widget for reference power spectrum
    @Element(name='Transmission Spectrum')
    def transmission_spectrum(self):
        p = LinePlotWidget()
        p.plot('Transmission Spectrum')
        return p

    # update the previous plot
    @transmission_spectrum.on(Spectrum_Scan.signalholder.update_transmission_measurement)
    def _transmission_spectrum_update(self, ev):
        w = ev.widget
        values = ev.event_args[0]
        laser = values['wavelength']
        rate = values['transmission_rate']
        w.set('Transmission Spectrum', xs=laser, ys=rate)
        return
    
    @Element(name="ongoing scan check")
    def wavelength_check(self):
        p = LinePlotWidget()
        
        p.plot('Wavelength Check',pen=pg.mkPen(color=(0, 0, 255), width=1))
        return p

    # update the previous plot
    @wavelength_check.on(Spectrum_Scan.signalholder.check_the_scanning)
    def _wavelength_check_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        # xs = np.array(self.bins)[self.cutoff:]
        # ys = np.array(self.hist)[self.cutoff:]
        values = ev.event_args[0]
        expect = values['expect']
        
        real = values['real']
        
        w.set('power measurement', xs=expect, ys=real)
        return

class InvalidDataFormat(Exception):
    pass
class MeasureSequenceError(Exception):
    pass
