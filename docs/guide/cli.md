# COM-Server Command Line Interface

Run `com_server -h` to get this message:

```txt
> com_server -h
COM_Server command line tool

A simple command line tool to start the API server that interacts
with the serial port in an development environment or a 
production environment.

Usage:
    com_server (-p | --serport) <serport> (-b | --baud) <baud> run [--env=<env>] [--host=<host>] [--port=<port>] [--s-int=<s-int>] [--to=<to>] [--cors]
    com_server -h | --help
    com_server --version

Options:
    -p, --serport   The serial port to connect to. For MacOS, use the "cu.*" port rather than the "tty.*" port.
    -b, --baud      The baud rate of the serial connection.
    --env=<env>     Development or production environment. Value must be 'dev' or 'prod'. [default: dev].
    --host=<host>   The name of the host server (optional) [default: 0.0.0.0].
    --port=<port>   The port of the host server (optional) [default: 8080].
    --s-int=<s-int>  
                    How long, in seconds, the program should wait between sending to serial port [default: 1].
    --to=<to>       How long, in seconds, the program should wait before exiting when performing time-consuming tasks [default: 1].
    --cors          If set, then the program will add cross origin resource sharing.

    -h, --help      Show help.
    --version       Show version.
>
```