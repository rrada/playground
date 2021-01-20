# Control Server

Very simple implementation of server and remote communication where
 * `server` is manager for many remotes
 * `remote`s are sending `ping` packets in defined interval and telling the server about own state 

Server
 * is keeping track about all remotes that are sending ping
 * periodically clean all remotes declared as 'stale'

Remote states:
 * IDLE
 * WORKING
 * ERROR
 
If remote is in IDLE state, server will send work offer to remote

> This implementation is not meant to be fully complete and working as final product.
Server is not sending any meaningful work requests.
Remotes are only sending ping and the IDLE/WORKING state is randomized, so its not doing any real work at background.  



```
# ~/playground/controlserver                                    │    # ~/playground/controlserver
> python3 server.py                                             │    > python3 remote.py
Adding remote: 173683416947055                                  │    GYUIRJQWOFIDGNWW
Remote state WORKING || desc: gyuirjqwofidgnww                  │    RWTECNIVOFCOPWYL
Updating remote: 173683416947055                                │    HNRVZVNFV
Remote state WORKING || desc: rwtecnivofcopwyl                  │    FCAIRQUJTYQJODSXDWBJ
Updating remote: 173683416947055                                │    Job offer from server
Remote state WORKING || desc: hnrvzvnfv                         │    Job offer from server
Updating remote: 173683416947055                                │    Job offer from server
Remote state IDLE || desc: fcairqujtyqjodsxdwbj                 │    QOVFOPXSZGBMTDIEZC
Updating remote: 173683416947055                                │    Job offer from server
Remote state IDLE || desc: qovfopxszgbmtdiezc                   │    Job offer from server
Updating remote: 173683416947055                                │    Job offer from server
Remote state WORKING || desc: szeaerwffgkicyonxarx              │    SZEAERWFFGKICYONXARX
Updating remote: 173683416947055                                │    XVBDYKLJWSLC
Remote state IDLE || desc: xvbdykljwslc                         │    Job offer from server
Updating remote: 173683416947055                                │    Job offer from server
Remote state WORKING || desc: tskknwlcuhqhbvoesory              │    Job offer from server
                                                                │    TSKKNWLCUHQHBVOESORY
                                                                │    ^C
                                                                │
Removing stale remote: 173683416947055                          │
^C                                                              │
```

TODO:
 * [ ] implement console with prompt
    * [ ] getting information about remote(s)
    * [ ] sending offer to specific remote(s) 