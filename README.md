# Ethereum Alarm Clock Client


This is a client that can be used to monitor the alarm service for upcoming
scheduled calls and execute them when the appropriate block number is reached.

This is only compatable with the 0.6.0 release of alarm.

## Warning

This software should be considered alpha quality.  Please feel free to reach out to me with any issues you run into.

Some things that should probably be added before this is really ready for
public consumption:

* Claiming of scheduled calls.
* Conversion from RPC to IPC


## Installation
### Windows  
If you're running Windows 10 Anniversary, you have to enable windows subsystem for linux, and then you can use the bash shell provided, as if you're running linux.
Otherwise, you can try running coLinux or Debian/Ubuntu distros in VM.
###Linux  
First, check whether you have these packages installed:  

    build-essential
    automake
    pkg-config
    libtool
    libffi-dev
    libgmp-dev
    libssl-dev
    python
    python-pip
    libtool
If you are not sure, just install them using apt/apt-get if you are on Debian or Ubuntu:  
```bash
$ sudo apt-get install build-essential automake pkg-config libtool libffi-dev libgmp-dev libssl-dev python python-pip libtool
```
And, if you are on clean install of Debian/Ubuntu, you'll also need geth:  
```bash
$ bash <(curl -L https://install-geth.ethereum.org)
```
Then, you can install
```bash
$ pip install ethereum-alarm-clock-client
```


## Usage

You can view all of the available commands:

```bash
$ eth_alarm
Usage: eth_alarm [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  scheduler  Run the call scheduler.
```

Or to run the scheduler

```bash
$ eth_alarm scheduler
...
```

In order for the scheduler to function there must be a unlocked JSON-RPC server
running locally.
