# home_1x8

#### 12.2.2023

#### DISPLAY CONFIGURATION:
Heltec Wifi kit 8 con 7 segmenti perche difettoso l'OLED<br>
CLK --> D7 GPIO 13<br>
DIO --> D6 GPIO 12<br>
istruzioni per il TM1637 4 digits, 7 segmenti<br>
https://tasmota.github.io/docs/TM163x/#supported-displays<br>

#### RULES:
```yaml
Rule1 ON Time#Initialized DO DisplayClock 2; ENDON
Rule1 1
```

#### BUTTONS:
```python
SetOption73 1
05:40:57.665 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"SINGLE"}}
05:41:01.575 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"SINGLE"}}
05:44:50.187 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"HOLD"}}
05:45:03.970 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"SINGLE"}}
05:45:08.022 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"DOUBLE"}}
05:45:12.184 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"TRIPLE"}}
05:45:16.521 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"PENTA"}}
05:45:33.532 MQT: stat/tasmota_144AF2/RESULT = {"Button1":{"Action":"QUAD"}}
```