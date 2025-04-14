import cv2
import mediapipe as mp
import time
import numpy as np
from bleak import BleakClient

# Replace with your ESP32 BLE device address
BLE_DEVICE_ADDRESS = "XX:XX:XX:XX:XX:XX"  # You can find this address using a BLE scanner
CHARACTERISTIC_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  # UUID for the characteristic to write to

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

FINGER_TIPS = [8, 12, 16, 20, 4]

def get_finger_bends(landmarks):
    bends = []
    for tip in FINGER_TIPS:
        base = tip - 2
        if tip == 4:
            bend = abs(landmarks[tip].x - landmarks[base].x)
        else:
            bend = abs(landmarks[tip].y - landmarks[base].y)
        bends.append(bend)
    return bends

def bend_to_value(bend, max_bend=0.1):
    value = np.interp(bend, [0, max_bend], [0, 1])
    return value

async def send_finger_values(client, finger_bends):
    values = [bend_to_value(bend) for bend in finger_bends]
    data = ",".join(map(str, values))  # Send values as comma-separated string
    await client.write_gatt_char(CHARACTERISTIC_UUID, data.encode())
    print("[SEND]", data)

async def main():
    async with BleakClient(BLE_DEVICE_ADDRESS) as client:
        if not client.is_connected:
            print("Failed to connect to the device!")
            return

        cap = cv2.VideoCapture(0)
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    continue

                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(rgb)

                if results.multi_hand_landmarks:
                    for handLms in results.multi_hand_landmarks:
                        mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
                        finger_bends = get_finger_bends(handLms.landmark)
                        await send_finger_values(client, finger_bends)

                cv2.imshow("Hand to Servo Control", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except KeyboardInterrupt:
            print("\n[INFO] Exiting...")

        finally:
            cap.release()
            cv2.destroyAllWindows()

# Run the BLE communication
import asyncio
asyncio.run(main())