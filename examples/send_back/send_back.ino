/*
send_back.ino

This Arduino sketch reads data (until newline) 
from the Serial port if there is any available
and sends `Got "[data]"\n` back. The baud rate for
communication is 115200.

Copyright 2021 (c) Jonathan Liu
Code is licensed under MIT license. 
*/

void setup(){
    Serial.begin(115200);
}

void loop(){
    if (Serial.available()){
        String s = Serial.readStringUntil('\n');

        Serial.print("Got: \"" + s + "\"\n");
    }
}