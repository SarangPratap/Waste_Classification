#include <Arduino.h>

// put function declarations here:
int myFunction(int, int);

// Define LED_BUILTIN for ESP32-CAM if not already defined
#ifndef LED_BUILTIN
#define LED_BUILTIN 4
#endif

void setup() {
  // put your setup code here, to run once:
  
  // blink the built-in LED based on the result
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:

  // LED blink disabled
  // digitalWrite(LED_BUILTIN, HIGH);   // turn the LED on (HIGH is the voltage level)
  // delay(1000);                       // wait for a second
  // digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
  // delay(1000);                       // wait for a second
}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}