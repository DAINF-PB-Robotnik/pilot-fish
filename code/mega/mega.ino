#include <Arduino.h>

// === Number of sensors ===
const uint8_t NUM_SENSORS = 8;

// === Pin assignments (inverted order) ===
// Sensor 0 → pins 24/25, Sensor 1 → 28/29, …, Sensor 7 → 51/52
const uint8_t TRIG_PINS[NUM_SENSORS] = {24, 28, 32, 36, 40, 44, 48, 52};
const uint8_t ECHO_PINS[NUM_SENSORS] = {25, 29, 33, 37, 41, 45, 49, 53};

// Timeout for pulseIn (µs) — covers ≈2 m range
const unsigned long TIMEOUT_US = 12000UL;

// Buffer de distâncias em milímetros (-1 = erro)
int16_t distances_mm[NUM_SENSORS];

void setup() {
  Serial.begin(115200);
  // Configura TRIG como OUTPUT e ECHO como INPUT
  for (uint8_t i = 0; i < NUM_SENSORS; i++) {
    pinMode(TRIG_PINS[i], OUTPUT);
    digitalWrite(TRIG_PINS[i], LOW);
    pinMode(ECHO_PINS[i], INPUT);
  }
}

int16_t measureSensor(uint8_t idx) {
  // 1) envia pulso de 10 µs no TRIG
  digitalWrite(TRIG_PINS[idx], LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PINS[idx], HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PINS[idx], LOW);

  // 2) lê largura do pulso no ECHO ou timeout
  unsigned long dur = pulseIn(ECHO_PINS[idx], HIGH, TIMEOUT_US);
  if (dur == 0) return -1;  // sem eco ou timeout

  // converte µs → mm: (dur/2) * 0.343 mm/µs → sem float
  return (dur * 343UL) / 2000;
}

void loop() {
  // Mede todos os sensores em sequência
  for (uint8_t i = 0; i < NUM_SENSORS; i++) {
    distances_mm[i] = measureSensor(i);
    // optional small recovery: delay(5);
  }

  // Se receber 'R' pela serial USB, envia string
  if (Serial.available()) {
    if (Serial.read() == 'R') {
      for (uint8_t i = 0; i < NUM_SENSORS; i++) {
        if (i) Serial.print(';');
        int16_t mm = distances_mm[i];
        if (mm < 0) {
          Serial.print("Err");
        } else {
          Serial.print(mm / 10);         // parte inteira em cm
          Serial.print('.');
          Serial.print(abs(mm % 10));    // décimo de cm
        }
      }
      Serial.println();
    }
    // limpa buffer
    while (Serial.available()) Serial.read();
  }
}
