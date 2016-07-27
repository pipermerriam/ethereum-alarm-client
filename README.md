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
###Windows [WIP]  
We need to get a library that secp256k1 depends on.  
You can download it here: [MingW](http://heanet.dl.sourceforge.net/project/mingw/Installer/mingw-get-setup.exe)  
And in the dialog select:  
From "Basic Setup":  

    mingw-developer-toolkit  
    mingw32-base  
    mingw32-gcc-g++  
    msys-base  

From "All Packages"  

    msys-crypt  

	
Then you'll need to copy file libgcc_s_dw2-1.dll from C:\mingw\bin to C:\python27\scripts  
Check if you can import the library by going into python interactive console and running  
```python
>>> import secp256k1
```
If that works you can move on onto instalation of ethereum-alarm-clock-client itself.  
You need to create a requirements.txt file, wherever you want, with this content:
```
ethereum-alarm-clock-client
git+https://github.com/chfast/secp256k1-py.git@fe39e4c#egg=secp256k1
```
The second line is important, it replaces the secp256k1 dependency with the git repository of secp256k1-transient, we need to do this, because secp256k1 won't compile on Windows, where as secp256k1-transient will, if you have 32 bit instalation of python.  
Now you can run:
```
pip install -r requirements.txt
```
If you named your file differently, replace requirements.txt by you filename.
[INCOMPLETE]
###Linux
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
