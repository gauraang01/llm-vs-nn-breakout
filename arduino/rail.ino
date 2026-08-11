// Define the control pins
const int dirPin = 2;
const int stepPin = 3;

// Delay in microseconds per half-step. Lower = faster top speed.
const int motorDelay = 400; 

long currentStep = 0;
long targetStep = 0;

void setup() {
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  Serial.begin(115200); 
  Serial.setTimeout(5); 
}

void loop() {
  // Process ALL incoming commands in the buffer before stepping
  while (Serial.available() > 0) {
    char firstChar = Serial.peek();
    if (firstChar == 'P') {
      Serial.read(); // consume 'P'
      targetStep = Serial.parseInt();
      Serial.read(); // consume '\n'
    } else if (firstChar == 'Z') {
      Serial.readStringUntil('\n'); // consume the rest
      currentStep = 0;
      targetStep = 0;
    } else {
      Serial.read(); // consume unknown char
    }
  }

  // Move as fast as possible toward targetStep
  if (currentStep < targetStep) {
    digitalWrite(dirPin, HIGH);
    stepOnce();
    currentStep++;
  } else if (currentStep > targetStep) {
    digitalWrite(dirPin, LOW);
    stepOnce();
    currentStep--;
  }
}

void stepOnce() {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(motorDelay);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(motorDelay);
}
