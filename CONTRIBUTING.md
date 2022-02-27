# Contributing

Note that I will probably not have time to get to many issues or pull requests. I will try to fix bugs as quickly as I can and answer questions, but the other ones are not as prioritized.

## Submitting an Issue

Before you submit an issue, make sure that your issue was not already submitted by someone else and is still open.

Otherwise, follow the issue template.

## Submitting a Pull Request

Make sure you have an Arduino and the [Arduino IDE](https://www.arduino.cc/en/software) installed before contributing.

### First time setup:

1. [Download and install Git](https://git-scm.com/downloads)
2. Configure git with username and email
```sh
> git config --global user.name 'your name'
> git config --global user.email 'your email'
```
3. Fork the repository
4. Clone the repository fork
```sh
> git clone https://github.com/{name}/COM-Server.git
> cd COM-Server
```
5. Add the fork as a remote named `fork`
```sh
> git remote add fork https://github.com/{name}/COM-Server 
```
6. Create a virtualenv named `.env`
```sh
> python -m venv .env
```
7. Install development dependencies and install the package in development mode
```sh
> pip install -r requirements.txt && pip install -e .
```
8. Upload the script named `send_back` provided in the `examples` directory onto the Arduino.

### Developing:

1. Create a new branch  
    * Off the `0.1.x` branch if bug fix/docs fix
    ```sh
    > git fetch
    > git checkout -b branch-name origin/0.1.x
    ```
    * Off the `develop` branch if adding feature
    ```sh
    > git fetch
    > git checkout -b branch-name origin/develop
    ```
2. Make changes and commit for each change
3. Add tests that apply to your change
4. Push your commits.
```sh
> git push -u fork branch-name
```
5. Open a PR into `develop` if adding a feature or into `0.1.x` if addressing a bug fix or a documentation fix.

**NOTE:** In the pull request, please specify the operating system and serial device (e.g. Arduino UNO, Arduino Mega, etc.) you tested COM-Server on.

```sh
> com_server --version
```


### Testing:

Launch the server:
```sh
> com_server run <baud> <serport>
```

Replace "&lt;baud&gt;" and "&lt;serport&gt;" with the baud and serial port of your serial device.

Use pytest:
```sh
> pytest -vv 
```

Make sure that all tests pass.

Some tests need the `com_server` command to be run or the Arduino to be plugged in. Make sure the listed command is run and and Arduino is plugged in to make sure that every test passes and none of them are skipped.

When writing tests, use the `pytest` library, and make them as specific as possible, testing a specific part of what you are making.

I am also open to those who write new tests to already existing code, especially ones that can test if the methods of the `BaseConnection` and `Connection` classes are behaving properly.

### Formatting:

Please format your code using [Black](https://black.readthedocs.io/en/stable/index.html).

### Building documentation

COM-Server uses `mkdocs` for its documentation. To build the documentation:

```sh
> mkdocs build
```

To serve the documentation on `localhost:8000`
```sh
> mkdocs serve
```

Make sure to update the documentation to reflect your changes if there were any in the library.
