#include <Arduino.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <Servo.h>

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

#define SERVICE_UUID           "12345678-1234-1234-1234-123456789abc"
#define CHARACTERISTIC_UUID    "87654321-4321-4321-4321-987654321abc"

// Define servo objects and pins
Servo servos[5];
int servoPins[5] = {5, 18, 19, 21, 22};  // Update these to match your wiring

class MyCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    std::string value = pCharacteristic->getValue();
    if (value.length() > 0) {
      Serial.print("Received: ");
      Serial.println(value.c_str());

      // Parse comma-separated values
      float values[5];
      int idx = 0;
      char *ptr = strtok((char *)value.c_str(), ",");
      while (ptr != NULL && idx < 5) {
        values[idx++] = atof(ptr);
        ptr = strtok(NULL, ",");
      }

      // Map 0-1 float values to servo angles (0-180)
      for (int i = 0; i < 5; i++) {
        int angle = map(values[i] * 100, 0, 100, 0, 180);
        servos[i].write(angle);
      }
    }
  }
};

class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
  }
  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
  }
};

void setup() {
  Serial.begin(115200);

  // Attach servos to pins
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
  }

  // Setup BLE
  BLEDevice::init("ESP32_Robotic_Hand");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);

  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );

  pCharacteristic->setCallbacks(new MyCallbacks());
  pCharacteristic->addDescriptor(new BLE2902());

  pService->start();

  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();

  Serial.println("Waiting for BLE client...");
}

void loop() {
}
