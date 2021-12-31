Testing some methods of the Connection object by testing the API builtin endpoints. 
Methods that are not in the Builtin API will not be tested.

Each folder contains tests for the endpoints of the corresponding version.

Note that in v0, the get() and wait_for_response() methods are tested by posting to the 
/send endpoint, then going to the /get and /get/wait endpoints, respectively,
and seeing if the data returned is the same. This may not work if the serial port
is really fast and the data gets received between the time that the data is sent
and the /get endpoint is reached. If you have a better test for this, please 
submit a PR.
