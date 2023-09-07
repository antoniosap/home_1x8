#
# home_1x8 controller 12.2.2023
# hardware: ESP8266, 4 buttons, 2x LED 8 digits
# firmware: 12.4.0.2(home_display_ir)
# for productions run inside ha-appdaemon add-on
#
# button left   = meteo: single mostra meteo + meteo unhold, double meteo hold
# button center = power meter: single mostra power, double mostra clock
# button right  = boiler: single simple toggle on/off
#
# ir receiver
# RULE1 ON IrReceived#DataLSB DO publish stat/tasmota_1DAA95/IR %value% ENDON
# RULE1 1
#

TOPIC_TASMOTA_ID = "1DAA95"
TOPIC_HOME_BOX_RESULT = f"stat/tasmota_{TOPIC_TASMOTA_ID}/RESULT"
TOPIC_HOME_BOX_IR = f"stat/tasmota_{TOPIC_TASMOTA_ID}/IR"
TOPIC_HOME_BOX_CMND = f"cmnd/tasmota_{TOPIC_TASMOTA_ID}/"
TOPIC_HOME_BOX_CMND_WIDTH = TOPIC_HOME_BOX_CMND + "DisplayWidth"
TOPIC_HOME_BOX_CMND_DIMMER = TOPIC_HOME_BOX_CMND + "DisplayDimmer"
TOPIC_HOME_BOX_CMND_DISPLAY_TEXT = TOPIC_HOME_BOX_CMND + "DisplayText"
TOPIC_HOME_BOX_CMND_DISPLAY_FLOAT = TOPIC_HOME_BOX_CMND + "DisplayFloat"
TOPIC_HOME_BOX_CMND_DISPLAY_CLOCK = TOPIC_HOME_BOX_CMND + "DisplayClock"
TOPIC_HOME_BOX_CMND_DISPLAY_SCROLL = TOPIC_HOME_BOX_CMND + "DisplayScrollText"

DISPLAY_LEN = 8
POWER_METER_EVENT = "sensor.total_watt"
# TC_EXTERNAL_ID = "sensor.ewelink_th01_b0071325_temperature"   guasto 4.9.2023
TC_EXTERNAL_ID = "sensor.sonoff_th_am2301_temperature"
METEO_EVENT = "weather.casatorino2022"
METEO_STATE = METEO_EVENT
BOILER_STATE = "switch.boiler"
ENTITY_SWITCH_BOILER = 'switch.boiler'
CO2_ID = 'sensor.mh_z19_co2_mhz19b_carbondioxide'
LUX_ID = 'sensor.home_lux_tsl2561_illuminance'

# --------------------------------------------------------------------
# end of configuration
# --------------------------------------------------------------------

import appdaemon.plugins.hass.hassapi as hass
import appdaemon.plugins.mqtt.mqttapi as mqtt
import json
import datetime as dt

DISPLAY_STATE_CLOCK = 0
DISPLAY_STATE_POWER_METER = 1
DISPLAY_STATE_METEO = 2
DISPLAY_STATE_CO2_LUX = 3

METEO_TEXT = {
    "clear-night": "SERE",
    "cloudy": "NUVO",
    "exceptional": "EXCP",
    "fog": "NEbb",
    "hail": "GRAN",
    "lightning": "TEMP",
    "lightning-rainy": "TMPP",
    "partlycloudy": "PNUV",
    "pouring": "ROVE",
    "rainy": "PIOG",
    "snowy": "NEVE",
    "snowy-rainy": "NEVP",
    "sunny": "SOLE",
    "windy": "VENT",
    "windy-variant": "PVEN",
    "unavailable": "-nd-"
}

