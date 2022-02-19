Examples here are outdated. Refer to the documentation instead.


OLD:

Examples of COM-Server:

NOTE: You need an Arduino, and you have to upload the Arduino sketches provided under each directory before running the scripts in that directory.

blink - An simple example of sending data to the serial port. It allows you to manipulate the LED on the Arduino from the command line.
Upload the blink.ino sketch, then run the python script.

send_back - The sketch tells the Arduino to read the data from the serial port until a newline character, then it will send that data back through the serial port.
Upload the send_back.ino sketch, then run each python script. Press ^C (Control-C) to exit the program. Read the files to see what output is expected.
