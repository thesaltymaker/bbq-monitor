# Wiring for ESP32-S2 QT PY

# MAX31855
#     VIN    -> ESP32-S2 3V
#     GND    -> ESP32-S2 GND
#     DO     -> ESP32-S2 MI
#     CS     -> ESP32-S2 A3
#     CLK    -> ESP32-S2 SCK
# ESP32-S2 QT PY
#     SCK    -> MAX31855 CLK
#     MI     -> MAX31855 DO
#     MO
#     3V     -> MAX31855 VIN
#     GND    -> MAX31855 GND
#     5V
#     A0
#     A1
#     A2
#     A3     -> MAX31855 CS
#     SDA
#     SCL
#     i2c bus for stemma connector is i2c = busio.I2C(board.SCL1, board.SDA1)

from adafruit_pcf8523.pcf8523 import PCF8523  # Real Time Clock for accurate logging
import board
import neopixel
import time
import json
from adafruit_ntp import NTP
from digitalio import DigitalInOut
import busio
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests

# import rtc
import adafruit_vl53l4cd  # Time of flight sensor
import adafruit_max31855  # Barrel Chamber Temp sensor
import adafruit_ahtx0  # Pellet hopper Temp sensor


import digitalio
import neopixel


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("My secrets are kept in secrets.py, please add them there!")
    raise

print("My MAC addr:", [hex(i) for i in wifi.radio.mac_address])

print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print(
        "\t%s\t\tRSSI: %d\tChannel: %d"
        % (str(network.ssid, "utf-8"), network.rssi, network.channel)
    )
wifi.radio.stop_scanning_networks()

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

ipv4 = ipaddress.ip_address("8.8.4.4")
print("Ping google.com: %f ms" % (wifi.radio.ping(ipv4) * 1000))

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())
msg = "hello from esp32-s2"
tts = "True"


radio = wifi.radio
pool = socketpool.SocketPool(radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

print("here")
# print(log_timestamp)
# requests.post(secrets["webhook_url"], json={"content" : msg, "tts" : tts})
i2c = busio.I2C(board.SCL1, board.SDA1)  # uses board.SCL and board.SDA

rtc = PCF8523(i2c)  # i2c address 0x68
# rtc = RTC()

spi = board.SPI()
cs = digitalio.DigitalInOut(board.A3)
pixels = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixels.fill((0, 255, 0))
max31855 = adafruit_max31855.MAX31855(spi, cs)
vl53 = adafruit_vl53l4cd.VL53L4CD(i2c)
vl53.start_ranging()
hopper_aht20 = adafruit_ahtx0.AHTx0(i2c)


response = requests.get(
    "https://timeapi.io/api/time/current/zone?timeZone=America%2FNew_York"
)


# set the time after being offline for so long
if response.status_code == 200:

    # Extract values
    year = response.json()["year"]
    month = response.json()["month"]
    day = response.json()["day"]
    hour = response.json()["hour"]
    minute = response.json()["minute"]
    second = response.json()["seconds"]
    dayOfWeek = response.json()["dayOfWeek"]
    isdst = response.json()["dstActive"]

    dayofweek = 0
    if dayOfWeek == "Monday":
        dayofweek = 0
    elif dayOfWeek == "Tuesday":
        dayofweek = 1
    elif dayOfWeek == "Wednesday":
        dayofweek = 2
    elif dayOfWeek == "Thrusday":
        dayofweek = 3
    elif dayOfWeek == "Friday":
        dayofweek = 4
    elif dayOfWeek == "Saturday":
        dayofweek = 5
    elif dayOfWeek == "Sunday":
        dayofweek = 6
    else:
        dayOfWeek = 0

    isDST = 0
    if isdst == "true":
        isDST = 1

    # Create a struct_time tuple
    dt_tuple = time.struct_time(
        (year, month, day, hour, minute, second, dayofweek, -1, isDST)
    )

    # Set RTC
    rtc.datetime = dt_tuple
    print(f"System Time: {rtc.datetime}")
else:
    print("Setting time failed")

current_time = time.time()
now = time.localtime(current_time)
log_timestamp = now


hopper_lid_open_count = 0
hopper_depth = 40  # distance in CM from sonar sensor to "Hopper Empty" depth
dist1 = 20
dist2 = 20
dist3 = 20
dist4 = 20
dist5 = 20
dist6 = 20
chamber_temp = 75
iteration = 0
distance = 20
tempC = 30
tempF = 75
msg = ""
hopper_temp = 80
hopper_humidity = 60


while True:
    try:
        tempC = max31855.temperature
        tempF = ((tempC * 9) / 5) + 32
    except:
        print("chamber temp not read")
    chamber_temp = round(tempF, 1)
    print("Chamber TempF: " + str(chamber_temp))
    # Get hopper temp and humidity
    hopper_temp = round(hopper_aht20.temperature * 9 / 5 + 32, 1)
    hopper_humidity = round(hopper_aht20.relative_humidity, 1)
    print(
        "Hopper_TempF: "
        + str(hopper_temp)
        + " Hopper_Humidity: "
        + str(hopper_humidity)
    )

    # Get ToF sensor data
    while not vl53.data_ready:
        pass
    vl53.clear_interrupt()
    distance = vl53.distance

    dist6 = dist5
    dist5 = dist4
    dist4 = dist3
    dist3 = dist2
    dist2 = dist1

    if distance < 60.0:
        dist1 = distance
    else:
        print("time of flight distance read problem")

    avg_distance = round((dist1 + dist2 + dist3 + dist4 + dist5 + dist6) / 6, 1)
    print("Hopper avg distance: " + str(avg_distance))

    # calculate LED color from Green to Red for needing to be filled
    hopper_pct = (avg_distance - 10) / hopper_depth
    if hopper_pct > 1.0:
        hopper_pct = 1.0
    elif hopper_pct < 0.0:
        hopper_pct = 0.0
    RGB_Red = int(round((255 * hopper_pct), 0))
    RGB_Green = int(255 - RGB_Red)
    # print(str(hopper_pct) + " " + str(RGB_Red) + " " + str(RGB_Green) )
    pixels.fill((RGB_Red, RGB_Green, 0))

    # Grab the log timestamp
    current_time = time.time()
    now = time.localtime(current_time)

    if iteration % 20 == 7:
        now = rtc.datetime
        # print(t)     # uncomment for debugging
        now_date = '{}/{}/{}  '.format(now.tm_year, now.tm_mon,now.tm_mday)
        print(
            "The date is {}/{}/{}".format(
                now.tm_mday, now.tm_mon, now.tm_year
            )
        )
        now_time = ' {}:{:02}:{:02}'.format(now.tm_hour, now.tm_min, now.tm_sec)
        print("The time is {}:{:02}:{:02}".format(now.tm_hour, now.tm_min, now.tm_sec))

        log_timestamp = now_date + now_time
        print(log_timestamp)
        log_message = (
            log_timestamp
            + "   Hopper_empty(cm): "
            + str(avg_distance)
            + " Chamber_Temp(F): "
            + str(chamber_temp)
            + " Hopper_Temp(F): "
            + str(hopper_temp)
            + " Hopper_humidity: "
            + str(hopper_humidity)
        )
        requests.post(secrets["webhook_url"], json={"content": log_message, "tts": tts})
        print(log_message)
    iteration = iteration + 1
    time.sleep(6)