IR_REMOTE_MELICONI_SAMSUNG = {
    "0X70704FB": "1",
    "0X70705FA": "2",
    "0X70706F9": "3",
    "0X70708F7": "4",
    "0X70709F6": "5",
    "0X7070AF5": "6",
    "0X7070CF3": "7",
    "0X7070DF2": "8",
    "0X7070EF1": "9",
    "0X70711EE": "0",
    "0X7071FE0": "I",
    "0X70701FE": "CH_IN",
    "0X7076C93": "rosso",
    "0X70714EB": "verde",
    "0X70715EA": "GIALLO",
    "0X70716E9": "BLU",
    "0X70702FD": "ON_OFF",
    "0X7070BF4": "VOL -",
    "0X70707F8": "VOL +",
    "0X70710EF": "Prog -",
    "0X70712ED": "Prog +",
    "0X7071AE5": "menu",
    "0X7070FF0": "mute",
    "0X707F30C": "app",
    "0X7077986": "home",
    "0X7074FB0": "GUIDE",
    "0X707609F": "up",
    "0X707659A": "left",
    "0X707629D": "right",
    "0X707619E": "down",
    "0X7076897": "OK",
    "0X70758A7": "BACK",
    "0X7072DD2": "EXIT"
}


class Home1x8(hass.Hass):
    mqtt = None
    insideDimmerRange = False
    displayState = DISPLAY_STATE_CLOCK
    totalW = 9999
    meteoHoldOption = False
    meteoText = METEO_TEXT['unavailable']

    def initialize(self):
        # mqtt buttons
        self.mqtt = self.get_plugin_api("MQTT")
        self.mqtt.mqtt_subscribe(topic=TOPIC_HOME_BOX_RESULT)
        self.mqtt.listen_event(self.mqttEvent, "MQTT_MESSAGE", topic=TOPIC_HOME_BOX_RESULT, namespace='mqtt')
        # IR service
        self.mqtt.mqtt_subscribe(topic=TOPIC_HOME_BOX_IR)
        self.mqtt.listen_event(self.mqttEventIR, "MQTT_MESSAGE", topic=TOPIC_HOME_BOX_IR, namespace='mqtt')
        # LED display service
        self.run_minutely(self.displayUpdateEMinutely, dt.time(0, 0, 0))
        # power meter events
        self.listen_event(self.powerMeterEvent, 'state_changed', entity_id=POWER_METER_EVENT)
        # meteo events
        self.meteoText = METEO_TEXT[self.get_state(METEO_STATE)]
        self.listen_event(self.meteoEvent, 'state_changed', entity_id=METEO_EVENT)

    def mqttEvent(self, event_name, data, *args, **kwargs):
        pld = json.loads(data['payload'])
        if 'Button1' in pld.keys():
            Button1 = pld['Button1']['Action']
            if Button1 == 'SINGLE':
                self.meteoHoldOption = False
            elif Button1 == 'DOUBLE':
                self.meteoHoldOption = True
            self.meteoDisplay()
        if 'Button2' in pld.keys():
            Button2 = pld['Button2']['Action']
            if Button2 == 'SINGLE':
                self.meteoHoldOption = False
                self.displayState = DISPLAY_STATE_POWER_METER
                self.powerMeterDisplay()
            elif Button2 == 'DOUBLE':
                self.displayState = DISPLAY_STATE_CLOCK
                self.clockDisplay()
        if 'Button3' in pld.keys():
            Button3 = pld['Button3']['Action']
            if Button3 == 'SINGLE':
                if self.get_state(BOILER_STATE) == 'on':
                    self.boilerOff()
                elif self.get_state(BOILER_STATE) == 'off':
                    self.boilerOn()
                else:
                    self.boilerOff()
            elif Button3 == 'DOUBLE':
                pass
        if 'Button4' in pld.keys():
            Button4 = pld['Button4']['Action']
            if Button4 == 'SINGLE':
                self.displayState = DISPLAY_STATE_CO2_LUX
                self.co2LuxDisplay()

    def mqttEventIR(self, event_name, data, *args, **kwargs):
        ir_code = IR_REMOTE_MELICONI_SAMSUNG[data['payload']]
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, ir_code)
        if ir_code == '7':
            # vent on
            self.turn_on("switch.tasmota_5")
        elif ir_code == '8':
            # vent off
            self.turn_off("switch.tasmota_5")
        elif ir_code == '9':
            # voice repeat last message
            self.turn_on("media_player.mopidy")
        elif ir_code == 'rosso':
            # all lights on, @ eWeLink WB02
            self.turn_on("switch.tasmota_3")
            self.turn_on("switch.th10_1")
            self.turn_on("switch.tasmota_7")
            self.turn_on("switch.tasmota_8")
        elif ir_code == 'verde':
            # all lights off, @ eWeLink WB02
            self.turn_off("switch.tasmota_3")
            self.turn_off("switch.th10_1")
            self.turn_off("switch.tasmota_7")
            self.turn_off("switch.tasmota_8")
        elif ir_code == 'GIALLO':
            # boiler on, timed
            self.boilerOn()
        elif ir_code == 'BLU':
            # boiler off
            self.boilerOff()

    def displayUpdateEMinutely(self, *args, **kwargs):
        weekday = dt.datetime.now().weekday() + 1  # lun == 1
        # display dimmer time range
        if self.now_is_between("22:00:00", "08:00:00"):
            if not self.insideDimmerRange:
                self.insideDimmerRange = True
                self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DIMMER, 20)
        else:
            if self.insideDimmerRange:
                self.insideDimmerRange = False
                self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DIMMER, 100)
        # default state
        self.displayState = DISPLAY_STATE_CLOCK
        if self.meteoHoldOption:
            self.displayState = DISPLAY_STATE_METEO
            self.meteoDisplay()
        else:
            # power meter time range
            if ((self.now_is_between("04:00:00", "23:59:00")) and
                    weekday in [1, 2, 3, 4, 5]):
                self.displayState = DISPLAY_STATE_POWER_METER
            if ((self.now_is_between("08:00:00", "23:59:00")) and
                    weekday in [6, 7]):
                self.displayState = DISPLAY_STATE_POWER_METER
        #
        # timed actions
        #
        if self.displayState == DISPLAY_STATE_CLOCK:
            self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_CLOCK, 2)
        elif self.displayState == DISPLAY_STATE_POWER_METER:
            self.powerMeterDisplay()
        elif self.displayState == DISPLAY_STATE_METEO:
            pass
        elif self.displayState == DISPLAY_STATE_CO2_LUX:
            pass
        else:
            self.displayState = DISPLAY_STATE_CLOCK

    def boilerOn(self):
        self.call_service("switch/turn_on", entity_id=ENTITY_SWITCH_BOILER)
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, "BOIL ON")

    def boilerOff(self):
        self.call_service("switch/turn_off", entity_id=ENTITY_SWITCH_BOILER)
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, "BOIL OFF")

    def clockDisplay(self):
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_CLOCK, 2)

    def co2LuxDisplay(self):
        device_co2 = self.get_entity(CO2_ID)
        value_co2 = device_co2.get_state()
        value = ''
        if value_co2 == 'unavailable':
            value += f"CO2 {METEO_TEXT['unavailable']}"
        else:
            value += f"CO2 {float(device_co2.get_state()):.0f} PPM"
        device_lux = self.get_entity(LUX_ID)
        value_lux = device_lux.get_state()
        if value_lux == 'unavailable':
            value += f" ILL {METEO_TEXT['unavailable']} LX"
        else:
            value += f" ILL {float(device_lux.get_state()):g} LX"
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_SCROLL, value)

    def powerMeterDisplay(self):
        value = f"P {float(self.totalW):.0f} _"
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, value)

    def meteoDisplay(self):
        device_tc_ext = self.get_entity(TC_EXTERNAL_ID)
        value_tc_ext = device_tc_ext.get_state()
        if value_tc_ext == 'unavailable':
            value = f"{self.meteoText}{METEO_TEXT['unavailable']}"
        else:
            value = f"{self.meteoText} {float(device_tc_ext.get_state()):.1f}"
        self.mqtt.mqtt_publish(TOPIC_HOME_BOX_CMND_DISPLAY_TEXT, value)

    def powerMeterEvent(self, event_name, data, *args, **kwargs):
        self.totalW = data['new_state']['state']
        if self.displayState == DISPLAY_STATE_POWER_METER:
            self.powerMeterDisplay()

    def meteoEvent(self, event_name, data, *args, **kwargs):
        try:
            self.meteoText = METEO_TEXT[data['new_state']['state']]
        except KeyError:
            self.meteoText = METEO_TEXT['unavailable']
        self.meteoDisplay()
