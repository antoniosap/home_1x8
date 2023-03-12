#
# home_1x8 controller 12.2.2023
# hardware: ESP8266, 4 buttons, 2x LED 8 digits
# firmware: tasmota 12.3.0
# for productions run inside ha-appdaemon add-on
#
# button left   = meteo: single mostra meteo + meteo unhold, double meteo hold
# button center = power meter: single mostra power, double mostra clock
# button right  = boiler: single simple toggle on/off
#

TOPIC_HOME_1X8_RESULT = "stat/tasmota_1DAA95/RESULT"
TOPIC_HOME_1X8_CMND = "cmnd/tasmota_1DAA95/"
TOPIC_HOME_1X8_CMND_DIMMER = TOPIC_HOME_1X8_CMND + "DisplayDimmer"
TOPIC_HOME_1X8_CMND_DISPLAY_TEXT = TOPIC_HOME_1X8_CMND + "DisplayText"
TOPIC_HOME_1X8_CMND_DISPLAY_FLOAT = TOPIC_HOME_1X8_CMND + "DisplayFloat"
TOPIC_HOME_1X8_CMND_DISPLAY_CLOCK = TOPIC_HOME_1X8_CMND + "DisplayClock"
TOPIC_HOME_1X8_CMND_DISPLAY_SCROLL = TOPIC_HOME_1X8_CMND + "DisplayScrollText"

DISPLAY_LEN = 8
POWER_METER_EVENT = "sensor.total_watt"
TC_EXTERNAL_ID = "sensor.ewelink_th01_b0071325_temperature"
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
        self.mqtt.mqtt_subscribe(topic=TOPIC_HOME_1X8_RESULT)
        self.mqtt.listen_event(self.mqttEvent, "MQTT_MESSAGE", topic=TOPIC_HOME_1X8_RESULT, namespace='mqtt')
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
        # if 'IrReceived' in pld.keys() and pld['IrReceived']['Protocol'] == "UNKNOWN" and pld['IrReceived']['Bits'] == 34:
        #    self.IrReceivedDisplay(pld['IrReceived']['Hash'])

    def displayUpdateEMinutely(self, *args, **kwargs):
        weekday = dt.datetime.now().weekday() + 1  # lun == 1
        # display dimmer time range
        if self.now_is_between("22:00:00", "08:00:00"):
            if not self.insideDimmerRange:
                self.insideDimmerRange = True
                self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DIMMER, 20)
        else:
            if self.insideDimmerRange:
                self.insideDimmerRange = False
                self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DIMMER, 100)
        # default state
        self.displayState = DISPLAY_STATE_CLOCK
        if self.meteoHoldOption:
            self.displayState = DISPLAY_STATE_METEO
            self.meteoDisplay()
        else:
            # power meter time range
            if ((self.now_is_between("18:00:00", "22:00:00") or
                 self.now_is_between("05:00:00", "07:00:00")) and
                    weekday in [1, 2, 3, 4, 5]):
                self.displayState = DISPLAY_STATE_POWER_METER
            if ((self.now_is_between("05:00:00", "23:00:00")) and
                    weekday in [6, 7]):
                self.displayState = DISPLAY_STATE_POWER_METER
        #
        # timed actions
        #
        if self.displayState == DISPLAY_STATE_CLOCK:
            self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_CLOCK, 2)
        elif self.displayState == DISPLAY_STATE_POWER_METER:
            pass
        elif self.displayState == DISPLAY_STATE_METEO:
            pass
        elif self.displayState == DISPLAY_STATE_CO2_LUX:
            pass
        else:
            self.displayState = DISPLAY_STATE_CLOCK

    def boilerOn(self):
        self.call_service("switch/turn_on", entity_id=ENTITY_SWITCH_BOILER)
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_TEXT, "BOIL ON")

    def boilerOff(self):
        self.call_service("switch/turn_off", entity_id=ENTITY_SWITCH_BOILER)
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_TEXT, "BOIL OFF")

    def clockDisplay(self):
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_CLOCK, 2)

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
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_SCROLL, value)

    def powerMeterDisplay(self):
        value = f"P {float(self.totalW):.0f}"
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_TEXT, value)

    def meteoDisplay(self):
        device_tc_ext = self.get_entity(TC_EXTERNAL_ID)
        value = f"{self.meteoText} {float(device_tc_ext.get_state()):.1f}"
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_TEXT, value)

    def powerMeterEvent(self, event_name, data, *args, **kwargs):
        if self.displayState == DISPLAY_STATE_POWER_METER:
            self.totalW = data['new_state']['state']
            self.powerMeterDisplay()

    def meteoEvent(self, event_name, data, *args, **kwargs):
        try:
            self.meteoText = METEO_TEXT[data['new_state']['state']]
        except KeyError:
            self.meteoText = METEO_TEXT['unavailable']
        self.meteoDisplay()

    def IrReceivedDisplay(self, value):
        value = value.replace('0x', '')
        self.mqtt.mqtt_publish(TOPIC_HOME_1X8_CMND_DISPLAY_TEXT, value)
