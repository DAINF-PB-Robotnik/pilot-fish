/**
 * @file ultrasonic_8_sensor_array.ino
 * @brief Reads 8 HC-SR04 ultrasonic sensors sequentially on an Arduino Mega.
 *
 * This firmware is designed to run on an Arduino Mega. It continuously measures
 * distances from 8 ultrasonic sensors and sends the collected data over USB
 * serial when it receives a specific character ('R') from the host.
 *
 * Communication Protocol:
 * - Host sends: 'R' (char)
 * - Arduino replies: A single line string with 8 distance values (in cm, with
 * one decimal place), separated by semicolons. e.g., "15.2;30.0;Err;..."
 * "Err" indicates a timeout or failed reading for that sensor.
 */
#include <Arduino.h>

//==============================================================================
// SENSOR CONFIGURATION
//==============================================================================

// The total number of ultrasonic sensors connected.
const uint8_t NUM_SENSORS = 8;

// Pin assignments for the HC-SR04 sensors' TRIG and ECHO pins.
// The order here maps to the logical sensor index (0 to 7).
// Sensor 0 -> TRIG=24, ECHO=25
// Sensor 1 -> TRIG=28, ECHO=29
// ...
// Sensor 7 -> TRIG=52, ECHO=53
const uint8_t TRIG_PINS[NUM_SENSORS] = {24, 28, 32, 36, 40, 44, 48, 52};
const uint8_t ECHO_PINS[NUM_SENSORS] = {25, 29, 33, 37, 41, 45, 49, 53};

// Maximum wait time for the echo pulse from a sensor, in microseconds.
// This value determines the maximum measurable distance.
// 12000µs corresponds to a max range of approximately 2 meters.
// (12000µs * 0.0343 cm/µs) / 2 ≈ 205 cm
const unsigned long TIMEOUT_US = 12000UL;

// Buffer to store the latest distance readings for all sensors in millimeters.
// A value of -1 indicates a failed reading (error).
int16_t distances_mm[NUM_SENSORS];


//==============================================================================
// SETUP FUNCTION
//==============================================================================

void setup() {
  // Initialize the serial communication with the host computer.
  Serial.begin(115200);

  // Configure the GPIO pins for all sensors.
  for (uint8_t i = 0; i < NUM_SENSORS; i++) {
    // Set TRIG pins as OUTPUT and ensure they are initially LOW.
    pinMode(TRIG_PINS[i], OUTPUT);
    digitalWrite(TRIG_PINS[i], LOW);
    // Set ECHO pins as INPUT.
    pinMode(ECHO_PINS[i], INPUT);
  }
}


//==============================================================================
// SENSOR MEASUREMENT
//==============================================================================

/**
 * @brief Measures the distance from a single specified sensor.
 * @param idx The index of the sensor to measure (0 to NUM_SENSORS-1).
 * @return The distance in millimeters, or -1 if the reading times out.
 */
int16_t measureSensor(uint8_t idx) {
  // 1) Trigger the sensor by sending a 10µs high pulse on the TRIG pin.
  digitalWrite(TRIG_PINS[idx], LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PINS[idx], HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PINS[idx], LOW);

  // 2) Read the duration of the echo pulse. The pulseIn() function waits for the
  //    pin to go HIGH, starts timing, and then waits for the pin to go LOW.
  //    It returns the pulse length in microseconds or 0 if it times out.
  unsigned long duration_us = pulseIn(ECHO_PINS[idx], HIGH, TIMEOUT_US);

  // If duration is 0, it means no echo was received within the timeout period.
  if (duration_us == 0) {
    return -1; // Return -1 to indicate an error.
  }

  // 3) Convert the pulse duration to distance in millimeters.
  //    Formula: distance = (duration / 2) * speed_of_sound
  //    Speed of sound ≈ 0.343 mm/µs
  //    To avoid floating-point math, we use integer arithmetic:
  //    (duration_us * 343) / 2000
  return (duration_us * 343UL) / 2000;
}


//==============================================================================
// MAIN LOOP
//==============================================================================

void loop() {
  // Continuously measure all sensors in sequence and update the global buffer.
  // This ensures that when the host requests data, the latest values are ready.
  for (uint8_t i = 0; i < NUM_SENSORS; i++) {
    distances_mm[i] = measureSensor(i);
    // Optional: a small delay can improve stability for some sensor models,
    // allowing any residual echoes to dissipate.
    // delay(5);
  }

  // Check if the host has sent any data over USB.
  if (Serial.available()) {
    // If the received character is 'R', send back the distance data.
    if (Serial.read() == 'R') {
      for (uint8_t i = 0; i < NUM_SENSORS; i++) {
        // Add a semicolon separator before each value except the first one.
        if (i > 0) {
          Serial.print(';');
        }
        
        int16_t mm = distances_mm[i];
        if (mm < 0) {
          // If the distance is -1, print "Err" to indicate a sensor error.
          Serial.print("Err");
        } else {
          // Send the distance formatted as centimeters with one decimal place.
          // Example: 152mm becomes "15.2"
          Serial.print(mm / 10);      // Integer part in cm (e.g., 152 / 10 = 15)
          Serial.print('.');
          Serial.print(abs(mm % 10));  // Decimal part (e.g., 152 % 10 = 2)
        }
      }
      // Terminate the message with a newline character.
      Serial.println();
    }

    // Clear any other characters from the serial receive buffer to prevent
    // processing old requests.
    while (Serial.available()) {
      Serial.read();
    }
  }
}