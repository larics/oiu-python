#!/usr/bin/env python
__author__ = 'tratincica'


import serial
import time
import string


def build_cmd_str(cmd, args=None):
    """
    Build a command string that can be sent to the arduino.

    Input:
    :param cmd (str): the command to send to the arduino, must not
            contain a % character
    :param args (iterable): the arguments to send to the command
    """
    if args:
        args = '%'.join(map(str, args))
    else:
        args = ''
    return "@{cmd}%{args}$!".format(cmd=cmd, args=args)


def get_version(sr):
    """
    Requests and then prints the version of software currently on the microcontroller.
    It is used to ensure no mismatch in communications.
    Netreba se koristit ako se zna s cim se radi
    -------------
    :param sr: currently open serial communication
    -------------
    :return value: software version currently on the microcontroller
    """
    cmd_str = build_cmd_str("version")
    try:
        sr.write(cmd_str)
        sr.flush()
    except serial.SerialTimeoutException:
        return None
    return sr.readline().replace("\r\n", "")


class Arduino(object):

    def __init__(self, baud=9600, port="COM6", timeout=2, sr=None):
        """
        Initializes serial communication with Arduino if no connection is
        given.
        -------------
        :param baud: Serial communication speed
        :param port: Serial communication port
        :param timeout: Read timeout value
        :param sr: Serial communication variable
        """
        if not sr:
            sr = serial.Serial(port, baud, timeout=timeout)
        sr.flush()
        self.sr = sr

    def version(self):
        return get_version(self.sr)

    def digital_write(self, pin, val):
        """
        Sends digital_write command
        to digital pin on Arduino
        -------------
        :param pin: digital pin number
        :param val: either "HIGH" or "LOW"
        """
        if val == "LOW":
            pin_ = -pin
        else:
            pin_ = pin
        cmd_str = build_cmd_str("dw", (pin_, ))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            pass

    def digital_read(self, pin):
        """
        Returns the value of a specified
        digital pin.
        -------------
        inputs:
        :param pin: digital pin number for measurement
        -------------
        returns:
        :return value: 0 for "LOW", 1 for "HIGH"
        """
        cmd_str = build_cmd_str("dr", (pin, ))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            pass
        rd = self.sr.readline().replace("\r\n", "")
        try:
            return int(rd)
        except ValueError:
            return 0

    def analog_write(self, pin, val):
        """
        Sends analog_write pwm command
        to pin on Arduino
        :::has nothing to do with analog write, it is pwm control:::
        -------------
        :param pin: pin number
        :param val: integer 0 (off) to 255 (always on)
        """
        if val > 255:
            val = 255
        elif val < 0:
            val = 0
        cmd_str = build_cmd_str("aw", (pin, val))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            pass

    def analog_read(self, pin):
        """
        Returns the value of a specified
        analog pin.
        -------------
        inputs:
        :param pin : analog pin number for measurement
        -------------
        returns:
        :return value: integer from 0 to 1023
        """
        cmd_str = build_cmd_str("ar", (pin, ))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            pass
        rd = self.sr.readline().replace("\r\n", "")
        try:
            return int(rd)
        except ValueError:
            return 0

    def pin_mode(self, pin, val):
        """
        Sets I/O mode of pin
        :::you cannot write to an input pin, or read from an output:::
        -------------
        inputs:
        :param pin: pin number to toggle
        :param val: "INPUT" or "OUTPUT"
        """
        if val == "INPUT":
            pin_ = -pin
        else:
            pin_ = pin
        cmd_str = build_cmd_str("pm", (pin_, ))
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            pass

    def read_sensor(self):
        """
        Reads the data from the IMU
        -------------
        :return value: imu_data
        """
        cmd_str = build_cmd_str("sd")
        try:
            self.sr.write(cmd_str)
            self.sr.flush()
        except serial.SerialTimeoutException:
            print "Gwaaah!"
        time.sleep(0.03)
        try:
            raw_data = self.sr.readline()
            raw_data = raw_data.replace("!ANG:", "")
            raw_data = raw_data.replace("\r\n", "")
            data = string.split(raw_data, ",")
        except:
            print "Failed to reach sensor"
            data = ['False', 'False', 'False']
        if len(data) > 2:
            try:
                return data
            except ValueError:
                print "Invalid line"

    def close(self):
        """
        All data is transmitted
        before closing the serial port

        """
        if self.sr.isOpen():
            self.sr.flush()
            self.sr.close()
