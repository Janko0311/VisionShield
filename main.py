import machine, network, ujson, time, uasyncio as asyncio
from machine import Pin, PWM

# --- Hardware Configuration ---
# Trigger Pin (Output) and Echo Pin (Input) for HC-SR04 Ultrasonic Sensor
trigger, echo = Pin(13, Pin.OUT), Pin(12, Pin.IN)

# Servo Motor initialization on Pin 15 with 50Hz frequency
servo = PWM(Pin(15))
servo.freq(50)

# Global dictionary to store the latest radar metrics
current_data = {"angle": 90, "distance": 999.0}

def get_distance():
    """
    Measures distance using the HC-SR04 ultrasonic sensor.
    Returns distance in cm (rounded to 1 decimal place).
    """
    trigger.low()
    time.sleep_us(2)
    trigger.high()
    time.sleep_us(10)
    trigger.low()
    
    timeout = 30000 # 30ms timeout limit
    start = time.ticks_us()
    
    # Wait for echo pin to go HIGH
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout: 
            return 999.0
    off = time.ticks_us()
    
    # Wait for echo pin to go LOW
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), start) > timeout: 
            return 999.0
    on = time.ticks_us()
    
    return round(((on - off) * 0.0343) / 2, 1)

async def radar_loop():
    """
    Continuously sweeps the servo motor from 30 to 150 degrees and back.
    Pacing is adjusted to 120ms to provide structural stability for TTS audio syncing.
    """
    global current_data
    while True:
        # Forward Sweep: 30 degrees to 150 degrees
        for angle in range(30, 151, 15):
            servo.duty_u16(int(1500 + (angle / 180) * 6500))
            
            # 🎯 OPTIMIZATION: Slowed down from 60ms to 120ms to prevent browser speech buffer congestion
            await asyncio.sleep_ms(120) 
            
            current_data["angle"], current_data["distance"] = angle, get_distance()
            print(ujson.dumps(current_data)) # Stream data to Mac over USB Serial

        # Backward Sweep: 150 degrees down to 30 degrees
        for angle in range(150, 29, -15):
            servo.duty_u16(int(1500 + (angle / 180) * 6500))
            
            # 🎯 OPTIMIZATION: Slowed down from 60ms to 120ms to prevent browser speech buffer congestion
            await asyncio.sleep_ms(120) 
            
            current_data["angle"], current_data["distance"] = angle, get_distance()
            print(ujson.dumps(current_data)) # Stream data to Mac over USB Serial

def setup_wifi():
    """
    Initializes the Wi-Fi Access Point (Dual-mode support fallback).
    """
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(ssid="VisionShield_OS_Radar")
    while not ap.active(): 
        pass
    print("🎉 OS AP Established!\n👉 Connect Wi-Fi: VisionShield_OS_Radar\n🔗 URL: http://192.168.4.1")

async def handle_client(reader, writer):
    """
    Handles incoming HTTP requests.
    """
    global current_data
    request = await reader.read(1024)
    req_str = request.decode('utf-8')
    
    if "GET /data" in req_str:
        res = "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n" + ujson.dumps(current_data)
    elif "GET /style.css" in req_str:
        with open("style.css", "r") as f: res = "HTTP/1.1 200 OK\r\nContent-Type: text/css\r\n\r\n" + f.read()
    elif "GET /app.js" in req_str:
        with open("app.js", "r") as f: res = "HTTP/1.1 200 OK\r\nContent-Type: application/javascript\r\n\r\n" + f.read()
    else:
        with open("visionshield-os.html", "r") as f: res = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + f.read()
        
    writer.write(res.encode('utf-8'))
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def main():
    """
    Main task orchestrator to run Wi-Fi Server and Radar sweeping concurrently.
    """
    setup_wifi()
    await asyncio.start_server(handle_client, "0.0.0.0", 80)
    await asyncio.gather(radar_loop())

# --- Application Entry Point ---
try: 
    asyncio.run(main())
except KeyboardInterrupt: 
    print("System Shutdown")