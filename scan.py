import time
import board
from digitalio import DigitalInOut, Pull
from analogio import AnalogIn
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_hid.mouse import Mouse

# --- Hardware Setup ---
# VRx -> GP26, VRy -> GP27, SW -> GP22
analog_x = AnalogIn(board.GP26)
analog_y = AnalogIn(board.GP27)
button = DigitalInOut(board.GP22)
button.switch_to_input(pull=Pull.UP)

# --- BLE & HID Setup ---
ble = BLERadio()
ble.name = "PicoNativeMouse"
hid = HIDService()
advertisement = ProvideServicesAdvertisement(hid)
advertisement.appearance = 962  # Standard Bluetooth SIG appearance code for a Mouse

# Start advertising
ble.start_advertising(advertisement)
mouse = Mouse(hid.devices)

print("🔍 Broadcasting BLE HID Mouse as 'PicoNativeMouse'...")

while True:
    if ble.connected:
        print("🔗 Connected to Mac!")
        while ble.connected:
            x_raw = analog_x.value
            y_raw = analog_y.value
            btn_pressed = not button.value  # True when pressed
            
            # Calibrated center & deadzone
            center_x = 47000
            center_y = 51500
            deadzone = 4000
            
            dx, dy = 0, 0
            
            x_diff = x_raw - center_x
            y_diff = y_raw - center_y
            
            if abs(x_diff) > deadzone:
                scaled = (abs(x_diff) - deadzone) / (32768 - deadzone)
                dx = int(scaled * 10) * (1 if x_diff > 0 else -1)
                dx = max(-127, min(127, dx))
                
            if abs(y_diff) > deadzone:
                scaled = (abs(y_diff) - deadzone) / (32768 - deadzone)
                dy = int(scaled * 10) * (1 if y_diff > 0 else -1)
                dy = max(-127, min(127, dy))
            
            # Send movement or clicks natively over Bluetooth HID
            if dx != 0 or dy != 0:
                mouse.move(x=dx, y=dy)
                
            if btn_pressed:
                mouse.press(Mouse.LEFT_BUTTON)
            else:
                mouse.release(Mouse.LEFT_BUTTON)
                
            time.sleep(0.01)  # 100Hz polling rate
            
    else:
        if not ble.advertising:
        # Re-advertise if connection dropped
            ble.start_advertising(advertisement)
        time.sleep(0.5)
