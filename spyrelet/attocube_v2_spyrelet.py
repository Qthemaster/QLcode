import numpy as np
import pyqtgraph as pg
import time

from PyQt5.Qsci import QsciScintilla, QsciLexerPython

from spyre import Spyrelet, Task, Element
from spyre.widgets.task import TaskWidget
from spyre.plotting import LinePlotWidget
from spyre.widgets.rangespace import Rangespace
from spyre.widgets.param_widget import ParamWidget
from spyre.widgets.repository_widget import RepositoryWidget

from lantz import Q_

from lantz.drivers.attocube import ANC350

class Attocube(Spyrelet):

    requires = {
        'attocube': ANC350
    }

    @Task(name='set position')
    def set_position(self):
        toggle = self.toggle_params.widget.get()
        pos = self.position_params.widget.get()
        pos0 = pos['axis0_position']
        pos1 = pos['axis1_position']
        pos2 = pos['axis2_position']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.position[0] = pos0
        if toggle1:
            self.attocube.position[1] = pos1
        if toggle2:
            self.attocube.position[2] = pos2

    @Task(name='set amp')
    def set_position(self):
        toggle = self.toggle_params.widget.get()
        amp = self.amp_params.widget.get()
        amp0 = amp['axis0_amp']
        amp1 = amp['axis1_amp']
        amp2 = amp['axis2_amp']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.amplitude[0] = amp0
        if toggle1:
            self.attocube.amplitude[1] = amp1
        if toggle2:
            self.attocube.amplitude[2] = amp2

    @Task(name='set dc')
    def set_position(self):
        toggle = self.toggle_params.widget.get()
        dc = self.dc_params.widget.get()
        dc0 = dc['axis0_dc']
        dc1= dc['axis1_dc']
        dc2 = dc['axis2_dc']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.DCvoltage[0] = dc0
        if toggle1:
            self.attocube.DCvoltage[1] = dc1
        if toggle2:
            self.attocube.DCvoltage[2] = dc2

    
    @Task(name='get position')
    def get_position(self):
        toggle = self.toggle_params.widget.get()
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']
        if toggle0:
            print(self.attocube.position[0])
        if toggle1:
            print(self.attocube.position[1])
        if toggle2:
            print(self.attocube.position[2])


    @Task(name='capacitence')
    def capacitence(self):
        toggle = self.toggle_params.widget.get()
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']
        if toggle0:
            print(self.attocube.capacitance[0])
        if toggle1:
            print(self.attocube.capacitance[1])
        if toggle2:
            print(self.attocube.capacitance[2])

    @Task(name='status')
    def status(self):
        toggle = self.toggle_params.widget.get()
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']
        if toggle0:
            print(self.attocube.status[0])
        if toggle1:
            print(self.attocube.status[1])
        if toggle2:
            print(self.attocube.status[2])

    @Task(name='get Amplitude')
    def get_amp(self):
        toggle = self.toggle_params.widget.get()
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']
        if toggle0:
            print(self.attocube.amplitude[0])
        if toggle1:
            print(self.attocube.amplitude[1])
        if toggle2:
            print(self.attocube.amplitude[2])

    @Task(name='get DCVoltage')
    def get_dc(self):
        toggle = self.toggle_params.widget.get()
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']
        if toggle0:
            print(self.attocube.DCvoltage[0])
        if toggle1:
            print(self.attocube.DCvoltage[1])
        if toggle2:
            print(self.attocube.DCvoltage[2])


    @Task(name='single step')
    def single_step(self):
        toggle = self.toggle_params.widget.get()
        single = self.single_step_params.widget.get()
        single0 = single['axis0_step']
        single1 = single['axis1_step']
        single2 = single['axis2_step']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.single_step(0,single0)
        if toggle1:
            self.attocube.single_step(1,single1)
        if toggle2:
            self.attocube.single_step(2,single2)

    @Task(name='Target Range')
    def target_range(self):
        toggle = self.toggle_params.widget.get()
        target = self.target_params.widget.get()
        target0 = target['axis0_step']
        target1 = target['axis1_step']
        target2 = target['axis2_step']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.set_target_range(0,target0)
        if toggle1:
            self.attocube.set_target_range(1,target1)
        if toggle2:
            self.attocube.set_target_range(2,target2)

    @Task(name='relative move')
    def move(self):
        toggle = self.toggle_params.widget.get()
        move = self.move_params.widget.get()
        move0 = move['axis0_move']
        move1 = move['axis1_move']
        move2 = move['axis2_move']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.move(0,move0) 
        if toggle1:
            self.attocube.move(1,move1)
        if toggle2:
            self.attocube.move(2,move2)

    @set_position.initializer
    def initialize(self):
        print('initializing move...')
        
        return

    @set_position.finalizer
    def finalize(self):
        
        print('finalizing move...')
        return

    @Task(name='jog')
    def jog(self):
        toggle = self.toggle_params.widget.get()
        jog = self.jog_params.widget.get()
        speed0 = jog['axis0_speed']
        speed1 = jog['axis1_speed']
        speed2 = jog['axis2_speed']
        toggle0 = toggle['axis0_toggle']
        toggle1 = toggle['axis1_toggle']
        toggle2 = toggle['axis2_toggle']

        if toggle0:
            self.attocube.jog(0, speed0)
        if toggle1:
            self.attocube.jog(1, speed1)
        if toggle2:
            self.attocube.jog(2, speed2)

    @jog.initializer
    def initialize(self):
        print('initializing jog...')
        
        return

    @jog.finalizer
    def finalize(self):
        
        print('finalizing jog...')
        return

    @Task(name='stop')
    def stop(self):
        self.attocube.stop()

    @stop.initializer
    def initialize(self):
        print('initializing stop...')
        
        return

    @stop.finalizer
    def finalize(self):
        
        print('finalizing stop...')
        return

    @Element(name='select axis')
    def toggle_params(self):
        params = [
        ('axis0_toggle', {'type': bool}),
        ('axis1_toggle', {'type': bool}),
        ('axis2_toggle', {'type': bool}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='positon parameters')
    def position_params(self):
        params = [
        ('axis0_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis1_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis2_position', {'type': float, 'default': 1, 'units': 'um'}),
        ]
        w = ParamWidget(params)
        return w
    
    @Element(name='amp parameters')
    def amp_params(self):
        params = [
        ('axis0_amp', {'type': float, 'default': 1, 'units': 'V'}),
        ('axis1_amp', {'type': float, 'default': 1, 'units': 'V'}),
        ('axis2_amp', {'type': float, 'default': 1, 'units': 'V'}),
        ]
        w = ParamWidget(params)
        return w
    
    @Element(name='dc parameters')
    def dc_params(self):
        params = [
        ('axis0_dc', {'type': float, 'default': 1, 'units': 'V'}),
        ('axis1_dc', {'type': float, 'default': 1, 'units': 'V'}),
        ('axis2_dc', {'type': float, 'default': 1, 'units': 'V'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='move parameters')
    def move_params(self):
        params = [
        ('axis0_move', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis1_move', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis2_move', {'type': float, 'default': 1, 'units': 'um'}),
        ]
        w = ParamWidget(params)
        return w
    
    @Element(name='positon parameters')
    def target_params(self):
        params = [
        ('axis0_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis1_position', {'type': float, 'default': 1, 'units': 'um'}),
        ('axis2_position', {'type': float, 'default': 1, 'units': 'um'}),
        ]
        w = ParamWidget(params)
        return w

    @Element(name='jog parameters')
    def jog_params(self):
        params = [
        ('axis0_speed', {'type': int, 'default': 1,}),
        ('axis1_speed', {'type': int, 'default': 1,}),
        ('axis2_speed', {'type': int, 'default': 1,}),
        ]
        w = ParamWidget(params)
        return w
    
    @Element(name='single step parameters')
    def single_step_params(self):
        params = [
        ('axis0_step', {'type': int, 'default': 1}),
        ('axis1_step', {'type': int, 'default': 1}),
        ('axis2_step', {'type': int, 'default': 1}),
        ]
        w = ParamWidget(params)
        return w


