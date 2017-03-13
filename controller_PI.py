"""
Template for a fuzzy controller.
"""

from pyheli import Heli

import argparse
import ConfigParser
from threading import Thread, Event

# For logging
import time
from datetime import datetime
import csv

class Controller(Thread):
    """
    Controls the pitch and yaw of the helicopter model.
    """
    
    def __init__(self, event, config_file, log = True, show = False):
        
        Thread.__init__(self)
        self.stopped = event
    
        ### Initialize controller variables ###
        config = ConfigParser.RawConfigParser()
        config.read(config_file)
        self.Td = config.getfloat('Controller','Td')
        self.__heli = Heli(config.getstring('Motors','port'))

        # Initialize motors
        self.__heli.set_12v_motor_sleep_state(False)
        self.__heli.set_5v_motor_sleep_state(False)

        # State variables
        (psi,theta,phi) = self.__heli.read_sensor_data()
        self.theta = [theta, theta]
        self.theta_ref = [0]
        self.phi = [phi, phi]
        self.phi_ref = [0]
        self.ref_idx = 0
        self.e_theta = [0,0]
        self.e_phi = [0,0]
        self.u_1 = [0,0]
        self.u_2 = [0,0]

        # Yaw controller parameters
        self.Kp2 = 1.0
        self.Ti2 = 1.0

        # Pitch controller parameters
        self.Kp1 = 1.0
        self.Ti1 = 10000000.0
        
        self.__log_on = log
        if self.__log_on:
            self.log = True
            now_str = datetime.now().__str__().split('.')[0]
            now_str = now_str.replace(' ','-').replace(':','-')
            self.logfile = open(now_str + '_ctrl_log.csv','wb')
            self.logger = csv.writer(self.logfile,delimiter=';')
    
    def update(self):
        """
        This is one controller step.
        """
        
        # Update measurements
        (psi,theta,phi) = self.__heli.read_sensor_data()
        
        self.theta.insert(0,theta), self.theta.pop()
        self.phi.insert(0,phi), self.phi.pop()
        self.e_theta.insert(0,self.theta_ref[self.ref_idx]-theta), self.e_theta.pop()
        self.e_phi.insert(0,self.phi_ref[self.ref_idx]-phi), self.e_phi.pop()
        # Advance the reference index
        self.ref_idx = (self.ref_idx + 1) % min(len(self.theta_ref), len(self.phi_ref))

        ### Yaw Control law ###
        
        # The yaw control law is a simple PI controller.
        self.u_2.insert(0,0), self.u_2.pop()
        self.u_2[0] += self.Kp2*((self.e_phi[0] - self.e_phi[1])
                                 + self.Td*self.e_phi[0]/self.Ti2)

        ### Pitch Control law ###
        # P Controller
        self.u_1.insert(0,0), self.u_1.pop()
        self.u_1 += self.Kp1*((self.e_theta[0] - self.e_theta[1])
                              + self.Td*self.e_theta[0]/self.Ti1)
        self.__heli.set_motor_speed_12v(self.u_1[0])
        self.__heli.set_motor_speed_5v(self.u_2[0])
        print(self.u_1[0], self.u_2[0])
        
        # Log data
        if self.__log_on:
            self.logger.writerow([time.time(),self.theta[0],self.phi[0],
                                  self.theta_ref[self.ref_idx], self.phi_ref[self.ref_idx],
                                  self.u_1[0], self.u_2[0]])
    
    def set_ref(self, x_ref, y_ref):
        """
        Set the reference position of the ball.
        x_ref and y_ref should be lists of the same size
        """
        self.theta_ref = theta_ref
        self.phi_ref = phi_ref
        self.ref_idx = 0
    
    def run(self):
        """
        Run update every Td
        """
        while not self.stopped.wait(self.Td):
            self.update()
        
        self.__cleanup()
        
    def __cleanup(self):    
        self.__heli.reset_all()
        self.__heli.close()
        if self.__log_on:
            self.logfile.close()
        
if __name__ == '__main__':

    # Parse command line arguments, if any
    parser = argparse.ArgumentParser(description='Ball position control, P control law')
    parser.add_argument('--config_file',help='Platform configuration file name',
                        default='platform.cfg')
    args = parser.parse_args()

    stop_flag = Event()
    ctrl = Controller(stop_flag, args.config_file, log=True, show = False)
    try:
        ctrl.start()
    except KeyboardInterrupt:
        print('Stopping controller...')
        stop_flag.set()
