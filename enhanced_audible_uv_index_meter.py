#!/usr/bin/env python
# coding: utf-8

# # Enhanced Audible UV Index Meter
# 
# Implementing a simple **audible** UV index meter with the 
# DFRobot Gravity:Analog UV Sensor V2
# ![UV Sensor V2](img/UV_sensor_SKU__SEN0162.png)
# and the 
# DFRobot UNIHIKER
# ![UNIHIKER](img/UNIHIKER.png)
# 

# ## Connection
# The **DFRobot Gravity:Analog UV Sensor V2** must be connected to the **UNHIKER** on **P21**:
# ![P21](img/UNIHIKER_P21.png)

# In[ ]:


# -*- coding: UTF-8 -*-
# Wiring: Connect a DFRobot Gravity:Analog UV Sensor V2 to the UNIHIKER P21 pin
# Optional: Connect a Blues Notecard Carrier with a Blues Notecard Cellular to the USB port for GPS support


# In[ ]:


import time
from pinpong.board import *
from pinpong.extension.unihiker import *
from unihiker import GUI


# ## Configuration Parameters

# In[ ]:


import configparser
config = configparser.ConfigParser()

config['DEFAULT'] = {
    'Enabled': False
}


# ### UI
# Configuration for the background images etc. ...

# In[ ]:


config['UI'] = { 
    'ImageFilenamePrefix' : 'img/background_',
    'ImageFilenameSuffix' : '.jpg'
}


# ### Data Logging
# Configuration for data logging:
#     Setup the log interval in seconds and the name prefix for the data log files.

# In[ ]:


config['DataLogging'] = { 
    'Enabled': False,
    'DataLogInterval' : 60,
    'DataLogFilenamePrefix' : 'uv_meter_data.'
}


# ### Accoustic Alert
# 
# This configuration enables/disables an automatic accoustic alert when the messaured UV index reaches the given threshold *AlertUVIndex*. The alert then is repeated every *AlertInterval* seconds.

# In[ ]:


config['Alert'] = {
    'Enabled': False,
    'AlertUvIndex' : 7,
    'AlertInterval' : 60
}


# ### Risk Info Text
# Additional information or advice texts for different risk levels can be configured here ...

# In[ ]:


config['RiskInfoText'] = {
    'Enabled': True,
    'low' : 'NO PROTECTION REQUIRED - You can safely enjoy being outside!',
    'moderate' : 'PROTECTION REQUIRED - Seek shade during midday hours! Slip on a shirt, slop on sunscreen and slap on hat!',
    'high' : 'PROTECTION REQUIRED - Seek shade during midday hours! Slip on a shirt, slop on sunscreen and slap on hat!',
    'very high' : 'EXTRA PROTECTION - Avoid being outside during midday hours! Make sure you seek shade! Shirt, sunscreen and hat are a must!',
    'extreme' : 'EXTRA PROTECTION - Avoid being outside during midday hours! Make sure you seek shade! Shirt, sunscreen and hat are a must!'
}


# ### Risk Info Audio
# If an audio device is connected to the UNIHIKER via Bluetooth or USB, additional audio output from WAV files associated with the UV risk level can be configured here ..

# In[ ]:


config['RiskInfoAudio'] = {
    'Enabled': False,
    'AudioFilenamePrefix' : 'audio/UV_risk_level_',
    'AudioFilenameSuffix' : '.wav'
}


# ### Configuration File
# This configuration can be changed by maintaining a configuration file ```config.ini``` with the following format:
# ```
# [DEFAULT]
# enabled = False
# 
# [UI]
# imagefilenameprefix = img/background_
# imagefilenamesuffix = .jpg
# 
# [DataLogging]
# enabled = False
# dataloginterval = 60
# datalogfilenameprefix = uv_meter_data.
# 
# [Alert]
# enabled = False
# alertuvindex = 7
# alertinterval = 60
# 
# [RiskInfoText]
# enabled = True
# low = NO PROTECTION REQUIRED - You can safely enjoy being outside!
# moderate = PROTECTION REQUIRED - Seek shade during midday hours! Slip on a shirt, slop on sunscreen and slap on hat!
# high = PROTECTION REQUIRED - Seek shade during midday hours! Slip on a shirt, slop on sunscreen and slap on hat!
# very high = EXTRA PROTECTION - Avoid being outside during midday hours! Make sure you seek shade! Shirt, sunscreen and hat are a must!
# extreme = EXTRA PROTECTION - Avoid being outside during midday hours! Make sure you seek shade! Shirt, sunscreen and hat are a must!
# 
# [RiskInfoAudio]
# enabled = False
# audiofilenameprefix = audio/UV_risk_level_
# audiofilenamesuffix = .wav
# 
# ```

