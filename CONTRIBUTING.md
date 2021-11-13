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

1. Create a new branch off the `master` branch
```sh
> git fetch
> git checkout -b branch-name origin/master
```
2. Make changes and commit for each change
3. Add tests that apply to your change
4. Push your commits and create a pull request to merge into the `develop` branch of the base repository.
```sh
> git push -u fork branch-name
```

I will change the merge branch if needed.

### Testing:

Use pytest:
```sh
> pytest -vv
```

Make sure that all tests pass.

Some tests need the `com_server` command to be run or the Arduino to be plugged in. Make sure the listed command is run and and Arduino is plugged in to make sure that every test passes and none of them are skipped.

When writing tests, use the `pytest` library, and make them as specific as possible, testing a specific part of what you are making.

I am also open to those who write new tests to already existing code, especially ones that can test if the methods of the `BaseConnection` and `Connection` classes are behaving properly.

### Building documentation

COM-Server uses `mkdocs` for its documentation. To build the documentation:

```sh
> mkdocs build
```

To serve the documentation on `localhost:8000`
```sh
> mkdocs serve
```

