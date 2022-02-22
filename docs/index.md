# COM-Server Documentation

![PyPI](https://img.shields.io/pypi/v/com_server?label=Latest%20Version)

Welcome to the COM-Server documentation.

COM-Server is a Python library and a local web server that hosts an API locally and interacts with serial or COM ports. The Python library provides a different way of sending and receiving data from the serial port using a thread, and it also gives a set of tools that simplifies the task of manipulating data to and from the port. Additionally, the server makes it easier for other processes to communicate with the serial port.

The serial communication uses [pyserial](https://pyserial.readthedocs.io/en/latest/pyserial.html) as its back-end and the server uses [flask-restful](https://flask-restful.readthedocs.io/en/latest/quickstart.html) and [Flask](https://flask.palletsprojects.com/en/2.0.x/). Reading their documentations may help with developing with COM-Server.

**NOTE**: COM-Server is mainly tested on a Raspberry Pi connected to an Arduino UNO running Raspberry Pi OS Buster with Python 3.7.3. It has also been tested on:

OS | Version
---- | ----
Linux | Ubuntu 20.04 with Python 3.8.10
MacOS | Big Sur with Python 3.8.9
Windows | Windows 10 with Python 3.9.7, Windows 11 with Python 3.9.7

It is likely that this library will not work for non-USB ports. 

## Contents

- [Home](/)
    - [Recommended Use](/#recommended-use)
    - [Links](/#links)
    - [Installation](/#installation)
    - [Quickstart](/#quickstart)
    - [License](/#license)
- [Getting Started](guide/getting-started)
    - [Creating a Connection Class](guide/getting-started/#creating-a-connection-class)
    - [Creating a ConnectionRoutes Class](guide/getting-started/#creating-a-connectionroutes-class)
    - [Using the builtin endpoints](guide/getting-started/#using-the-builtin-endpoints)
    - [Using the CLI](guide/getting-started/#using-the-cli)
- [Library API](guide/library-api)
    - [Functions](guide/library-api/#functions)
        - [com_server.all_ports()](guide/library-api/#com_serverall_ports)
        - [com_server.start_app()](guide/library-api/#com_serverstart_app)
        - [com_server.add_resources()](guide/library-api/#com_serveradd_resources)
        - [com_server.start_conns()](guide/library-api/#com_serverstart_conns)
    - [Classes](guide/library-api/#classes)
        - [com_server.Connection](guide/library-api/#com_serverconnection)
        - [com_server.ConnectionRoutes](guide/library-api/#com_serverconnectionroutes)
        - [com_server.RestApiHandler](guide/library-api/#com_serverrestapihandler)
        - [com_server.ConnectionResource](guide/library-api/#com_serverconnectionresource)
        - [com_server.SendQueue](guide/library-api/#com_serversendqueue)
        - [com_server.ReceiveQueue](guide/library-api/#com_serverreceivequeue)
    - [Constants](guide/library-api/#constants)
    - [Exceptions](guide/library-api/#exceptions)
        - [com_server.ConnectException](guide/library-api/#com_serverconnectexception)
        - [com_server.EndpointExistsException](guide/library-api/#com_serverendpointexistsexception)
        - [com_server.DuplicatePortException](guide/library-api/#com_serverduplicateportexception)
- [Server API](server)
    - [Version 0](server/v0)
    - [Version 1](server/v1)

## Recommended use
COM-Server is **not** meant to be used like a normal JSON API, even though it uses Flask and Flask-restful. If there are many different devices accessing the endpoints at the same time, data will be backed up, since the serial communication is relatively slow and things cannot be sent to the serial device at the same time. 

The server is recommended to be used like a socket, and it should be used as a way for another process (should be only one; COM-Server has no implemented synchronization) on one computer (could be the same computer or another one on the same network) to communicate with the serial port via `pyserial` and this Python program. 
 
## Links
- Documentation: [https://com-server.readthedocs.io/en/latest/](https://com-server.readthedocs.io/en/latest/)
- Source code: [https://github.com/jonyboi396825/COM-Server](https://github.com/jonyboi396825/COM-Server)
- Issue tracker: [https://github.com/jonyboi396825/COM-Server/issues](https://github.com/jonyboi396825/COM-Server/issues)
- Contributing: [https://github.com/jonyboi396825/COM-Server/blob/master/CONTRIBUTING.md](https://github.com/jonyboi396825/COM-Server/blob/master/CONTRIBUTING.md)
- Changelog: [https://github.com/jonyboi396825/COM-Server/blob/master/CHANGELOG.md](https://github.com/jonyboi396825/COM-Server/blob/master/CHANGELOG.md)

## Installation

**NOTE**: COM_Server only works on Python >= 3.6.

Using [pip](https://pip.pypa.io/en/stable/getting-started/):
```sh
> pip install -U com-server
```

For beta releases, use the `--pre` option:
```sh
> pip install --pre com-server
```

Alternatively, you can install from source by running:
```sh
> python setup.py install
```

You can use `python3` depending on what command you are using for python 3.

## Quickstart

The examples below will start an API server that interacts with the port at http://0.0.0.0:8080

```py
# launches a server on http://0.0.0.0:8080

from com_server import Connection, ConnectionRoutes, start_app
from com_server.api import V1
from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

conn = Connection(<baud>, "<serport>") 
handler = ConnectionRoutes(conn)
V1(handler)

start_app(app, api, handler)
```
Replace "&lt;serport&gt;" and "&lt;baud&gt;" with the serial port and baud rate.

Alternatively, you can use the command line:
```sh
> com_server run <baud> <serport>
```
Again, replace "&lt;serport&gt;" and "&lt;baud&gt;" with the serial port and baud rate.

## License
This library is open source and licensed under the [MIT License](https://github.com/jonyboi396825/COM-Server/blob/master/LICENSE).