# In[ ]:


try:
    with open('config.ini', 'r') as configfile:
        config.read(configfile)
except FileNotFoundError:
    print("No config file found - using default configuration ...")
    pass


# ## Location: Blues Notecard Cellular
# For acquiring an exact location an external GPS device can be connected to the Unihiker. In this example a __[Blues Notecard Cellular](https://blues.com/notecard-cellular/)__ with its on-board GPS is used. 
# 
# ![Blues Notecard Cellular on a Blues Notecard Carrier A](img/notecard.png)
# 
# The required __[Python library](https://dev.blues.io/tools-and-sdks/firmware-libraries/python-library/)__ needs to be installed with `pip`
# 
# ```
# pip3 install note-python
# ```
# prior before running the next cell ...
# 

# In[ ]:


import notecard

import sys
import glob
import serial
import time
import datetime
import csv


# In this example the **Blues Notecard Cellular** is connected via a __[Notecarrier A](https://shop.blues.com/products/carr-al)__ via USB to the Unihiker. The following function tries to establish a connection to the card and returns a handle to communicate with it. It also sets up the GPS for periodic updates in given intervals.

# In[ ]:


def initialize_notecard_cellular(gps_periodic):
    devices = glob.glob('/dev/tty[A-Za-z]*')
    for dev in devices:
        try:
            port = serial.Serial(dev, 9600)
            card = notecard.OpenSerial(port)
            print("Notecard: Opened at "+dev)
            break;
        except (OSError, serial.SerialException, Exception):
            card = None
            pass
    if card != None:
        req = {"req":"card.version"}
        rsp = card.Transaction(req)
        print(f"Notecard: Version: {rsp}")
        req = {"req": "card.location.mode"}
        req["mode"] = "periodic"
        req["seconds"] = gps_periodic
        rsp = card.Transaction(req)
        print(f"Notecard: GPS: {rsp}")
    else:
        print("Notecard: No Notecard found!")
    return card


# The following function takes a handle for a Notecard Cellular and a dictionary as arguments. It tries to acquire time and location data from the Notecard and returns these as fields in the given dictionary.

# In[ ]:


def update_time_and_location(card,record):
    time = None
    lat = None
    lon = None
    minutes = 0
    if card != None:
        try:
            # acquire time and approx. card
            req = {"req":"card.time"}
            rsp = card.Transaction(req)
            time = rsp['time'] if 'time' in rsp else None
            lat = rsp['lat'] if 'lat' in rsp else None
            lon = rsp['lon'] if 'lon' in rsp else None
            minutes = rsp['minutes'] if 'minutes' in rsp else 0 
            # acquire location from card
            req = {"req":"card.location"}
            rsp = card.Transaction(req)
            lat = rsp['lat'] if 'lat' in rsp else lat
            lon = rsp['lon'] if 'lon' in rsp else lon
        except (OSError, serial.SerialException, Exception):
            print("Notecard: Connection lost! (Try to reconnect and restart application.)")
            card = None
            pass
    record['time'] = datetime.datetime.fromtimestamp(time+60*minutes,datetime.timezone.utc) if time != None else None
    record['lat'] = lat
    record['lon'] = lon


# ## Data Logging
# The next function writes the data in the given dict *record* in a CSV file named 
# ```<DATALOG_NAME_PREFIX><YYYY>-<MM>-<DD>.csv``` (e.g. uv_meter_data.2024-02-24.csv) if the given record has a valid time field ...

# In[ ]:


def log_record(logfile_prefix,record):
    if 'time' not in record or record['time'] == None:
        return
    filename=logfile_prefix+record['time'].strftime("%Y-%m-%d")+".csv"
    try:
        with open(filename, 'x') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=record.keys(), delimiter=',')
            writer.writeheader()
    except FileExistsError:
        pass
    try:
        with open(filename, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=record.keys(), delimiter=',')
            writer.writerow(record)
    except IOError:
        print("I/O error")


# ## Auxilliary Functions
# ### UV Index
# The UV index is calculated by comparing the voltage value read from the sensor to the following mapping table for the **GUVA-S12D** sensor
# ![UV Index](img/UV_index.png)

# In[ ]:


