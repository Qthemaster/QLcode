from lantz import Driver
from lantz import Feat, DictFeat, Action, Q_
import time
from PyANC350v3 import Positioner
from ANC350libv3 import checkError
class ANC350(Driver):
    
    MAX_RELATIVE_MOVE = Q_(10e-6, 'um')
    MAX_ABSOLUTE_MOVE = Q_(40, 'um')

    def __init__(self):
        self.positioner = Positioner()
        # Discover systems
        devices = self.positioner.discover()
        if not devices:
            raise RuntimeError('No controller found. Check if controller is connected or if another application is using the connection')
        # Connect to the first discovered device
        self.positioner.connect(devices[0])
        super(ANC350, self).__init__()

    def initialize(self, device_address = None):
        # Connect to the provided device address
        if not device_address is None: self.devNo = device_address
        error_code = self.positioner.connect(device_address)
        ANC350libv3.checkError(error_code, 'connect', [device_address])
        # Wait until we get a non-zero position
        while self.position(axis=2) == Q_(0, 'um'):
            time.sleep(0.025)
    def finalize(self):
        self.positioner.disconnect()

    def __init__(self):
        self.positioner = Positioner()
        super(ANC350, self).__init__()
        #Discover systems
        if not devices.value:
            raise RuntimeError('No controller found. Check if controller is connected or if another application is using the connection')
                        # Function definitions
        return
    def initialize(self, devNo=None):
        if not devNo is None: self.devNo = devNo
        #Wait until we get something else then 0 on the position
            # Wait until we get a non-zero position
        while self.position(axis=2) == Q_(0, 'um'):
            time.sleep(0.025)

    def finalize(self):
        return self.positioner.disconnect()
    @DictFeat(units='Hz')
    def frequency(self, axis):
        return self.positioner.getFrequency(self.device, axis)
    @frequency.setter
    def frequency(self, axis, freq):
        return self.positioner.setFrequency(self.device, axis, freq)
    @DictFeat(units='um')
    def position(self, axis):
        return self.positioner.getPosition(self.device, axis) 
    @position.setter
    def position(self, axis, pos):
        return self.absolute_move(axis, pos)
    @DictFeat(units='F')
    def capacitance(self, axis):
        return self.positioner.measureCapacitance(self.device, axis)

    @DictFeat()
    def status(self, axis):
        # Placeholder implementation, needs to be implemented based on pyanc350 methods
        return {
            "connected": True,
            "enabled": True,
            "moving": False,
            "target": False,
            "eot_fwd": False,
            "eot_bwd": False,
            "error": False,
        }

    @DictFeat()
    def actuator_name(self, axis):
        return self.positioner.getActuatorName(axis)
    
    @actuator_name.setter
    def actuator_name(self, axis, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass

    @DictFeat()
    def actuator_type(self, axis):
        return self.positioner.getActuatorType(axis)
    
    @actuator_type.setter
    def actuator_type(self, axis, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass


    @DictFeat()
    def amplitude(self, axis):
        return self.positioner.getAmplitude(axis)
    
    @amplitude.setter
    def amplitude(self, axis, value):
        self.positioner.setAmplitude(axis, value)


    @DictFeat()
    def axis_status(self, axis):
        return self.positioner.getAxisStatus(axis)
    
    @axis_status.setter
    def axis_status(self, axis, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass

    @DictFeat()
    def device_config(self):
        return self.positioner.getDeviceConfig()
    
    @device_config.setter
    def device_config(self, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass

    @DictFeat()
    def device_info(self, devNo):
        return self.positioner.getDeviceInfo(devNo)
    
    @device_info.setter
    def device_info(self, devNo, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass

    @DictFeat()
    def firmware_version(self):
        return self.positioner.getFirmwareVersion()

    @firmware_version.setter
    def firmware_version(self, value):
        # Placeholder, need to implement based on pyanc350 methods
        pass


    # Untested
    @Action()
    def jog(self, axis, speed):
        backward = 0 if speed >= 0.0 else 1
        start = 1 if speed != 0.0 else 0
        return self.positioner.startContinuousMove(self.device, axis, start, backward)
    
    @Action()
    def single_step(self, axis, direction):
        backward = direction <= 0
        return
    
    @Action()
    def absolute_move(self, axis, target, max_move=MAX_ABSOLUTE_MOVE):
        if not max_move is None:
            if abs(self.position[axis]-Q_(target, 'm')) > max_move:
                raise Exception("Relative move (target-current) is greater then the max_move")
        return self.positioner.setTargetPosition(self.device, axis, target)
        

    
    @Action()
    def relative_move(self, axis, delta):
        delta = Q_(delta, 'um')
        if abs(delta) > MAX_RELATIVE_MOVE:
            raise Exception("Relative move <delta> is greater then the MAX_RELATIVE_MOVE")
        else:
            target = self.position + delta
            target = target.to('m').magnitude
            print(target)
            # self.absolute_move(axis, target)
    @Action()
    def relative_move(self, axis, delta, max_move=MAX_RELATIVE_MOVE):
        target = self.position[axis] + delta
        target = target.to('m').magnitude
        print("Moving to {}".format(target))
        self.absolute_move(axis, target, max_move=max_move)
    @Action()
    def set_target_range(self, axis, target_range):
        return self.positioner.setTargetRange(self.device, axis, target_range)
        return
    @Action()
    def dc_bias(self, axis, voltage):
        return self.positioner.setDcVoltage(self.device, axis, voltage)
        return
    # ----------------------------------------------
    # Closed-loop Actions
    # These action are much slower but they ensure the move completed
    @Action(units=(None, 'um', 'um', None, 'seconds', None, None))
    def cl_move(self, axis, pos, delta_z=Q_(0.1,'um'), iter_n=10, delay=Q_(0.01, 's'), debug=False, max_iter=1000):
        i = 0
        while(not self.at_pos(axis, Q_(pos, 'um'), delta_z=Q_(delta_z, 'um'), iter_n=iter_n, delay=Q_(delay,'s'))):
            self.position[axis] = Q_(pos, 'um')
            i += 1
            if i>=max_iter:
                raise Exception("Reached max_iter")
        if debug: 
            print("It took {} iterations to move to position".format(i))
        return
    @Action(units=(None, 'um', 'um', None, 'seconds'))
    def at_pos(self, axis, pos, delta_z=Q_(0.1,'um'), iter_n=10, delay=Q_(0.01, 's')):
        for i in range(iter_n):
            time.sleep(delay)
            if abs(self.position[axis].to('um').magnitude-pos)>delta_z:
                return False
        return True
    # ----------------------------------------------
    # Untested
    
    