const int ledPins[] = {2, 3, 4, 5};
const int numOfLEDS = 4;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numOfLEDS; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
}

int counter = 0;
void loop() {
  if (Serial.available() >= numOfLEDS) {
    for (int i = 0; i < numOfLEDS; i++) {
      bool b = Serial.read();
      digitalWrite(ledPins[i], b ? HIGH : LOW);
    }
  }
}