# Function to convert sensor output voltage (mV) to UV index
# for a GUVA-S12D based analog UV sensor based on a conversion table.
# See http://www.esp32learning.com/code/esp32-and-guva-s12sd-uv-sensor-example.php
# for conversion table ...
def uv_index(mv):
    uvi_mv_thresholds = [50, 227, 318, 408, 503, 606, 696, 795, 881, 976, 1079, 1170];
    
    for threshold in uvi_mv_thresholds:
        if (mv < threshold ):
            break
            
    i = uvi_mv_thresholds.index(threshold)
    
    if (i < 11 ):
        uvi = mv/threshold*(i+1)
    else:
        uvi = 11
        
    return uvi


# ### UV Level
# The UV level ($mW/cm^{2}$) is calculated as follows
# "The output voltage is: $Vo = 4.3 * Diode-Current-in-\mu A$.
# So if the photocurrent is $1 \mu A (\sim 9 mW/cm^2)$, the output voltage is $4.3V$."

# In[ ]:


# Function to convert sensor output voltage (mV) to mW/m^2
# for a GUVA-S12D based analog UV sensor: "The output voltage is: Vo = 4.3 * Diode-Current-in-uA.
# So if the photocurrent is 1uA (~ 9 mW/cm^2), the output voltage is 4.3V."
def uv_level(mv):
    return ( mv / 43 * 9 ) # 1 uA per 9 mW/cm^2 at 4.3V


# ### Risk level
# ![Risk level](img/uv-index-en.png)

# In[ ]:


def uv_risk_level(uvi):
    # UV risk level mapping (UV index threshold,risk level,display color)
    risk_levels=[(2,"low","green"),(5,"moderate","yellow"),(7,"high","orange"),(10,"very high","red"),(11,"extreme","violet")]
    
    for risk_level in risk_levels:
        if (uvi <= risk_level[0]):
            break
    
    return risk_level


# ### Audible UV Index
# 
# The UV index is presented as a sequence of tones played via the internal buzzer:
# 
# One base tone C at the beginning of each sequence followed by
# 
# * a number of F tones corresponding to (rounded) UV index levels 1 - 5 or
# * a number of A tones corresponding to (rounded) UV index levels 6 - 10 minus 5, following a sequence of five F tones or
# * a sequence of five F tone followed by five A tone and one C tone (next octave) for (rounded) UV index levels 11+.
# For example, if the UV index is 4 the tone sequence is C,F,F,F,F and if the UV index is 6.7 the tone sequence is C,F,F,F,F,F,A,A
# 
# Represented as score the tone sequence looks like shown in the following image:
# ![Score](img/audible_uv_meter_score.png)

# In[ ]:


def buzzer_play_uv_index_melody(uvi):
    # Play the corresponding tone sequence for the measured UV index on the buzzer:
    # C5 (F5){UV index} for an UV index < 6,
    # C5 (F5){5} (A5){UV index - 5} for an UV index 6 - 10 and
    # C5 (F5){5} (A5){5} C6 for UV index 11 ...
    buzzer.set_tempo(4, 160)
    buzzer.pitch(523, 4) # C5
    for i in range(0,uvi):
        print(f"Buzz! {i}")
        if i < 5:
            buzzer.pitch(698, 4) # F5
        elif i < 10:
            buzzer.pitch(880, 4) # A5
        else:
            buzzer.pitch(1046, 4) # C6
        buzzer.stop()        


# ### Optional: Audio output on external device
# 
# If additional audio device - e.g., a Bluetooth headset or speaker - can be connected to the UNIHIKER, additional audible information can be produced by playing an audio file (WAV) associated to the determined risk level.
# To enable this feature the __[simpleaudio package](https://simpleaudio.readthedocs.io/en/latest/index.html)__ needs to be installed with `pip`
# 
# ```
# pip3 install simpleaudio
# ```
# before running the next cell ...

# In[ ]:


try:
    import simpleaudio as sa

    def playaudio(tag):
        if not config.getboolean('RiskInfoAudio','Enabled'):
            return
        tag = tag.replace(" ", "_")
        path_to_file=config['RiskInfoAudio']['AudioFilenamePrefix']+tag+config['RiskInfoAudio']['AudioFilenameSuffix']
        try:
            print(f"trying to load WAV file '{path_to_file}'' ...")
            wave_obj = sa.WaveObject.from_wave_file(path_to_file)
            print(f"playing wave object ...")
            play_obj = wave_obj.play()
            print(f"waiting ...")
            play_obj.wait_done()
            print(f"completed.")
        except FileNotFoundError:
            pass
except ImportError:
    def playaudio(tag):
        return


# ## Application
# 
# ### Interrupt handler for button

# In[ ]:


def btn_a_rasing_handler(pin):  # Interrupt event callback function for button A rising edge
    global btn_a_pressed
    btn_a_pressed = True
    print ("button A pressed!")


# ### Initialization

# In[ ]:


