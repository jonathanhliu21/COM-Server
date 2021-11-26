# COM-Server Built-in API

## Endpoints from RestApiHandler

These endpoints cannot be used in any case with the `RestApiHandler`, even if `has_register_recall` is False. If they are defined again by the user, it will raise `com_server.EndpointExistsException`.

These endpoints will not apply if `has_register_recall` is False, and the response will be a `404 Not Found`.

```txt
/register
```

Registers an IP to the server. Note that this is IP-based, not
process based, so if there are multiple process on the same computer
connecting to this, the server will not be able to detect it and may
lead to unexpected behavior.

Method: GET

Arguments:
    None

Responses:

- `200 OK`: `{"message": "OK"}` if successful
- `400 Bad Request`: 
    - `{"message": "Double registration"}` if this endpoint is reached by an IP while it is registered
    - `{"message": "Not registered; only one connection at a time"}` if this endpoint is reached while another IP is registered

```txt
/recall
```

Unregisters an IP from a server and allows other IPs to use it.

Method: GET

Arguments:
    None

Responses:

- `200 OK`: `{"message": "OK}` if successful
- `400 Bad Request`:
    - `{"message": "Nothing has been registered"}` if try to call without any IP registered
    - `{"message": "Not same user as one in session"}` if called with different IP as the one registered

## Endpoints from Builtins

If the `Builtins` class is used on a `RestApiHandler` object, then both the endpoints above and the endpoints below cannot be used. If they are defined again by the user, the program will raise a `EndpointExistsException`.

```txt
/send
```

Endpoint to send data to the serial port.
Calls `Connection.send()` with given arguments in request.

Method: POST

Arguments:

- "data" (str, list): The data to send; can be provided in multiple arguments, which will be concatenated with the `concatenate` variable.
- "ending" (str) (optional): A character or string that will be appended to `data` after being concatenated before sending to the serial port.
By default a carraige return + newline.
- "concatenate" (str) (optional): The character or string that elements of "data" should be concatenated by if its size is greater than 1;
won't affect "data" if the size of the list is equal to 1. By default a space.

Responses:

- `200 OK`: 
    - `{"message": "OK"}` if send through
- `502 Bad Gateway`: 
    - `{"message": "Failed to send"}` if something went wrong with sending (i.e. `Connection.send()` returned false)

```txt
/receive
```

Endpoint to get data that was recently received.
If POST, calls `Connection.receive_str(...)` with arguments given in request.
If GET, calls `Connection.receive_str(...)` with default arguments (except strip=True). This means
that it responds with the latest received string with everything included after 
being stripped of whitespaces and newlines.

Method: GET, POST

Arguments (POST only):

- "num_before" (int) (optional): How recent the receive object should be.
If 0, then returns most recent received object. If 1, then returns
the second most recent received object, etc. By default 0.
- "read_until" (str, null) (optional): Will return a string that terminates with
character in "read_until", excluding that character or string. For example,
if the bytes was `b'123456'` and "read_until" was 6, then it will return
`'12345'`. If ommitted, then returns the entire string. By default returns entire string.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK", "timestamp": ..., "data": "..."}` where "timestamp"
    is the Unix epoch time that the message was received and "data" is the
    data that was processed. If nothing was received, then "data" and "timestamp"
    would be None/null.

```txt
/receive_all
```

Returns the entire receive queue. Calls `Connection.get_all_rcv_str(...)`.
If POST then uses arguments in request.
If GET then uses default arguments (except strip=True), which means that
that it responds with the latest received string with everything included after 
being stripped of whitespaces and newlines.

Method: GET, POST

Arguments (POST only):

- "read_until" (str, null) (optional): Will return a string that terminates with
character in "read_until", excluding that character or string. For example,
if the bytes was `b'123456'` and "read_until" was 6, then it will return
`'12345'`. If ommitted, then returns the entire string. By default returns entire string.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK", "timestamps": [...], "data": [...]}`: where "timestamps" 
    contains the list of timestamps in the receive queue and "data" contains the 
    list of data in the receive queue. The indices for "timestamps" and "data" match.

```txt
/get
```

Waits for the first string from the serial port after request.
If no string after timeout (specified on server side), then responds with 502.
Calls `Connection.get(str, ...)`.
If POST then uses arguments in request. 
If GET then uses default arguments (except strip=True), which means that
that it responds with the latest received string with everything included after 
being stripped of whitespaces and newlines.

Method: GET, POST

Arguments (POST only):

