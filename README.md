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
  addresses  List the addresses for different versions of...
  scheduler  Run the call scheduler.
```

Or to run the scheduler

```bash
$ eth_alarm scheduler
...
```

In order for the scheduler to function there must be a unlocked JSON-RPC server
running locally.
