# bbq-monitor
 Overview

This project runs on an ESP32-S2 QT PY board to monitor environmental and process parameters for a barrel chamber and pellet hopper system. It integrates multiple Adafruit sensors—including several Stemma-enabled devices—to read temperature, humidity, and distance data. The device synchronizes its time via an online API, logs measurements with a real-time clock, and provides visual feedback using a NeoPixel LED.
Key Components

    MAX31855 Thermocouple Amplifier (Barrel Chamber Temperature Sensor):

        Interface: SPI

        Purpose: Reads the barrel chamber temperature.

    Adafruit PCF8523 RTC (Real Time Clock):

        Interface: I2C (via the Stemma connector)

        Purpose: Provides accurate timestamping for data logging.

    Adafruit VL53L4CD Time-of-Flight Sensor (Distance Sensor):

        Interface: I2C (Stemma-enabled)

        Purpose: Measures distance to determine the pellet hopper’s fill level.

    Adafruit AHTx0 Sensor (Pellet Hopper Temperature & Humidity Sensor):

        Interface: I2C (Stemma-enabled)

        Purpose: Monitors the temperature and humidity of the pellet hopper.

    NeoPixel LED:

        Purpose: Displays a color indication (green to red) based on the hopper’s fill level.

Features & Workflow

    WiFi Connectivity & Time Sync:

        Scans available networks and connects using credentials stored in secrets.py.

        Retrieves current time from an external API to update the RTC (PCF8523).

    Sensor Data Acquisition:

        Reads barrel chamber temperature via the MAX31855.

        Monitors hopper conditions (temperature and humidity) using the AHTx0.

        Measures distance using the VL53L4CD; averages multiple readings to gauge the pellet hopper’s fill level.

    Visual Feedback:

        Adjusts the NeoPixel LED color based on the hopper fill percentage—from green (full) to red (nearly empty).

    Data Logging:

        Periodically compiles a log message with timestamped sensor data.

        Sends the log message via an HTTP POST to a specified webhook URL for remote monitoring or alerting.

    Robust Operation:

        Implements error handling for sensor read failures and connectivity issues to ensure continuous operation.

Wiring

    MAX31855 Sensor Wiring:

        VIN: Connected to ESP32-S2 3V

        GND: Connected to ESP32-S2 GND

        DO: Connected to ESP32-S2 MI

        CS: Connected to ESP32-S2 A3

        CLK: Connected to ESP32-S2 SCK

    I2C Bus (Stemma Connector):

        Used for connecting the PCF8523 RTC, VL53L4CD, and AHTx0 sensors via busio.I2C(board.SCL1, board.SDA1)
