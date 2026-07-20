import serial
import json
import time
import sys


SERIAL_PORT = '/dev/cu.usbmodem11101' 
BAUD_RATE = 115200

print(f"🔌 正在連線到 Pico W ({SERIAL_PORT})...")

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.5, rtscts=True, dsrdtr=True)
    print("✅ 連線成功！正在強制監聽底層訊號...\n")
    
    
    ser.write(b'\x04') 
    time.sleep(0.5)

    while True:
        if ser.in_waiting > 0:
            raw_data = ser.readline()
            
            
            print(f"🤖 Pico 原始訊號 >>> {raw_data.decode('utf-8', errors='ignore').strip()}")
            sys.stdout.flush()
            
            line = raw_data.decode('utf-8', errors='ignore').strip()
            
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    with open("data.json", "w") as f:
                        json.dump(data, f)
                except:
                    pass
        else:            
            time.sleep(0.01)

except KeyboardInterrupt:
    print("\n中斷程式。")
except Exception as e:
    print(f"❌ 錯誤: {e}")