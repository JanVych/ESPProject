from odoo_rpc import DeviceAPI
import time
import network
import webrepl
from rs485 import send
from sd_card import CardSD
from ntptime import settime
from machine import RTC


class Application:
    def __init__(self):
        self.wifi_name = "TTS_comp"
        #self.wifi_name = "AndroidAP4231"
        self.wifi_password = "KDD.RMS=1nm"
        #self.wifi_password = "dimetylhydrazin"
        self.ip_address = "37.46.208.212"
        self.port = 8070
        self.database = "pracovni_server"
        self.user = "gazix@email.cz"
        self.password = "0J11w$<B_/d)TEh"
        self.station = True
        self.rtc = RTC()
        self.sta_if = network.WLAN(network.STA_IF)
        self.wifi_interval = 60 * 6
        self.sleep_interval = 60

        sd = CardSD()
        sd.makedir()
        self.dir_address = sd.dir_address
        sd.deinit()

    def wifi_connection(self, number):
        """Connection to wifi"""
        self.sta_if.active(True)  # Activation of station interface
        try:
            self.sta_if.connect(self.wifi_name, self.wifi_password)
        except OSError:
            pass
        time.sleep(5)

        i = 0
        while self.sta_if.isconnected() is not True and i < number:
            print("sta_if.isconnected = ", self.sta_if.isconnected(), i, number)
            try:
                self.sta_if.connect(self.wifi_name, self.wifi_password)
            except OSError:
                print("Except:   OSError: Wifi Internal Error")
            time.sleep(5)
            i = i + 1

    def access_point(self):
        """Setting access point"""
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)

    def set_time(self):
        """It set time"""
        try:
            settime()
            print(self.rtc.datetime())
        except OSError:
            pass

    def sd_card(self, text, date):
        """It make sd card object and write text to it"""
        date_file = date[0:2] + date[3:5] + date[6:]
        sd = CardSD()
        sd.dir_address = self.dir_address
        sd.file_address = sd.dir_address + str("/") + date_file + ".txt"
        print("file_address = ", sd.file_address)
        sd.sd_write(text)
        #sd.sd_read()
        sd.deinit()

    def string2float(self, string):
        """It transform string to float"""
        try:
            result = float(string)
        except ValueError:
            result = 0.0
        return result

    def run(self):
        """Run application"""

        # Create webrepl
        webrepl.start()
        print("Webrepl is running")
        # "WebREPL server started on http://192.168.1.220:8266/"

        # Wifi connection
        self.wifi_connection(number=50)
        if self.sta_if.isconnected() is True:
            print("Internet connection successfull")
            self.set_time()

        if self.sta_if.isconnected() is True:
            device = DeviceAPI(host=self.ip_address, port=self.port, db=self.database, user=self.user, pwd=self.password, number=50)
            #device = DeviceAPI(host="localhost", port=8069, db="vita_lucka_odoo", user="vita", pwd="lamacvitek")
            #device = DeviceAPI(host="37.46.208.212", port=8070, db="pracovni_server", user="gazix@email.cz", pwd="0J11w$<B_/d)TEh")

            if device.connected is True:
                measurement_id = device.function(model_name='datalogger.measurement', function_name="make_record", vals={"name": "Z Arduina"}, number=20)
            else:
                measurement_id = False

        else:
            device = False
            measurement_id = False

        i = 1
        while True:
            time_date = self.rtc.datetime()
            date_str = str("%02d" % time_date[2]) + "." + str("%02d" % time_date[1]) + "." + str(time_date[0])
            time_str = str("%02d" % (time_date[4])) + ":" + str("%02d" % time_date[5]) + ":" + str("%02d" % time_date[6])

            dry_temperature_str1 = send("T1")
            dew_point_str1 = send("D1")
            temperature_period_str1 = send("TT1")
            humidity_period_str1 = send("H1")

            dry_temperature_str2 = send("T1")
            dew_point_str2 = send("D1")
            temperature_period_str2 = send("TT1")
            humidity_period_str2 = send("H1")

            text1 = date_str + "\t" + time_str + "\t" + dry_temperature_str1 + "\t" + dew_point_str1 + "\t" + temperature_period_str1 + "\t" + humidity_period_str1
            text2 = "\t" + dry_temperature_str2 + "\t" + dew_point_str2 + "\t" + temperature_period_str2 + "\t" + humidity_period_str2
            text = text1 + text2
            self.sd_card(text, date_str)

            dry_temperature1 = self.string2float(dry_temperature_str1)
            dew_point1 = self.string2float(dew_point_str1)
            temperature_period1 = self.string2float(temperature_period_str1)
            humidity_period1 = self.string2float(humidity_period_str1)

            dry_temperature2 = self.string2float(dry_temperature_str2)
            dew_point2 = self.string2float(dew_point_str2)
            temperature_period2 = self.string2float(temperature_period_str2)
            humidity_period2 = self.string2float(humidity_period_str2)

            if self.sta_if.isconnected() is True:
                self.set_time()
                if measurement_id is not False:
                    device.function(model_name='datalogger.temperature', function_name="make_record",
                                    vals={"measurement_id": int(measurement_id), "dry_temperature1": dry_temperature1,
                                          "dew_point1": dew_point1, "temperature_period1": temperature_period1,
                                          "humidity_period1": humidity_period1, "dry_temperature2": dry_temperature2,
                                          "dew_point2": dew_point2, "temperature_period2": temperature_period2,
                                          "humidity_period2": humidity_period2}, number=5)
                else:
                    device = DeviceAPI(host=self.ip_address, port=self.port, db=self.database, user=self.user, pwd=self.password, number=20)
                    measurement_id = device.function(model_name='datalogger.measurement', function_name="make_record", vals={"name": "Z Arduina"}, number=20)

            else:
                if measurement_id is False:
                    if i % self.wifi_interval == 0:
                        # Wifi connection
                        self.wifi_connection(number=20)
                        if self.sta_if.isconnected() is True:
                            if measurement_id is False:
                                device = DeviceAPI(host=self.ip_address, port=self.port, db=self.database, user=self.user, pwd=self.password, number=20)
                                measurement_id = device.function(model_name='datalogger.measurement', function_name="make_record", vals={"name": "Z Arduina"}, number=20)
                else:
                    if i % self.wifi_interval == 0:
                        # Wifi connection
                        self.wifi_connection(number=20)

            print("step ", i)
            time.sleep(self.sleep_interval)
            i = i + 1


app = Application()
app.run()