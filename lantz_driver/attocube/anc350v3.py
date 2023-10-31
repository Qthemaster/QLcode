from lantz.foreign import LibraryDriver
from lantz import Feat, DictFeat, Action, Q_

import time
from ctypes import c_uint, c_void_p, c_double, pointer, POINTER, c_int

class ANC350(LibraryDriver):

    LIBRARY_NAME = 'anc350v3.dll'
    LIBRARY_PREFIX = 'ANC_'

    RETURN_STATUS = {0:'ANC_Ok', -1:'ANC_Error', 1:"ANC_Timeout", 2:"ANC_NotConnected", 3:"ANC_DriverError",
                     7:"ANC_DeviceLocked", 8:"ANC_Unknown", 9:"ANC_NoDevice", 10:"ANC_NoAxis",
                     11:"ANC_OutOfRange", 12:"ANC_NotAvailable"}

    def __init__(self):
        super(ANC350, self).__init__()

        self.lib.discover.errcheck = ANC350.checkError
        self.lib.connect.errcheck = ANC350.checkError
        self.lib.disconnect.errcheck = ANC350.checkError
        self.lib.getDeviceConfig.errcheck = ANC350.checkError
        self.lib.getAxisStatus.errcheck = ANC350.checkError
        self.lib.setAxisOutput.errcheck = ANC350.checkError
        self.lib.setAmplitude.errcheck = ANC350.checkError
        self.lib.setFrequency.errcheck = ANC350.checkError
        self.lib.setDcVoltage.errcheck = ANC350.checkError
        self.lib.getAmplitude.errcheck = ANC350.checkError
        self.lib.getFrequency.errcheck = ANC350.checkError
        self.lib.startSingleStep.errcheck = ANC350.checkError
        self.lib.startContinousMove.errcheck = ANC350.checkError
        self.lib.startAutoMove.errcheck = ANC350.checkError
        self.lib.setTargetPosition.errcheck = ANC350.checkError
        self.lib.setTargetRange.errcheck = ANC350.checkError
        self.lib.getPosition.errcheck = ANC350.checkError
        self.lib.getFirmwareVersion.errcheck = ANC350.checkError
        self.lib.configureExtTrigger.errcheck = ANC350.checkError
        self.lib.configureAQuadBIn.errcheck = ANC350.checkError
        self.lib.configureAQuadBOut.errcheck = ANC350.checkError
        self.lib.configureRngTriggerPol.errcheck = ANC350.checkError
        self.lib.configureRngTrigger.errcheck = ANC350.checkError
        self.lib.configureRngTriggerEps.errcheck = ANC350.checkError
        self.lib.configureNslTrigger.errcheck = ANC350.checkError
        self.lib.configureNslTriggerAxis.errcheck = ANC350.checkError
        self.lib.selectActuator.errcheck = ANC350.checkError
        self.lib.getActuatorName.errcheck = ANC350.checkError
        self.lib.getActuatorType.errcheck = ANC350.checkError
        self.lib.measureCapacitance.errcheck = ANC350.checkError
        self.lib.saveParams.errcheck = ANC350.checkError


        #Discover systems
        ifaces = c_uint(0x03) # USB interface
        devices = c_uint()
        self.check_error(self.lib.discover(ifaces, pointer(devices)))
        if not devices.value:
            raise RuntimeError('No controller found. Check if controller is connected or if another application is using the connection')
        self.dev_no = c_uint(devices.value - 1)
        self.device = None

        
        return

    def initialize(self, devNo=None):
        if not devNo is None: self.devNo = devNo
        device = c_void_p()
        self.check_error(self.lib.connect(self.dev_no, pointer(device)))
        self.device = device
        self.DCvolt = [0.0, 0.0, 0.0]  # Initialize DCvoltage as an array of three 0.0 values

        # Set the DC voltage for axis 0, 1, and 2 to 0.0
        for axisNo in range(3):
            self.lib.setDcVoltage(self.device, axisNo, c_double(0.0))
        

        

    def finalize(self):
        self.lib.disconnect(self.device)
        self.device = None

    @staticmethod
    def checkError(code, func, args):
        if code != 0:
            raise Exception("Driver Error {}: {} in {} with parameters: {}".format(code, ANC350.RETURN_STATUS[code],str(func.__name__),str(args)))
        return

  
    
    @DictFeat(units='V')
    def DCvoltage(self, axis):
        return self.DCvolt[axis]
        
    @DCvoltage.setter
    def DCvoltage(self, axis, DCvoltage):
        self.DCvolt[axis] = DCvoltage
        self.lib.setDcVoltage(self.device, axis, c_double(DCvoltage))

    @DictFeat(units='V')
    def amplitude(self, axis):
        ret_amplitude = c_double()
        self.check_error(self.lib.getFrequency(self.device, axis, pointer(ret_amplitude)))
        return ret_amplitude.value

    @amplitude.setter
    def amplitude(self, axis, amplitude):
        self.lib.setAmplitude(self.device, axis, c_double(amplitude))

    
        
    
    @DictFeat(units='Hz')
    def frequency(self, axis):
        ret_freq = c_double()
        self.lib.getFrequency(self.device, axis, pointer(ret_freq))
        return ret_freq.value

    @frequency.setter
    def frequency(self, axis, freq):
        self.lib.setFrequency(self.device, axis, freq)
        

    @DictFeat(units='um')
    def position(self, axis):
        ret_pos = c_double()
        self.lib.getPosition(self.device, axis, pointer(ret_pos))
        return ret_pos.value 

    @position.setter
    def position(self, axis, pos):
        self.lib.setTargetPosition(self.device, axis, c_double(pos))
        self.lib.startAutoMove(self.device, axis, 1, 0)
        return
        


    @DictFeat(units='F')
    def capacitance(self, axis):
        ret_c = c_double()
        self.lib.measureCapacitance(self.device, axis, pointer(ret_c))
        return ret_c.value

    @DictFeat()
    def status(self, axis):
        status_names = [
            'connected',
            'enabled',
            'moving',
            'target',
            'eot_fwd',
            'eot_bwd',
            'error',
        ]
        status_flags = [c_uint() for _ in range(7)]
        status_flags_p = [pointer(flag) for flag in status_flags]
        self.lib.getAxisStatus(self.device, axis, *status_flags_p)

        ret = dict()
        for status_name, status_flag in zip(status_names, status_flags):
            ret[status_name] = True if status_flag.value else False
        return ret

    # Untested
    @Action()
    def stop(self):
        for axis in range(3):
            self.lib.startContinousMove(self.device, axis, 0, 1)


    @Action()
    def jog(self, axis, speed):
        backward = bool(speed < 0.0)
        start = bool(speed != 0.0)
        self.lib.startContinousMove(self.device, axis, start, backward)
        return

    @Action()
    def single_step(self, axis, direction):
        backward = direction <= 0
        self.lib.startSingleStep(self.device, axis, backward)
        return

    @Action()
    def move(self, axis, pos):
        self.lib.setTargetPosition(self.device, axis, c_double(pos))
        self.lib.startAutoMove(self.device, axis, 1, 1)
        return


    @Action()
    def set_target_range(self, axis, target_range):
        self.lib.setTargetRange(self.device, axis, target_range)
        return

    
    # ----------------------------------------------

  