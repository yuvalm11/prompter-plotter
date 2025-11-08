#include "osap/src/osap.h"
#include <Servo.h>

#define PIN_SERVO D10
#define PIN_LIMIT_SWITCH D0
#define PIN_LED_WD PIN_LED_G

Servo myServo;

// State machine for pen control
enum PenState {
  PEN_IDLE,
  PEN_RAISING,
  PEN_LOWERING
};

PenState pen_state = PEN_IDLE;
uint32_t pen_down_start_time = 0;
const uint32_t PEN_DOWN_DURATION_MS = 700;

void pen_up(void){
  // Start raising pen - loop() will handle the state machine
  pen_state = PEN_RAISING;
  myServo.write(80);
}

void pen_down(void){
  // Start lowering pen - loop() will handle the state machine
  pen_state = PEN_LOWERING;
  pen_down_start_time = millis();
  myServo.write(95);
}

OSAP_Runtime osap("ServoPatch", "servo_patch");
OSAP_Gateway_USBCDC_COBS<decltype(Serial)> serLink(&Serial, "usb");

BUILD_RPC(pen_up, "", "");
BUILD_RPC(pen_down, "", "");

void setup() {
  osap.begin();
  
  // Setup servo on pin D10
  myServo.attach(PIN_SERVO);
  myServo.write(90); // Start at stop position
  
  // Setup limit switch with internal pullup
  pinMode(PIN_LIMIT_SWITCH, INPUT_PULLUP);
  
  // Setup watchdog LED
  pinMode(PIN_LED_WD, OUTPUT);
}

uint32_t wdBlinkInterval = 50;
uint32_t wdBlinkLast = 0;

void loop() {
  osap.loop();
  
  // Handle pen state machine
  switch(pen_state){
    case PEN_RAISING:
      // Keep servo running at 80 while raising
      myServo.write(80);
      // Check if limit switch is triggered (goes LOW when triggered)
      if(!digitalRead(PIN_LIMIT_SWITCH)){
        // Limit switch triggered - stop the servo
        myServo.write(90);
        pen_state = PEN_IDLE;
      }
      break;
      
    case PEN_LOWERING:
      // Keep servo running at 95 while lowering
      myServo.write(95);
      // Check if we've waited long enough
      if(millis() - pen_down_start_time >= PEN_DOWN_DURATION_MS){
        // Time elapsed - stop the servo
        myServo.write(90);
        pen_state = PEN_IDLE;
      }
      break;
      
    case PEN_IDLE:
      // Do nothing
      break;
  }
  
  // Blink watchdog LED
  if(wdBlinkLast + wdBlinkInterval < millis()){
    wdBlinkLast = millis();
    digitalWrite(PIN_LED_WD, !digitalRead(PIN_LED_WD));
  }
}

