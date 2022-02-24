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
    * Off the `master` branch if bug fix/docs fix
    ```sh
    > git fetch
    > git checkout -b branch-name origin/master
    ```
    * Off the `develop` branch if adding feature
    ```sh
    > git fetch
    > git checkout -b branch-name origin/develop
    ```
2. Make changes and commit for each change
3. Add tests that apply to your change
4. Push your commits and create a pull request to merge into the `develop` branch of the base repository.
```sh
> git push -u fork branch-name
```
I will change the merge branch if needed.

**NOTE:** In the pull request, please specify the operating system and serial device (e.g. Arduino UNO, Arduino Mega, etc.) you tested COM-Server on.

**NOTE** (only applies to bug/docs fix from master branch): To change the version, type in the below command, which should show the COM-Server version as `X.Y.N`. In `__init__`.py of the module and `setup.cfg`, change the `N`-value of the version to `N+1`. For example, if the version output is `0.0.2`, then change it to `0.0.3`. If it is `X.Y`, then change it to `X.Y.1`.

```sh
> com_server --version
```


### Testing:

Launch the server:
```sh
> com_server run <baud> <serport>
```

Replace "&lt;baud&gt;" and "&lt;serport&gt;" with the baud and serial port of your serial device.

Use the testing scripts:
```sh
> python3 tests/passive_test.py -vv
> python3 tests/active_test.py -vv
```

Make sure that all tests pass.

Some tests need the `com_server` command to be run or the Arduino to be plugged in. Make sure to run both commands above and also ensure that the Arduino is plugged in.

When writing tests, use the `pytest` library, and make them as specific as possible, testing a specific part of what you are making. Tests that do not require a serial port or a server should go into the `tests/passive` directory, and tests that do require an Arduino should go into the `tests/active` directory.

I am also open to those who write new tests to already existing code.

## Typing:

If writing code in the `src/com_server` directory, please use `mypy` to check static typing by running:

```sh
> mypy -p com_server
```

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