Board().begin() # Initialize the UNIHIKER
gui = GUI() # Instantiate the GUI class


# ### Analog input configuration

# In[ ]:


# ADC analog input pins supported: P0 P1 P2 P3 P4 P10 P21 P22
adc21 = Pin(Pin.P21, Pin.ANALOG)  # Initialize the pin as an analog input 


# ### Interrupt handling for button A

# In[ ]:


btn_a_pressed = False
button_a.irq(trigger=Pin.IRQ_RISING, handler=btn_a_rasing_handler)  # Trigger on rising edge


# ### GUI Setup
# 
# The GUI displays the measured UV index and the associated risk level on a background image with a tint of the color associated with the risk level: 
# ![Screenshot](img/screenshot.jpg)

# In[ ]:


# GUI: 
#   Display a background image with the color tint of the risk level,
#   the UV index and the risk level text ...
try:
    image_filename = config['UI']['ImageFilenamePrefix']+"green"+config['UI']['ImageFilenameSuffix']
    bg = gui.draw_image(x=0, y=0, h=320, w=240, image=image_filename)
except FileNotFoundError:
    bg = None
    gui.fill_rect(x=0, y=0, h=320, w=240, color="gray")
    pass

title = gui.draw_text(x=120, y=20, text="UV Index", origin="center", color="white", font_size=25)

uv_index_text = gui.draw_digit(x=120, y=100, text="UVI", origin="center", color="white", font_size=50) # Display UV index using 7-segment font

uv_risk_text = gui.draw_text(x=120, y=160, text="N/A", origin="center", color="white", font_size=25)

if config.getboolean('RiskInfoText','Enabled'):
    risk_info_text = gui.draw_text(x=120, y=240, text="...", origin="center", color="white", font_size=10, w=220)


# 
# ### Loop

# In[ ]:


r0 = None

datalog_interval = int(config['DataLogging']['DataLogInterval'])
datalog_record = {}
datalog_time = 0

alert_uv_index = int(config['Alert']['AlertUvIndex'])
alert_interval = int(config['Alert']['AlertInterval'])
alert_time = 0


# In[ ]:


# Notecard initialization
if config.getboolean('DataLogging','Enabled'):
    notecard_cellular = initialize_notecard_cellular(int(datalog_interval/2))


# In[ ]:


while True:
    # Read the sensor value ...
    v = adc21.read_analog()  # Read the analog signal value from pin A0
    print(f"Sensor voltage: {v}")
        
    # Calculate UV index, level and risk ...
    i = uv_index(v)
    l = uv_level(v)
    r = uv_risk_level(i) 
    print(f"UV index: {i} - UV level: {l} - Risk level: {r}")
    
    # Update UI ...
    print("updating UI ...")
    uv_index_text.config(text="%.2f" % i)
    if r0 != r: # Update the background image and the risk level text only if the risk level changed ...
        if bg != None:
            try:
                image_filename = config['UI']['ImageFilenamePrefix']+r[2]+config['UI']['ImageFilenameSuffix']
                bg.config(image=image_filename)    
            except FileNotFoundError:
                bg = None
                pass
        uv_risk_text.config(text=r[1])
        if config.getboolean('RiskInfoText','Enabled'):
            risk_info_text.config(text=config['RiskInfoText'][r[1]])
    print("UI updated.")
           
    # Audio output
    if  btn_a_pressed == True:
        print("audio output ...")
        btn_a_pressed = False
        if config.getboolean('RiskInfoAudio','Enabled'):
            playaudio(r[1])
        else:
            buzzer_play_uv_index_melody(round(i))
        print("audio output: completed.")
        
    # Data logging ...
    if config.getboolean('DataLogging','Enabled') and time.time() - datalog_time >= datalog_interval:
        print("data logging ...")
        datalog_record['uv_index'] = i
        datalog_record['uv_level'] = l
        update_time_and_location(notecard_cellular,datalog_record)
        log_record(config["DataLogging"]["DataLogFilenamePrefix"],datalog_record)
        datalog_time = time.time()
        print("data logging completed.")
        
    # Automatic acoustic alert if a defined UV index threshold has been reached ... 
    if config.getboolean('Alert','Enabled') == True and i >= alert_uv_index and time.time() - alert_time >= alert_interval:
        print("alert ...")
        buzzer_play_uv_index_melody(round(i))
        alert_time = time.time()

    r0 = r
    
    print("sleeping ...")
    time.sleep(1) # Wait for a second ..


# ## Test
# ![Test](img/test.jpg)

# with Notecard connected:
# ![Test with Notecard](img/test_with_notecard.jpg)
