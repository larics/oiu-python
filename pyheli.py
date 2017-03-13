#!/usr/bin/env python
# -*- coding: utf-8 -*-


from pyno import Arduino


def per2val(percentage):
    """
    Converts the value from percentage to an integer in range from 0 to 255
    -------------
    input:
    :param percentage: a number from 0 to 100
    :return value: returns an integer in range from 0 to 255
    """
    val = int(percentage/float(100) * 255)
    return val


def ang2per(angle):
    """
    Converts the value of angle to an integer in range from 0 to 360
    -------------
    :param angle: a number from 0 to 360
    :return value: returns an integer in range from 0 to 360
    """
    val = int(angle/float(360) * 100)
    return val


class Heli(Arduino):

    def __init__(self, port):
        """
        Initialises the motors and parameters used for heli control
        """
        super(Heli, self).__init__(port=port)

        #Initialization of 5V motor pins
        self.motor_5v_sleep = 4
        self.motor_5v_in1 = 5
        self.motor_5v_in2 = 6
        self.motor_5v_fault = 19

        #Initialization of 12V motor pins
        self.motor_12v_sleep = 18
        self.motor_12v_in1 = 9
        self.motor_12v_in2 = 10

        #5V motor initialization
        Arduino.pin_mode(self, self.motor_5v_sleep, "OUTPUT")
        Arduino.pin_mode(self, self.motor_5v_in1, "OUTPUT")
        Arduino.pin_mode(self, self.motor_5v_in2, "OUTPUT")
        Arduino.pin_mode(self, self.motor_5v_fault, "INPUT")

        #12V motor initialization
        Arduino.pin_mode(self, self.motor_12v_sleep, "OUTPUT")
        Arduino.pin_mode(self, self.motor_12v_in1, "OUTPUT")
        Arduino.pin_mode(self, self.motor_12v_in2, "OUTPUT")

        #Initialization of 5v motor state
        self.state_5v_motor = False

        #Initialization of 12v motor state
        self.state_12v_motor = False

    def set_5v_motor_sleep_state(self, state):
        """
        Sets the state of the 5v motor and sends the value to the uC

        0 for sleep, 1 to enable the device
        """

        if state:
            self.state_5v_motor = True
            Arduino.digital_write(self, self.motor_5v_sleep, "HIGH")
        elif not state:
            self.state_5v_motor = False
            Arduino.digital_write(self, self.motor_5v_sleep, "LOW")

    def check_5v_motor_fault(self):
        """
        Checks for faults on the 5v motor
        -------------
        :return value: returns a 0 when in fault, 1 when operational
        """
        return Arduino.digital_read(self, self.motor_5v_fault)

    def set_12v_motor_sleep_state(self, state):
        """
        Sets the state of the 12v motor

        0 for sleep, 1 to enable the device
        """
        if state:
            self.state_12v_motor = True
            Arduino.digital_write(self, self.motor_12v_sleep, "HIGH")
        elif not state:
            self.state_12v_motor = False
            Arduino.digital_write(self, self.motor_12v_sleep, "LOW")

    def set_motor_speed_5v(self, percentage):
        """
        Sets the 5V motor speed in percentage of full speed.
        -------------
        inputs:
        :param percentage: a number from -100 for CCW to 100 for CW direction
        """

        #ensures the percentages are in 0 to 100 range
        if percentage > 100:
            percentage = 100
        elif percentage < -100:
            percentage = -100
        elif 10 < percentage < 30:
            percentage = 30
        elif -10 > percentage > -30:
            percentage = -30

        #sends the direction and value to the motor only if there is no fault
        #and the motor is not in sleep condition
        if (percentage > 0) and self.state_5v_motor:  # and (self.check_5v_motor_fault()):
            Arduino.analog_write(self, self.motor_5v_in1, per2val(percentage))
            Arduino.digital_write(self, self.motor_5v_in2, "LOW")
        elif percentage < 0 and self.state_5v_motor:  # and (self.check_5v_motor_fault()):
            Arduino.analog_write(self, self.motor_5v_in2, per2val(-percentage))
            Arduino.digital_write(self, self.motor_5v_in1, "LOW")
        elif not self.state_5v_motor:
            Arduino.digital_write(self, self.motor_5v_in1, "LOW")
            Arduino.digital_write(self, self.motor_5v_in2, "LOW")

    def set_motor_speed_12v(self, percentage):
        """
        Sets the 5V motor speed in percentage of full speed.
        -------------
        inputs:
        :param percentage: a number from 0 to 100
        """

        #ensures the percentages are in 0 to 100 range
        if percentage > 100:
            percentage = 100
        elif percentage < 0:
            percentage = 0

        #sends the direction and value to the motor
        if self.state_12v_motor:
            Arduino.analog_write(self, self.motor_12v_in1, per2val(percentage))
            Arduino.digital_write(self, self.motor_12v_in2, "LOW")
        else:
            Arduino.digital_write(self, self.motor_12v_in1, "LOW")
            Arduino.digital_write(self, self.motor_12v_in2, "LOW")

    def read_sensor_data(self):
        """
        Reads the data from the IMU
        -----------
        :return value: returns the sensor data roll, pitch, yaw
        """

        data = Arduino.read_sensor(self)
        # print data[0]
        # print data[1]
        # print data[2]
        return data

    def reset_all(self):
        """
        A function to reset all ports that control the motors

        """
        if self.state_12v_motor:
            self.set_12v_motor_sleep_state(0)
        if self.state_5v_motor:
            self.set_5v_motor_sleep_state(0)
        self.set_motor_speed_12v(0)
        self.set_motor_speed_5v(0)