- "read_until" (str, null) (optional): Will return a string that terminates with
character in "read_until", excluding that character or string. For example,
if the bytes was `b'123456'` and "read_until" was 6, then it will return
`'12345'`. If ommitted, then returns the entire string. By default returns entire string.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK", "data": "..."}` where "data" is received data
- `502 Bad Gateway`: 
    - `{"message": "Nothing received"}` if nothing was received from the serial port
    within the timeout specified on the server side.   

```txt
/send/get_first
```

Respond with the first string received from the 
serial port after sending something given in request.
Calls `Connection.get_first_response(is_bytes=False, ...)`.

Method: POST

Arguments:

- "data" (str, list): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
- "ending" (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
- "concatenate" (str) (optional): What the strings in args should be concatenated by
- "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK", "data": "..."}` where "data" is the
    data that was processed. 
- `502 Bad Gateway`: 
    - `{"message": "Nothing received"}` if nothing was received from the serial port
    within the timeout specified on the server side.   

```txt
/get/wait
```

Waits until connection receives string data given in request.
Calls `Connection.wait_for_response(...)`.

Method: POST

Arguments:

- "response" (str): The string the program is waiting to receive.
Compares to response to `Connection.receive_str()`.
- "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK"}` if everything was able to send through
- `502 Bad Gateway`: 
    - `{"message": "Nothing received"}` if nothing was received from the serial port
    within the timeout specified on the server side.   

```txt
/send/get
```

Continues sending something until connection receives data given in request.
Calls `Connection.send_for_response(...)`

Method: POST

Arguments:

- "response" (str): The string the program is waiting to receive.
Compares to response to `Connection.receive_str()`.
- "data" (str, list): Everything that is to be sent, each as a separate parameter. Must have at least one parameter.
- "ending" (str) (optional): The ending of the bytes object to be sent through the Serial port. By default a carraige return ("\\r\\n")
- "concatenate" (str) (optional): What the strings in args should be concatenated by
- "read_until" (str, None) (optional): Will return a string that terminates with `read_until`, excluding `read_until`. 
For example, if the string was `"abcdefg123456\\n"`, and `read_until` was `\\n`, then it will return `"abcdefg123456"`.
If `read_until` is None, the it will return the entire string. By default None.
- "strip" (bool) (optional): If true, then strips received and processed string of
whitespaces and newlines and responds with result. Otherwise, returns raw string. 
Note that using {"strip": False} may not work; it is better to omit it.
By default False.

Response:

- `200 OK`:
    - `{"message": "OK"}` if everything was able to send through
- `502 Bad Gateway`: 
    - `{"message": "Nothing received"}` if nothing was received from the serial port
    within the timeout specified on the server side.   

```txt
/connected
```

Indicates if the serial port is currently connected or not.
Returns the `Connection.connected` property. 

Method: GET

Arguments:
    None

Response:

- `200 OK`:
    - `{"message": "OK", "connected": ...}`: where connected is the connected state: `true` if connected, `false` if not.

```txt
/list_ports
```

Lists all available Serial ports. Calls `com_server.tools.all_ports()`
and returns list of lists of size 3: [`port`, `description`, `technical description`]

Method: GET

Arguments:
    None

Response:

- `200 OK`:
    - `{"message": "OK", ports = [["...", "...", "..."], "..."]}` where "ports"
    is a list of lists of size 3, each one indicating the port, description, and
    technical description

## Escape characters

When including escape characters (newlines, carriage returns, etc.) in a post request to one of the endpoints, the request might not interpret the character. For example, in some cases, if you send `ending="\n"` to the `/send` endpoint (other endpoints have this issue too; we're just using `/send` as an example), the server may interpret it as `\\n` (a backslash followed by `n`), rather than an actual newline. Below contains a list of ways to solve this for different programs:

### Python requests library

The Python requests library works by default if you put a normal newline character `\n` (or any other escape character) in the string. 

### cURL

If you are using `zsh` or `bash`, then you can use the `$''` syntax to include escape characters. For example, sending data to `/send` with cURL can look like:

```bash
$ curl -X POST -d "data=hello" -d $'ending=\n' <url>
```

### JSON

Escape characters should work normally with JSON. 

### Adding more programs

If you want to add more programs to this list, feel free to submit a [pull request](https://github.com/jonyboi396825/COM-Server/pulls). If something does not work or you see something wrong, please submit an [issue](https://github.com/jonyboi396825/COM-Server/issues) under the category "Documentation."
