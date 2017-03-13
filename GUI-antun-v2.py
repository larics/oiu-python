__author__ = 'tratincica'

from PyQt4 import QtCore, QtGui, uic
import sys
from Pyheli_bare import Heli
import time
import datetime

# class Test(QtCore.QObject):
#
#     # Define a new signal
#     trigger = QtCore.pyqtSignal()
#
#     def connect_and_emit_trigger(self):
#         # Connect the trigger signal to a slot - mozda radi - tesirati
#         self.trigger.connect(self.handle_trigger)
#
#         # Emit the signal
#         self.trigger.emit()


class GUI():

    def __init__(self):

        #inicijalizacija
        self.board = Heli(port="/dev/ttyACM0")

        #dio vezan za spremanje podataka naziv dadoteke je mjesec-dan-sat-minuta
        datetimes = datetime.datetime.now()
        self.ftimer = time.clock()
        self.f = open("Test " + str(datetimes.month) + '-' + str(datetimes.day) + '-' + str(datetimes.hour) + '-' +
                      str(datetimes.minute) + '.txt', 'w')
        self.f.write('{0:10}, {1:10}, {2:10}, {3:10}, {4:10}, {5:10}, {6:10}, {7:10}\r\n'.format('time', 'yaw', 'pitch',
                     'u_yaw', 'u_pitch', 'p_yaw', 'p_pitch', 'factor'))

        #vrijeme ciklusa za metodu update
        self.t = 50

        #inicijalizacija timera ciklusa, integratora za elevaciju te azimut i grafickog sucelja
        self.timer = QtCore.QTimer()
        app = QtGui.QApplication(sys.argv)
        self.window = uic.loadUi("main.ui")
        self.window.show()
        self.timer.start(self.t)
        self.y_integrator = 0
        self.p_integrator = 0

        #a = Test()

        #povezivanje djelova grafickog sucelja sa metodama za upravljanje maketom
        self.window.verticalSliderPitch.valueChanged.connect(self.vertical_slider_pitch_callback)
        self.window.verticalSliderYaw.valueChanged.connect(self.vertical_slider_yaw_callback)
        self.window.checkBox5V.clicked.connect(self.set_5v_motor_state_callback)
        self.window.checkBox12V.clicked.connect(self.set_12v_motor_state_callback)

        self.timer.timeout.connect(self.update)
        #a.trigger.connect(self.refresh_yaw_reading) # - ne radi
        #a.trigger.connect(self.refresh_pitch_reading) # - ne radi
        #a.trigger.emit()

        #prilikom izlazska iz aplikacije, ulazi i izlazi se postave na nulu
        ret = app.exec_()
        self.closing()
        sys.exit(ret)

    def update(self):

        """
        Funckija koja se pokrece svakih self.t vremena
        refreshaju se podaci sa senzora
        ukoliko je u automatskom modu rada, provodi se regulacija
        zapisuju se podatci u datoteku
        """
        sensor_data = self.board.read_sensor_data()

        self.window.horizontalSliderYawSensor.setValue(int(float(sensor_data[2])))
        self.window.horizontalSliderPitchSensor.setValue(int(float(sensor_data[1])))

        yaw_angle = self.window.horizontalSliderYawSensor.value()
        pitch_angle = self.window.horizontalSliderPitchSensor.value()
        p_yaw = self.window.doubleSpinBoxYaw.value()
        p_pitch = self.window.doubleSpinBoxPitch.value()
        ref_yaw = self.window.horizontalSliderYawReg.value()
        ref_pitch = self.window.horizontalSliderPitchReg.value()
        e_yaw = ref_yaw-yaw_angle
        e_pitch = ref_pitch-pitch_angle
        ki_pitch = self.window.doubleSpinBoxFaktor.value()

        #omogucavanje slidera za rucnu kontrolu
        if self.window.radioButtonRucno.isChecked() and not self.window.radioButtonAut.isChecked():
            self.window.verticalSliderPitch.setEnabled(1)
            self.window.verticalSliderYaw.setEnabled(1)
            self.window.spinBoxPitch.setReadOnly(1)
            self.window.spinBoxYaw.setReadOnly(1)

            #kada je u rucnom modu, resetira se velicina integratora kako ne bi doslo do windupa
            u_yaw = 'rucno'
            u_pitch = 'rucno'
            self.p_integrator = 0
            self.y_integrator = 0

        #onemogucavanje rucne kontrole prilikom automatskog nacina rada
        if self.window.radioButtonAut.isChecked() and not self.window.radioButtonRucno.isChecked():
            self.window.verticalSliderPitch.setEnabled(0)
            self.window.verticalSliderYaw.setEnabled(0)
            self.window.spinBoxPitch.setReadOnly(0)
            self.window.spinBoxYaw.setReadOnly(0)

            self.p_integrator += e_pitch

            u_yaw = p_yaw * e_yaw
            u_pitch = 20 - (p_pitch * e_pitch) - (self.p_integrator * ki_pitch)

            if u_yaw > 100:
                u_yaw = 100
            elif u_yaw < -100:
                u_yaw = 100

            #deadzone
            if abs(ref_pitch-pitch_angle) > 2:
                self.window.verticalSliderPitch.setValue(int(u_pitch))

            #deadzone
            if abs(ref_yaw-yaw_angle) > 5:
                self.window.verticalSliderYaw.setValue(int(u_yaw))

        #zapisivanje u datoteku
        self.f.write('{:10.5}, {!s:10.2}, {!s:10.2}, {!s:10.2}, {!s:10.2}, {!s:10.2}, {!s:10.2}, {!s:10.2}\r\n'
                     .format(time.clock(), yaw_angle, pitch_angle, u_yaw, u_pitch, p_yaw, p_pitch, ki_pitch))

    def set_12v_motor_state_callback(self):

        """
        pomocu checkboxa se omogucuje/onemogucuje rad motora od 12V

        """
        print "12v motor state", self.window.checkBox12V.isChecked()

        if self.window.checkBox12V.isChecked():
            self.window.verticalSliderPitch.setValue(0)

        self.board.set_12v_motor_sleep_state(self.window.checkBox12V.isChecked())

    # def keyPressEvent(self, event):
    #
    #     false = QtCore.Qt.CheckState.False
    #
    #     if event.key() == QtCore.Qt.Key_R:
    #         if self.window.checkBox5V.isChecked():
    #             self.window.checkBox5V.setCheckedState(false)
    #             self.board.set_5v_motor_sleep_state(0)
    #         if self.window.checkBox12V.isChecked():
    #             self.window.checkBox12V.setCheckedState(false)
    #             self.board.set_12v_motor_sleep_state(0)

    def set_5v_motor_state_callback(self):

        """
        pomocu checkboxa se omogucuje/onemogucuje rad motora od 5V

        """
        print "5v motor state", self.window.checkBox5V.isChecked()

        if self.window.checkBox5V.isChecked():
            self.window.verticalSliderYaw.setValue(0)

        self.board.set_5v_motor_sleep_state(self.window.checkBox5V.isChecked())

    def vertical_slider_pitch_callback(self):

        """
        svaki put kada se promijeni vrijednost slidera pitcha
        sto je moguce postici pomicanjem slidera ili mijenjanjem vrijednosti u kucici
        vrijednost se posalje na motor od 12V

        """
        print self.window.verticalSliderPitch.value()

        if self.window.verticalSliderPitch.value() > 100:
            self.window.verticalSliderPitch.setValue(100)
        elif self.window.verticalSliderPitch.value() < 0:
            self.window.verticalSliderPitch.setValue(0)

        self.board.set_motor_speed_12v(self.window.verticalSliderPitch.value())

    def vertical_slider_yaw_callback(self):

        """
        svaki put kada se promijeni vrijednost slidera yaw
        sto je moguce postici pomicanjem slidera ili mijenjanjem vrijednosti u kucici
        vrijednost se posalje na motor od 5v

        """
        print self.window.verticalSliderYaw.value()

        if self.window.verticalSliderYaw.value() > 100:
            self.window.verticalSliderYaw.setValue(100)
        elif self.window.verticalSliderYaw.value < -100:
            self.window.verticalSliderYaw.setValue(-100)

        self.board.set_motor_speed_5v(self.window.verticalSliderYaw.value()-20)
    #
    # funckije vezane za pokusaj refreshanja vrijednosti sa senzora na drugi nacin - neuspjeli, ali da ostane
    #
    # def refresh_yaw_reading(self):
    #
    #     # self.board.read_yaw()
    #
    #     print self.window.horizontalSliderYawSensor.value()
    #
    #     self.window.horizontalSliderYawSensor.setValue(self.window.verticalSliderYaw.value())
    #
    # def refresh_pitch_reading(self):
    #
    #     # self.board.read_pitch()
    #
    #     print self.window.horizontalSliderPitchSensor.value()
    #
    #     self.window.horizontalSliderPitchSensor.setValue(self.window.verticalSliderPitch.value())

    def closing(self):
        """
        prilikom gasenja programa se vrijednosti vrate na 0 kako prilikom pokretanja ne bi bilo iznenadenja

        """
        self.board.reset_all()
        self.board.close()
        print 'Ending'


if __name__ == "__main__":
    a = GUI()
