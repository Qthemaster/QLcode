import numpy as np
import pyqtgraph as pg
import time
import csv
from lantz import Q_

import matplotlib.pyplot as plt
import datetime
from scipy.constants import c

from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtWidgets import QPushButton, QTextEdit, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, Qt, pyqtSlot

from LaserControl import adjust_piezo, get_avg_wavelength

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

###Import lantz drivers files for all instruments you use.
# e.g.
# from lantz.drivers.keysight import Keysight_33622A
# The above line will import the AWG driver
from toptica.lasersdk.client import NetworkConnection, Client, SerialConnection
from lantz.log import log_to_screen, DEBUG
from lantz.drivers.bristol import Bristol_771  # Wavelength meter


nm = Q_(1, 'nm')
s = Q_(1, 's')
THz = Q_(1.0, 'THz')
Hz = Q_(1, 'Hz')
dBm = Q_(1, 'dB')
mW = Q_(1, 'mW')

class StabilizerSignalHolder():
    signal=pyqtSignal(bool) 

class WavelengthStabilizer(Spyrelet):
    requires = {
        'wm': Bristol_771
    }

    laser = NetworkConnection('169.254.21.75')

    status = True

    signalholder=StabilizerSignalHolder()
    target = None

    @pyqtSlot(bool)
    @pyqtSlot(float)
    def update_stabilizer_status(self, value):
        if isinstance(value, bool):
            self.status = value

        elif isinstance(value, float):
            self.target = value



    @Task()
    def enable_stabilize(self):
        #log_to_screen(DEBUG)

        stabilizerparams = self.stabilizer_params.widget.get()

        trigger = stabilizerparams['Critical Accuracy']
        precision = stabilizerparams['Precision']

        while True:
            if self.status:
                time.sleep(1)
            else:
                self.signalholder.signal.emit(True)
                if self.target is None:
                    self.target = get_avg_wavelength(self.wm, 30)
                current = get_avg_wavelength(self.wm, measure_time=15)
                if abs(current - self.target) > trigger :
                    adjust_piezo(self.laser, self.wm, self.target, precision, measure_time=15, drift_time=4, max_iterations=20)
                self.signalholder.signal.emit(False)

    @Task()
    def plot_wavelength(self):
        count = []
        wavelength = []
        t = 0
        while True:
            count.append(t)
            wavelength.append(self.wm.measure_wavelength())
            values={
            'time': np.array(count),
            'wavelength' : np.array(wavelength)

            }

            self.plot_wavelength.acquire(values)
            t+=1
            
            time.sleep(0.2)

    @Element(name="ongoing wavelength check")
    def wavelength_check(self):
        p = LinePlotWidget()
        
        p.plot('Wavelength Check',pen=pg.mkPen(color=(0, 0, 255), width=1))
        return p

    # update the previous plot
    @wavelength_check.on(plot_wavelength.acquired)
    def _wavelength_check_update(self, ev):
        w = ev.widget
        # cut off pulse in display
        # xs = np.array(self.bins)[self.cutoff:]
        # ys = np.array(self.hist)[self.cutoff:]
        values = ev.event_args[0]
        expect = values['time']
        
        real = values['wavelength']
        
        w.set('Wavelength Check', xs=expect, ys=real)
        return


    @Element(name='Piezo scan parameters')
    def stabilizer_params(self):
        params = [
            ('Critical Accuracy', {'type': float, 'default': 0.0001}),
            ('Precision',{'type': float, 'default': 0.00002})
        ]

        w = ParamWidget(params)
        return w

    @enable_stabilize.initializer
    def initialize(self):
        print('Start wavelength stabilizing...')

    @enable_stabilize.finalizer
    def finalize(self):
        print('Done.')
        return
