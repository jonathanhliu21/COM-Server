/*
blink.ino

This sketch reads data from the serial port, then changes the
state of the built-in LED whenever a command comes in from the 
serial port. The baud rate for this is 115200.

When it reads "s", then it leaves it on solid.
When it reads "b", then it blinks the LED.
When it reads "o", then it turns the LED off. 

It shows how you can write data to the Arduino using
com_server.

Copyright 2021 (c) Jonathan Liu
Code is licensed under MIT license. 
*/

int curstate = 0; // 0 = off, 1 = blink, 2 = solid on

void setup(){
    Serial.begin(115200);

    pinMode(LED_BUILTIN, OUTPUT);
}

void loop(){
    if (Serial.available()){
        String s = Serial.readStringUntil('\n');

        if (s == "s")
            curstate = 2;
        else if (s == "b")
            curstate = 1;
        else
            curstate = 0;
    }

    if (curstate == 0) {
        digitalWrite(LED_BUILTIN, LOW);
    } else if (curstate == 2) {
        digitalWrite(LED_BUILTIN, HIGH);
    } else {
        // blink every second so cycle = 2 seconds        
        digitalWrite(LED_BUILTIN, ((millis() / 1000) % 2 == 0));
    }
}
