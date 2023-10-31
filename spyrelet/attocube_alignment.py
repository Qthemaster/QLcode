import numpy as np
import pyqtgraph as pg
import time
import csv
import os
from pathlib import Path
import pickle  # for saving large arrays
import math
from scipy.optimize import minimize
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


from lantz.drivers.thorlabs.pm100d import PM100D

from lantz.drivers.attocube import ANC350
from lantz.log import log_to_screen, DEBUG

class Optimization(Spyrelet):

    requires = {
        'attocube': ANC350,
        'pmd':PM100D
    }

    def get_instrument_parameters(self, movable_axes, mode="position"):
        return np.array([getattr(self.attocube, mode)[axis] for axis in movable_axes])

    def set_instrument_parameters(self, params, movable_axes, mode="position"):
        params_dict = dict(zip(movable_axes, params))
        setattr(self.attocube, mode, params_dict)
        
    def get_instrument_measurement(self):
        return self.pmd.power.magnitude * 1000000
    
    def objective_function(self, params, movable_axes, mode="position"):
        self.set_instrument_parameters(params, movable_axes, mode)
        return -self.get_instrument_measurement()
    
    def grid_search(self, ranges):
        max_power = float('-inf')
        movable_axes = list(ranges.keys())
        best_params = [None for _ in movable_axes]
        
        for axis, range_ in zip(movable_axes, ranges.values()):
            start, stop, num_steps = range_
            for value in np.linspace(start, stop, num_steps):
                trial_params = best_params.copy()
                trial_index = movable_axes.index(axis)
                trial_params[trial_index] = value
                self.set_instrument_parameters(trial_params, [axis])
                power = self.get_instrument_measurement()
                if power > max_power:
                    max_power = power
                    best_params = self.get_instrument_parameters(movable_axes)
        return best_params
    
    def optimize(self, initial_guess, movable_axes, bounds, mode="position"):
        result = scipy.optimize.minimize(
            lambda params: self.objective_function(params, movable_axes, mode),
            initial_guess,
            bounds=bounds,
            method='L-BFGS-B'
        )
        actual_params = self.get_instrument_parameters(movable_axes, mode)
        print(f'Optimal parameters for {mode}: {actual_params}')
        print(f'Maximized power: {self.get_instrument_measurement()}')


    @Task(name="auto-alignment start")
    def optimize_instrument(self):
        axis_status = self.status_params.widget.get()
        axis_range = self.range_params.widget.get()

        ranges = {}
        for i in [0, 1, 2]:
            if axis_status[f'axis{i}_enable')]:
                lower_bound = axis_range[f'axis{i}_lower_bound'].magnitude
                upper_bound = axis_range[f'axis{i}_upper_bound'].magnitude
                num_steps = axis_range[f'axis{i}_numstep']
                
                ranges[i] = (lower_bound, upper_bound, num_steps)
        # Grid search
        initial_guess = self.grid_search(ranges)
        
        # Optimize position
        movable_axes = list(ranges.keys())
        bounds_position = [ranges[axis] for axis in movable_axes]
        self.optimize(initial_guess, movable_axes, bounds_position, mode="position")

        # Optimize DC
        bounds_dc = [(0, 60) for axis in movable_axes]
        self.optimize(initial_guess, movable_axes, bounds_dc, mode="DCvoltage")


    @Element(name='select axis')
    def status_params(self):
        params = [
        ('axis0_enable', {'type': bool}),
        ('axis1_enable', {'type': bool}),
        ('axis2_enable', {'type': bool}),
        ]
        w = ParamWidget(params)
        return w
    
    @Element(name='range parameters')
    def range_params(self):
        params = [
        ('axis0_lower_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis0_upper_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis0_numstep', {'type': int, 'default': 1, }),
        ('axis1_lower_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis1_upper_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis1_numstep', {'type': int, 'default': 1, }),
        ('axis2_lower_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis2_upper_bound', {'type': float, 'default': 1, 'units': 'mm'}),
        ('axis2_numstep', {'type': int, 'default': 1}),
        
        
        ]
        w = ParamWidget(params)
        return w