#include <Arduino.h>
#include "configB1.h"

long motorSteps[NUM_MOTORS] = {0}; // One entry per motor, initialized to 0
bool dev_mod = true; // Set to true for development mode to print limit switch states

// Find motor index by name
int findMotorIndexByName(const String& name) {
  for (int i = 0; i < NUM_MOTORS; i++) {
    if (motors[i].name == name) return i;
  }
  return -1;
}

bool findZero(int motorIndex) {
    unsigned long start = millis();
    Serial.print("Finding zero for motor: ");
    Serial.println(motors[motorIndex].name);
    // Check if the limit switch is already triggered
    digitalWrite(EN, LOW); // Enable driver
    if (digitalRead(motors[motorIndex].limitSwitchPin) == motors[motorIndex].zeroPinState) {
        while (digitalRead(motors[motorIndex].limitSwitchPin) == motors[motorIndex].zeroPinState) {
          if (millis() - start > ZERO_TIMEOUT_MS) {
            digitalWrite(EN, HIGH);
            Serial.println("ERROR,TIMEOUT");
            return false;
          }
          digitalWrite(motors[motorIndex].dirPin, motors[motorIndex].zeroDirection ? LOW : HIGH);
          digitalWrite(motors[motorIndex].stepPin, HIGH);
          delayMicroseconds(motors[motorIndex].slow_stepSpeed);
          digitalWrite(motors[motorIndex].stepPin, LOW);
          delayMicroseconds(motors[motorIndex].slow_stepSpeed);
        }        
    }
    while (digitalRead(motors[motorIndex].limitSwitchPin) != motors[motorIndex].zeroPinState) {
      if (millis() - start > ZERO_TIMEOUT_MS) {
          digitalWrite(EN, HIGH);
          Serial.println("ERROR,TIMEOUT");
          return false;
      }
      digitalWrite(motors[motorIndex].dirPin, motors[motorIndex].zeroDirection ? HIGH : LOW);
      digitalWrite(motors[motorIndex].stepPin, HIGH);
      delayMicroseconds(motors[motorIndex].slow_stepSpeed);
      digitalWrite(motors[motorIndex].stepPin, LOW);
      delayMicroseconds(motors[motorIndex].slow_stepSpeed);
    }
    digitalWrite(EN, HIGH);  // disable driver
    motorSteps[motorIndex] = 0; // Reset the step count for this motor
    Serial.println("ZERO,DONE");
    return true;
}

void moveStepper(int motorIndex, long steps, bool direction, bool speed = SLOW) {
    // This function should implement the logic to move the stepper motor
    // For now, it just prints the action
    digitalWrite(EN, LOW); // Enable the stepper driver
    Serial.print("Moving motor ");
    Serial.print(motors[motorIndex].name);
    Serial.print(" ");
    Serial.print(steps);
    Serial.print(" steps ");
    Serial.println(direction ? "forward" : "backward");
    motorSteps[motorIndex] += (direction ? steps : -steps); // Update the step count

    digitalWrite(motors[motorIndex].dirPin, direction ^ motors[motorIndex].zeroDirection ? HIGH : LOW);
    for (int i = 0; i < steps; i++) {
        digitalWrite(motors[motorIndex].stepPin, HIGH);
        delayMicroseconds(speed == SLOW ? motors[motorIndex].slow_stepSpeed : motors[motorIndex].fast_stepSpeed);
        digitalWrite(motors[motorIndex].stepPin, LOW);
        delayMicroseconds(speed == SLOW ? motors[motorIndex].slow_stepSpeed : motors[motorIndex].fast_stepSpeed);
    }
    digitalWrite(EN, HIGH); // HIGH to Deactivate the stepper drivers
    Serial.print("Limit switch state for ");
    Serial.print(motors[motorIndex].name);
    Serial.print(": ");
    Serial.println(digitalRead(motors[motorIndex].limitSwitchPin));

    Serial.print("Current position of ");
    Serial.print(motors[motorIndex].name);
    Serial.print(": ");
    Serial.println(motorSteps[motorIndex]);
}

