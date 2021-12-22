# ICS<sup>3</sup>Fuzzer: A Framework for discovering protocol implementation bugs in supervisory software by fuzzing

<div align=center>
  <img src="https://github.com/boofish/ICS3Fuzzer/blob/main/img/system_architecture.png" width="350" height="250" />
</div>

## Preface

To help understand the ideas in the paper, 
and considering the situation of bug fix,
we show a detailed example of fuzzing GX Works2.
The process of fuzzing other objects is exactly the same.

## Code structure

+ Dispatcher (The main fuzzer)
  + `mutate_engine.py`: for mutation
  + `utils.py`: send comand to the proxy
  + `read_from_plc.py`: the main fuzzer, one of the functionality
  + `length_cluster.py`: protocol analysis
  + `length_fields_analysis.py`: protocol analysis
  + `split_fields.py`: protocol analysis
  + `gen_template.py`:  protocol analysis
  + `state_fiter.py`: pre-processing for selecting states


+ Proxies
  + `./gui/watchdog.py`: launch he environment related to the proxies
  + `./gui/utils/kill_gxworks.py`: kill the process after feeding the inputs
  + `./gui/utils/*.exe`: guiautolits
  + `./gui/utils/source/*.au3`: source code of guiautolits
  + `./gui/driver.py`: GUI proxy
  + `./network/proxy.py`: Traffic proxy

Note that all `*.au3` file need to be adjusted due to different size of screen display. For example, in `read_from_plc.au3`, you may need to adjust the constant `330` in the statement `Local $x = $aPos[0] + 330` to a special value according to your display configuration. Also, the path of executables need to be adjusted too.


## Setup
Currently, ICS3Fuzzer only supports python 2.7.13.
Also, you may need to install some python lib.
+ boofuzz
+ win32evtlog 
+ netzob (for fuzzing process, it is not a must)

Besides, you need to install AutoIt to write `guiautolits`, see https://www.autoitscript.com/site.

We recommend that the main fuzzer and the proxies should be in different machines.
The proxies and the target software can be on the same host, the main fuzzer(dispatcher) should be on another host. 


### 1.Download & configure & install the `boofuzz`

```
git clone https://github.com/jtpereyda/boofuzz.git
```
Our mutation is based on mutate() function, which is deprecated in the latest version. Therefore, we need to roll back its version.

```
cd boofuzz
git checkout 0c03ee04817fae2
python -m pip install .
```
Maybe you will encounter an error log, and you need to install `typing` based on 
```
python -m pip install typing
```


### 2. Run the fuzzer
+ Install the GX Works2, which can be downloaded from the Internet.
+ Configure the IP address of GX Works2 as `0.0.0.0`
+ run `python watchdog.py` on the same machine of GX Works2. It assumed that python lib `win32evtlog` has been installed.
+ run `python read_from_plc.py` from another machine. If things go smoothly, fuzzing process will be started!


