# Ellis Protocol Documentation  
    This document provides a reference for the implementation of the version
of the Ellis Protocol Implemented within Version 1.0.0 of Ellis. The standard
port used by Ellis is TCP port 4526.

## Connection  
  There is currently no authentication scheme provided by Ellis or the protocol
to ensure only verified clients connect to it. Upon reciving a connection.
a client may send/recieve commands, and the server may do the same.


## Commands  
  Commands are UTF-8 Encoded Strings sent by either the client or the
server to request data or a certain action be taken. A command may have
zero or one arguments, however a command sender may only send one request
at a time, and must wait for a response before sending a new request --
unless the command does NOT return a response. If the response is a command
that is allowed as a respose, then the recipient MUST perform that command 
as defined for that recipient (if any exists). A Server MAY disconnect a
Client that it detects as violating this restriction by immediately sending
the END Command and disconnecting. Commands are case-insensitive.

### List of Commands
#### END: Server -> Client/Client -> Server
  The END command has no arguments, and may be sent by either the
server or the client. Upon the reciving the command, the recipeint
is to assume not response will occur and MUST close the connection
without sending a response. This command MAY be sent at any time,
including in resposne to a command. The sender MUST NOT send any responses
to any commands recieved after sending the command, and it MUST close
the connection immediately afterwards.

#### GET: Client -> Server
  The GET command has no arguments, and may only be sent by a client
to the server get a nation for recruitment. The response is a UTF-8
encoded JSON String representing a nation with the information that
the NS nation shard has. It MAY include additional information,
but any additional information is NOT guaranteed.
  
#### RETURN nation: Client -> Server
  The RETURN command has one argument, which is a UTF-8 Encoded JSON
String that is a nation sent to the client with GET. This command is
only sent to the server by a client. Upon reciving this command,
the server MUST check to ensure the nation is still recruitable before
allowing another client to check it out, HOWEVER the Ellis client does
NOT have to return it immediately, and may delay the return. It may also
chose to NOT make it available. IF the nation is unrecruitable upon its
return the server CAN NOT return it to the pool, and instead must discard
the nation.

#### CHECK nation: Client -> Server
  The CHECK command has one argument, which is a UTF-8 Encoded String that
is the name of a nation that was sent to the client. Upon reciving it, the
server MUST make a request to NationStates to ensure that the nation is
recruitable. The response is a UTF-8 Encoded JSON String that contains one
field: recruitable. The field will be 1 IF AND ONLY IF the nation is recruitable,
otherwise the resposne will be 0.
