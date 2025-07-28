#include <Arduino.h>

#define EN 8 /* Enable pin for all stepper outputs */

#define WL_DIR 5 /* Direction pin for Wavelength */
#define WL_STEP 2 /* Step pin for Wavelength */
#define WL_LIMIT_SWITCH A0 /* Limit switch pin for Wavelength RESET ABORT*/
#define WL_LIMIT_SWITCH2 A1 /* Limit switch pin for Wavelength FEED HOLD*/

#define SLIT1_DIR 13 /* Light occluder pin */
#define SLIT1_STEP 12 /* Step pin for Light occluder */
#define SLIT1_LIMIT_SWITCH 11 /* Limit switch pin for Light occluder END STOPS Z*/

#define SLIT2_DIR 7 /* Light occluder pin */
#define SLIT2_STEP 4 /* Step pin for Light occluder */
#define SLIT2_LIMIT_SWITCH 10 /* Limit switch pin for Light occluder END STOPS Y */

#define SLIT3_DIR 6 /* Light occluder pin */
#define SLIT3_STEP 3 /* Step pin for Light occluder */
#define SLIT3_LIMIT_SWITCH A2 /* Limit switch pin for Light occluder RESUME */

#define SHUTTER 9 /* Shutter pin END STOPS X */

#define SLOW true // Flag to indicate if the stepper should move slowly
#define FAST false // Flag to indicate if the stepper should move fast
#define ZERO_TIMEOUT_MS 70000 // Timeout for zeroing the motor in milliseconds

struct StepperMotor {
    int dirPin;
    int stepPin;
    int limitSwitchPin;
    String name; // Name of the motor for debugging purposes
    int slow_stepSpeed = 200; // Default slow step speed in microseconds
    int fast_stepSpeed = 50; // Default step speed in microseconds
    bool zeroDirection = LOW; // Default zero direction
    bool zeroPinState = LOW; // Default state of the limit switch when zeroed

    // 1. Only pins and name
    StepperMotor(int dir, int step, int limit, String motorName)
        : dirPin(dir), stepPin(step), limitSwitchPin(limit), name(motorName) {}
    
    // 2. Everything
    StepperMotor(int dir, int step, int limit, String motorName, int slowSpeed, int fastSpeed, bool zeroDirection, bool zeroPinState)
        : dirPin(dir), stepPin(step), limitSwitchPin(limit), name(motorName), slow_stepSpeed(slowSpeed), fast_stepSpeed(fastSpeed), zeroDirection(zeroDirection), zeroPinState(zeroPinState) {}

    StepperMotor() = default;
};

// Create an array of motors
StepperMotor motors[] = {
    {WL_DIR, WL_STEP, WL_LIMIT_SWITCH, "WL", 50, 25, LOW, HIGH}
};

const int NUM_MOTORS = sizeof(motors) / sizeof(motors[0]);