void setup() {
  Serial.begin(9600);

  pinMode(EN, OUTPUT); // Enable pin for all stepper outputs
  digitalWrite(EN, HIGH); // HIGH to Deactivate the stepper drivers
  for (int i = 0; i < NUM_MOTORS; i++) {
    pinMode(motors[i].dirPin, OUTPUT);
    pinMode(motors[i].stepPin, OUTPUT);
    pinMode(motors[i].limitSwitchPin, INPUT_PULLUP); // Set limit switch pins to INPUT_PULLUP
  }

  pinMode(WL_LIMIT_SWITCH2, INPUT_PULLUP); // Second wavelength limit switch (not used in this code)
  pinMode(SHUTTER, OUTPUT);
  Serial.println("Monochromator Control Initialized");
}

// Split a line into up to N comma-separated tokens
int splitTokens(const String &line, String tokens[], int maxTokens) {
  int start = 0, count = 0;
  int len = static_cast<int>(line.length());
  for (int i = 0; i <= len && count < maxTokens; ++i) {
    if (i == len || line[i] == ',') {
      tokens[count++] = line.substring(start, i);
      start = i + 1;
    }
  }
  return count;
}


void handleCommand(const String &raw) {
  String line = raw;
  line.trim();                    // strip \r\n and spaces
  if (line.length() == 0) return;
  bool highSpeed = false;

  const int MAX_TOKENS = 4;
  String tok[MAX_TOKENS];
  int n = splitTokens(line, tok, MAX_TOKENS);

  if (tok[0] == "INIT" && n == 1) {
    for (int i = 0; i < NUM_MOTORS; i++) {
      if (!findZero(i)) {
        Serial.println("INIT,FAILED");
        return;
      }
    }
    Serial.println("INIT,DONE");
    return;
  }

  if (tok[0] == "ZERO" && n == 2) {
    int idx = findMotorIndexByName(tok[1]);
    if (idx < 0) {
      Serial.println("ERROR,UNKNOWN_MOTOR");
      return;
    }
    findZero(idx);
    return;
  }

  if (tok[0] == "SPEED" && n == 2) {
    highSpeed = (tok[1] == "HIGH");
    Serial.print("ACTIVATED,");
    Serial.println(highSpeed ? "HIGH SPEED" : "LOW SPEED");
    return;
  }

  if (tok[0] == "MOVE" && n == 4) {
    int idx   = findMotorIndexByName(tok[1]);
    long steps = tok[2].toInt();
    bool dir  = tok[3].toInt();
    if (idx < 0) {
      Serial.println("ERROR,UNKNOWN_MOTOR");
      return;
    }
    moveStepper(idx, steps, dir, highSpeed);
    Serial.println("MOVE,DONE");
    return;
  }

  if (tok[0] == "SHUTTER" && n == 2) {
    if (tok[1] == "OPEN") {
      digitalWrite(SHUTTER, HIGH);
      Serial.println("SHUTTER,OPENED");
    } else if (tok[1] == "CLOSE") {
      digitalWrite(SHUTTER, LOW);
      Serial.println("SHUTTER,CLOSED");
    } else {
      Serial.println("ERROR,UNKNOWN_CMD");
    }
    return;
  }

  Serial.println("ERROR,UNKNOWN_CMD");
  Serial.print("Received on arduino: ");
  Serial.println(line);
}

void loop() {
  if (Serial.available() > 0) {
    String line = Serial.readStringUntil('\n');
    handleCommand(line);
  }
  delay(50);

  if (dev_mod){
    Serial.println("Development Mode: Printing Limit Switch States");
    Serial.print("WL1:");
    Serial.println(digitalRead(WL_LIMIT_SWITCH));
    Serial.print("WL2:");
    Serial.println(digitalRead(WL_LIMIT_SWITCH2));

    Serial.print("SLIT1:");
    Serial.println(digitalRead(SLIT1_LIMIT_SWITCH));
    Serial.print("SLIT2:");
    Serial.println(digitalRead(SLIT2_LIMIT_SWITCH));
    Serial.print("SLIT3:");
    Serial.println(digitalRead(SLIT3_LIMIT_SWITCH));

    Serial.println("Development Mode: Position of Motors");
    for (int i = 0; i < NUM_MOTORS; i++) {
      Serial.print(motors[i].name);
      Serial.print(": ");
      Serial.println(motorSteps[i]);
    }
    delay(5000);
  }
}