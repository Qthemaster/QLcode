from lantz import Feat, DictFeat, Action
from lantz.messagebased import MessageBasedDriver
from lantz import Q_
import functools
from time import sleep

'''
Author: Qian Lin 
	10/17/2023
'''


class JDSHA9(MessageBasedDriver):
	"""This is the driver for the Keysight 36622A."""

	"""For VISA resource types that correspond to a complete 488.2 protocol
	(GPIB Instr, VXI/GPIB-VXI Instr, USB Instr, and TCPIP Instr), you
	generally do not need to use termination characters, because the
	protocol implementation also has a native mechanism to specify the
	end of the of a message.
	"""

	DEFAULTS = {
		'ASRL': {'read_termination': '\n',
		   'write_termination': '\n'
		   },
		'COMMON':{
			'baud_rate': '1200'
			}
		}
	
	RETURN_STATUS = {0: 'No error',
				  -100: 'Command error',
				  -102: 'Syntax error',
				  -103: 'Invalid separator',
				  -104: 'Data type error',
				  -108: 'Parameter not allowed',
				  -109: 'Missing parameter',
				  -110: 'Command header error',
				  -111: 'Header separator error',
				  -112: 'Program mnemonic too long',
				  -113: 'Undefined header',
				  -114: 'Header suffix out of range',
				  -120: 'Numeric data error',
				  -121: 'Invalid character in number',
				  -123: 'Exponent too large',
				  -124: 'Too many digits',
				  -128: 'Numeric data not allowed',
				  -130: 'Suffix error',
				  -134: 'Suffix too long',
				  -140: 'Character data error',
				  -141: 'Invalid character data',
				  -144: 'Character data too long',
				  -200: 'Execution error',
				  -220: 'Parameter error',
				  -221: 'Settings conflict',
				  -222: 'Data out of range',
				  -223: 'Too much data',
				  -224: 'Illegal parameter value',
				  -240: 'Hardware error',
				  -300: 'Device-specific error',
				  -310: 'System error',
				  -313: 'Save/recall memory lost',
				  -330: 'Self-test failed',
				  -350: 'Queue overflow',
				  -400: 'Query error',
				  -410: 'Query interrupted',
				  -420: 'Query unterminated',
				  -430: 'Query deadlocked',
				  '??': 'Undefined error number'
				  }

    #-----------------------------------------------------------------------------------------
	# Common Command
	@Feat()
	def idn(self):
		"""Returns a string that identifies the manufacturer, the HA9 model number, the
		serial number (or 0 if unavailable) and the firmware level."""
		return self.query('*IDN?')

	@Action()
	def clear_status(self):
		"""This command clears the following registers:
		1. Standard Event Status
		2. Operation Status Event
		3.  Questionable Status Event
		4. Status Byte
		5. Clears the Error Queue

		If this *CLS immediately follows a program message terminator (<NL>),
		then the output queue and teh MAV bit are also cleared.

		Command Syntax: *CLS
		Parameters:     (None)
		Query Syntax:   (None)

		"""
		self.write('*CLS')
		print('Status cleared')

	@Feat(values = tuple(range(256)))
	def standard_event_status_enable_register(self):
		"""Reads the Standard Event Status Enable register. Reading the
		register clears it.
		Query Syntax:        *ESE?
		Parameters:          (None)
		Returned Parameters: <NR1> (Register binary value)
		Related Commands:    *CLS *ESE *ESE? *OPC
		"""
		return self.query('*ESE?')

	@standard_event_status_enable_register.setter
	def standard_event_status_enable_register(self, NRf):
		"""Sets the bits in the standard event status enable register. The numeric value is
		rounded to the nearest integer and converted to a binary number. The bits of the
		register are set to match the bit values of the binary number
		"""
		
		self.write('*ESE {}'.format(NRf))
	
	

	@Feat()
	def read_standard_event_status_register(self):
		"""Reads the Standard Event Status Even register. Reading the
		register clears it.
		Query Syntax:        *ESR?
		Parameters:          (None)
		Returned Parameters: <NR1> (Register binary value)
		Related Commands:    *CLS *ESE *ESE? *OPC
		"""
		return self.query('*ESR?')

	@Action()
	def operation_complete_command(self):
		"""Causes the attenuator to set the OPC bit in the standard event status register
		when all pending operations have been completed.
		"""
		self.write('*OPC')

	@Action()
	def operation_complete_query(self):
		'''Places a 1 in the output queue of the attenuator when all pending operations
		have been completed. Because the 1 is not always placed in the output queue
		immediately, poll the status byte register and check the MAV bit to determine if
		there is a message available in the output queue.
		'''
		return self.query('*OPC?')
	
	@Action()
	def read_operation_identification(self):
		'''Reports on options installed or included with the attenuator.'''
		return self.query('*OPT?')
	
	@Action(values = tuple(range(10)))
	def recall(self,state):
		'''Restores the attenuator to a state that has been stored in local memory.
		Restoring to state 0 (*RCL 0) is equivalent to sending the *RST command. See
		the Save Command for a list of settings that are stored for each state.
		*RCL <space><numeric value> where 0 <= <numeric value> <= 9
		'''
		self.write('*RCL {}'.format(state))
	
	@Action(values = tuple(range(1,10)))
	def save(self,state):
		'''Stores the current state of the attenuator in local memory; as many as nine
		states can be stored. For each state, the following settings are stored:
		Total attenuation
		Display offset
		Wavelength
		LCM state (ON or OFF)
		Absolute power mode (ON or OFF)
		Beam block state at power-on (OFF or LAST)
		Beam block state (ON or OFF)'''
		self.write('*SAV {}'.format(state))

	@Feat(values = tuple(range(256)))
	def service_request_enable_register(self):
		'''Returns the contents of the service request enable register as an integer that,
		when converted to a binary number, represents the bit values of the register'''
		return self.query('*SRE?')

	@service_request_enable_register.setter
	def service_request_enable_register(self,sre):
		'''Sets the bits in the service request enable register. The numeric value is
		rounded to the nearest integer and converted to a binary number. The bits of the
		register are set to match the bit values of the binary number.'''
		self.write('*SRE {}'.format(sre))

	@Action()				
	def read_status_byte(self):
		'''Returns the contents of the status byte register as an integer that, when
		converted to a binary number, represents the bit values of the register The bit
		value for bit 6 of the register is the MSS bit value, not the RQS bit value.'''
		return self.query('*STB?')

	@Action()
	def reset(self):
		'''Restores the attenuator to the following settings:
		Total attenuation = 0 dB
		Display offset = 0 dB
		Wavelength = 1310 nm
		LCM state = OFF
		Absolute power mode state = OFF
		Beam block state at power on = LAST
		Beam block state = ON
		'''
		return self.query('*RST')

	@Action()
	def self_test(self):
		"""Initiates a self-test of the attenuator, and returns 0 if the attenuator passes the
		self-test or 1 if it fails.
		
		"""
		return self.query('*TST?')

	@Action()
	def wait(self):
		"""Prevents the attenuator from executing any further commands or queries until all
		pending operations have been completed.
		:INP:ATT 10;WAI;INP:OFF? prevents the attenuator from reading the offset until
		it has completed setting the attenuation to 10 dB.
		"""
		self.write('*WAI')

	#-------------------------------------------------------------------------------------
	# DISPlay Commands

	@Feat(limits=(0,1))
	def display_brightness(self):
		'''Returns the brightness setting for the display, which is always 1'''
		return self.query(':DISP:BRIG?')

	@display_brightness.setter
	def display_brightness(self,brig):
		'''Sets the brightness of the LCD display. Because the display brightness can only
		be set to 1, the numeric value is rounded to 1. This command is implemented
		only to maintain compatibility with the HP 8156A attenuator.'''
		self.write(':DISP:BRIG {}'.format(brig))

	@Feat(values={True: 1, False: 0})
	def display_status(self):
		'''Returns the current state of the display., which is always 1'''
		return self.query(':DISP:ENAB?')

	@display_brightness.setter
	def display_status(self,status):
		'''This command enables or disables a display on the attenuator. However,
		because the attenuator display cannot be turned off, the command has no
		effect. It is implemented only to maintain compatibility with the HP 8156A
		attenuator..'''
		self.write(':DISP:ENAB {}'.format(status))

    #---------------------------------------------------------------------------------------
	# I/O command

	def valid_check(value, min_value, max_value, valid_strings):
		if isinstance(value, (int, float)) and min_value <= value <= max_value:
			return value
		elif isinstance(value, str) and value.upper() in valid_strings:
			return value.upper()  # Convert to uppercase to ensure consistency
		else:
			raise ValueError(f'Invalid value: must be between {min_value} and {max_value}, or {", ".join(valid_strings)}')

	@Feat(procs=functools.partial(valid_check, min_value=0, max_value=100, valid_strings=['MIN', 'MAX', 'DEF']))
	def attenuation(self):
		"""Returns the current total attenuation in dB. The total attenuation is the total of
		the actual attenuation and the offset:
		Atttotal = Attactual + Offset
		This query also accepts the parameters MIN, MAX, and DEF. The minimum,
		maximum, or default value for the total attenuation at the current offset setting is
		returned."""
		return self.query(':INP:ATT?')

	@attenuation.setter
	def attenuation(self, value):
		'''Sets the total attenuation to the parameter value by changing the actual
		attenuation. Because the total attenuation includes the offset, the actual
		attenuation of the attenuator is set according to the following formula:
		Attactual = Atttotal - Offset
		This command also accepts the parameters MIN, MAX, and DEF. The minimum
		total attenuation is the total attenuation at which the actual attenuation is 0 dB.
		The maximum total attenuation is the total attenuation at which the actual
		attenuation is 30 dB. The default total attenuation is the same as the minimum
		attenuation.'''
		self.write(':INP:ATT {}'.format(value))

	@Action(values = {0: 'DEF', 1: 'MIN', 2: 'MAX'})
	def get_attenuation_setting(self, value):
		"""This query also accepts the parameters MIN, MAX, and DEF. The minimum,
		maximum, or default value for the total attenuation at the current offset setting is
		returned."""
		return self.query(':INP:ATT? {}'.format(value))
	
	@Feat(values={'ON': True, 'OFF': False})
	def lc_mode(self):
		'''Returns the current state of LCM mode, for example, returns 1 if LCM mode is
		ON and 0 if LCM mode is OFF.'''
		return self.query(':INP:LCM?')

	@lc_mode.setter
	def lc_mode(self, value):
		'''Sets the process by which the wavelength calibration is implemented when the
		wavelength is changed.
		A boolean value of 1 or ON activates LCM mode. In LCM mode, the total
		attenuation remains fixed when the wavelength is changed, for example, the
		attenuator prism is moved to give the same attenuation at the new wavelength.
		A boolean value of 0 or OFF deactivates LCM mode. When LCM mode is turned
		off, the actual attenuation changes (as well as the total attenuation) when the
		wavelength is changed, for example, the attenuator prism does not move when
		the wavelength is changed.'''
		self.write(':INP:LCM {}'.format(value))


	@Feat(procs=functools.partial(valid_check, min_value=-29.99, max_value=29.99, valid_strings=['MIN', 'MAX', 'DEF']))
	def offset(self):
		'''Returns the current setting of the display offset. The query accepts the
		parameters MIN, MAX, and DEF to return the minimum, maximum, or default
		value (respectively) for the display attenuation at the current offset setting.'''
		return self.query(':INP:OFFS?')

	@offset.setter
	def offset(self, value):
		'''Sets the display offset of the attenuator. The value of the offset has no effect on
		the actual attenuation, but it does affect the total attenuation, for example,
		Atttotal = Attactual + Offset
		This command also accepts the parameters MIN, MAX, and DEF. The minimum
		offset is -29.99 dB, the maximum offset is 29.99 dB, and the default offset is 0.'''
		self.write(':INP:OFFS {}'.format(value))

	@Action(values = {0: 'DEF', 1: 'MIN', 2: 'MAX'})
	def get_offset_setting(self, value):
		"""This query also accepts the parameters MIN, MAX, and DEF. The minimum,
		maximum, or default value for the total attenuation at the current offset setting is
		returned."""
		return self.query(':INP:OFFS? {}'.format(value))
	
	@Action()
	def set_offset_display(self):
		"""Sets the display offset so that the total attenuation is 0 dB:
		Offsetnew = Atttotal - Offsetold = -Attact"""
		self.write(':INP:OFFS:DISP')

	@Feat(procs=functools.partial(valid_check, min_value=1200, max_value=1700, valid_strings=['MIN', 'MAX', 'DEF']))
	def wavelength(self):
		'''Returns the current setting of the calibration wavelength in meters. This query
		also accepts the parameters MIN, MAX, and DEF, returning the minimum,
		maximum, or default value (respectively) for the calibration wavelength.'''
		return self.query(':INP:WAV?')


	@wavelength.setter
	def wavelength(self, value):
		'''Sets the calibration wavelength of the attenuator. Because the calibration
		wavelength is used to account for the wavelength dependence of the
		attenuation, set the calibration wavelength as close as possible to the source
		wavelength.
		This command also accepts the parameters MIN, MAX and DEF. The minimum
		wavelength is 1200 nm, the maximum wavelength is 1700 nm, and the default
		wavelength is 1310 nm.'''
		
		self.write(':INP:WAV {}'.format(value))

	@Action(values={0: 'DEF', 1: 'MIN', 2: 'MAX'})
	def get_wavelength_setting(self, value):
		'''Returns the current setting of the calibration wavelength in meters. This query
		also accepts the parameters MIN, MAX, and DEF, returning the minimum,
		maximum, or default value (respectively) for the calibration wavelength.'''
		return self.query(':INP:WAV? {}'.format(value))
		
	@Feat(values={True: 'ON',False : 'OFF'})
	def ap_mode(self):
		'''Returns the current absolute power mode state, for example, returns 1 if
		absolute power mode is ON (the actual attenuation is set by throughput) and 0 if
		absolute power mode is OFF (the actual attenuation is set by the total
		attenuation).'''
		return self.query(':OUTP:APM?')

	@ap_mode.setter
	def ap_mode(self, value):
		'''Sets whether the actual attenuation of the attenuator is set by changing the total
		attenuation or by changing the through power.
		When absolute power mode is set to ON, the actual attenuation is set by setting
		the through power rather than the total attenuation. The base through power,
		otherwise referred to as the power mode offset, is automatically set to the total
		attenuation when absolute power mode is activated:
		ThroughPowerbase = ATTtotal at apmode on = ATTactual + Offset
		This value differs from setting the power mode offset manually (using the
		keypad) because the attenuator is not set to power mode before the power
		mode offset is adjusted.
		To match the display of the attenuator to that of a power meter, adjust the offset
		until the attenuator display matches the power meter display, then turn on the
		absolute power mode and set the through power as required.
		The absolute power mode is turned off automatically when any of the following
		commands or their associated queries are received by the attenuator:
		:INP:ATT
		:INP:OFFS
		:INP:OFFS:DISP'''
		self.write(':OUTP:APM {}'.format(value))

	@Feat(values={True: 'ON', False: 'OFF'})
	def driver(self):
		"""Get or set the state of the 5 V output. 
		A value of True or 'ON' turns the 5 V output on.
		A value of False or 'OFF' turns the 5 V output off.
		"""
		self.query(':OUTP:DRIV?')
		
	@driver.setter
	def driver(self, value):
		'''Sets the state of the 5 V output. A boolean value of 1 or ON turns the 5 V output
		on. A boolean value of 0 or OFF turns the 5 V output off.'''
		self.write(':OUTP:DRIV {}'.format(value))

	@Feat(procs=functools.partial(valid_check, min_value=-29.99, max_value=29.99, valid_strings=['MIN', 'MAX', 'DEF']))
	def power(self):
		"""Returns the current through power of the attenuator in dBm. This query also
		accepts the parameters MIN, MAX, and DEF. The minimum, maximum, or default
		value (respectively) for the through power at the current base through power is
		returned
		"""
		return self.query(':OUTP:POW?')
		
	@power.setter
	def power(self, value):
		'''Sets the through power of the attenuator. The through power is used to set the
		actual attenuation of the attenuator.
		This command also accepts the parameters MIN, MAX, and DEF. The minimum
		through power is the through power for which the actual attenuation is 100 dB for
		the standard HA9 model and 60 dB for the HA9W (wide) model. The maximum
		through power is the through power for which the actual attenuation is 0 dB. The
		default through power is the same as the maximum through power.'''
		self.write(':OUTP:POW {}'.format(value))

	@Action(values={0: 'DEF', 1: 'MIN', 2: 'MAX'})
	def get_power_setting(self, value):
		'''Returns the current setting of the calibration wavelength in meters. This query
		also accepts the parameters MIN, MAX, and DEF, returning the minimum,
		maximum, or default value (respectively) for the calibration wavelength.'''
		return self.query(':OUTP:POW? {}'.format(value))

	@Feat(values={True: 'ON', False: 'OFF'})
	def state(self):
		'''Returns the state of the beam block: 1 if the beam block is out of the beam and
		0 if the beam block is in the beam.'''
		return self.query(':OUTP:STAT?')
	
	@state.setter
	def state(self, value):
		"""Sets the state of the beam block. A boolean value of 0 or OFF leaves the beam
		block in the beam (the default position) thereby turning off the optical power from
		the attenuator. When the beam block is in the beam, the attenuation of the
		attenuator is >110 dB.
		A boolean value of 1 or ON moves the beam block out of the beam, thereby
		turning on the optical power out of the attenuator.
		The attenuation setting of the attenuator is not affected by the beam block state.
		"""
		self.write(':OUTP:STAT {}'.format(value))

	@Feat(values={'LAST': 'ON',True: 'ON', 'DIS': 'OFF', False: 'OFF'})
	def beam_block(self):
		"""Returns the state of the beam block at power-on: 1 if the beam block is set to the
		same state that it was in at power-off and 0 if the beam block state is in the
		beam.
		"""
		return self.query(':OUTP:STAT:APOW?')
	

	@beam_block.setter
	def beam_block(self, value):
		'''Sets the state of the beam block at power-on: DIS, OFF, or 0 leaves the beam
		block in the beam, and 1, ON, or LAST sets the beam block state at power-on to
		the same state that the beam block was in at power-off.'''
		self.write(':OUTP:STAT:APOW {}'.format(value))

	#----------------------------------------------------------------------------------
	#Status and System Command

	#OPER

	@Action()
	def check_operation_condition(self):
		'''Returns the contents of the operation condition register as an integer that, when
		converted to a binary number, represents the bit values of the register.
		The attenuator only uses bit 1 of the operation condition register. Bit 1, the
		settling bit, is set when the attenuator is in the process of adjusting the actual
		attenuation.'''
		return self.query(':STAT:OPER:COND?')
	
	@Feat()
	def operation_enable_register(self):
		"""Get or set the bits in the operation enable register."""
		return self.query(':STAT:OPER:ENAB?')
		
	@operation_enable_register.setter
	def operation_enable_register(self, NRf):
		self.write(':STAT:OPER:ENAB {}'.format(NRf))  

	@Action()
	def get_operation_event_register(self):
		"""Returns the contents of the operation event register."""
		return self.query(':STAT:OPER:EVENT?')


	@Feat()
	def operation_negative_transition_register(self):
		"""Get or set the bits of the operation negative transition register."""
		return self.query(':STAT:OPER:NTR?')


	@operation_negative_transition_register.setter
	def operation_negative_transition_register(self, NRf):
		self.write(':STAT:OPER:NTR {}'.format(NRf))  

	@Feat()
	def operation_positive_transition_register(self):
		"""Get or set the bits of the operation positive transition register."""
		return self.query(':STAT:OPER:PTR?')


	@operation_positive_transition_register.setter
	def operation_positive_transition_register(self, NRf):
		self.write(':STAT:OPER:PTR {}'.format(NRf))
    
	#QUES

	@Action()
	def check_questionable_condition(self):
		'''Returns the contents of the questionable condition register as an integer that, when
		converted to a binary number, represents the bit values of the register.
		The attenuator only uses bit 1 of the operation condition register. Bit 1, the
		settling bit, is set when the attenuator is in the process of adjusting the actual
		attenuation.'''
		return self.query(':STAT:QUES:COND?')
	
	@Feat()
	def questionable_enable_register(self):
		"""Get or set the bits in the questionable enable register."""
		return self.query(':STATus:OPERation:ENABle?')
		
	@questionable_enable_register.setter
	def questionable_enable_register(self, NRf):
		self.write(':STAT:QUES:ENAB {}'.format(NRf))  

	@Action()
	def get_questionable_event_register(self):
		"""Returns the contents of the questionable event register."""
		return self.query(':STAT:QUES:EVENT?')


	@Feat()
	def questionable_negative_transition_register(self):
		"""Get or set the bits of the questionable negative transition register."""
		return self.query(':STAT:QUES:NTR?')


	@questionable_negative_transition_register.setter
	def questionable_negative_transition_register(self, NRf):
		self.write(':STAT:QUES:NTR {}'.format(NRf))  

	@Feat()
	def questionable_positive_transition_register(self):
		"""Get or set the bits of the questionable positive transition register."""
		return self.query(':STAT:QUES:PTR?')


	@questionable_positive_transition_register.setter
	def questionable_positive_transition_register(self, NRf):
		self.write(':STAT:QUES:PTR {}'.format(NRf))

	@Action()
	def status_preset(self):
		'''This command presets all the enable and transition registers in the questionable
		and operation registers to the following settings:
		All bits in the ENABle registers are set to 0
		All bits in the positive transition registers are set to 1
		All bits in the negative transition registers are set to 0'''
		self.write(':STAT:PRES')	

	@Action()
	def get_error(self):
		'''Returns the next error message in the error queue. Because the error queue is
		an FIFO queue, the error returned is the oldest unread error. The error message
		consists of an error number followed by an error message, for example,
		0, No Error
		See the Error Queue section for a list of error numbers and their associated
		messages.'''
		code = self.query(':SYST:ERR?')
		if code != 0:
			print("Error type {}: {} ".format(code, JDSHA9.RETURN_STATUS[code]))
		return code
		
	
	@Action()
	def get_version(self):
		'''Returns the formatted numeric value corresponding to the SCPI version number
		to which the attenuator complies.'''
		return self.query(':SYST:VERS?')
	
	#------------------------------------------------------------------------------------
	#user command
	
	@Feat(values={True: 'ON', False: 'OFF'})
	def user_mode(self):
		"""Get or set the user mode. 
		A boolean value of 1 or ON turns user mode on and
		the HA9 uses the current user slope instead of the factory-set slope.
		A boolean value of 0 or OFF turns user mode off and the HA9 uses the factory-set slope.
		"""
		return self.query(':UCAL:USRM?')
		
	@user_mode.setter
	def user_mode(self, value):
		self.write(':UCAL:USRM {}'.format(value))

	@Feat(procs=functools.partial(valid_check, min_value=0.5, max_value=2.0, valid_strings=['MIN', 'MAX', 'DEF']))
	def user_slope(self):
		'''Returns the current user slope setting. This query also accepts the parameters
		MIN, MAX and DEF, returning the corresponding minimum, maximum, or default
		value for the user slope.'''
		return self.query(':UCAL:SLOP?')


	@user_slope.setter
	def user_slope(self, value):
		'''Sets the user slope. The slope of the attenuator can be matched to a power
		meter for a given source by adjusting the user slope.
		This command also accepts the parameters MIN, MAX, and DEF. The minimum
		value for the slope is 0.5, the maximum value is 2.0, and the default value is 1.0.'''
				
		self.write(':UCAL:SLOP {}'.format(value))

	@Action(values={0: 'DEF', 1: 'MIN', 2: 'MAX'})
	def get_user_slope_setting(self, value):
		'''Returns the current user slope setting. This query also accepts the parameters
		MIN, MAX and DEF, returning the corresponding minimum, maximum, or default
		value for the user slope.'''
		return self.query(':UCAL:SLOP? {}'.format(value))



















if __name__ == '__main__':
	from time import sleep
	from lantz import Q_
	from lantz.log import log_to_screen, DEBUG

	volt = Q_(1, 'V')
	milivolt = Q_(1, 'mV')
	Hz = Q_(1, 'Hz')

	log_to_screen(DEBUG)
	
