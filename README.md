# nagios-check-speedtest
Nagios check to test internet connection speed.

## Prerequisites
- Python 3.8
- Package "speedtest-cli" (can be installed by package manager or pip)

## Usage
```
./check-speedtest.py -h
usage: check-speedtest.py [-h] [-w [MINDOWNLOAD_WARNING]] [-c [MINDOWNLOAD_CRITICAL]] [-W [MINUPLOAD_WARNING]] [-C [MINUPLOAD_CRITICAL]] [-v] [--log-file LOGFILE]

Nagios check for internet connection speed

optional arguments:
-h, --help            show this help message and exit
-w [MINDOWNLOAD_WARNING], --warning [MINDOWNLOAD_WARNING]
Lower download speed warning limit (Mbit/s), default: 0 (no warning)
-c [MINDOWNLOAD_CRITICAL], --critical [MINDOWNLOAD_CRITICAL]
Lower download speed critical limit (Mbit/s), default: 0 (no critical)
-W [MINUPLOAD_WARNING], --Warning [MINUPLOAD_WARNING]
Lower upload speed warning limit (Mbit/s), default: 0 (no warning)
-C [MINUPLOAD_CRITICAL], --Critical [MINUPLOAD_CRITICAL]
Lower Upload speed critical limit (Mbit/s), default: 0 (no critical
-v, --verbose         enable verbose output
--log-file LOGFILE    file to log to, default: <stdout>
```
## Examples
```
$ check-speedtest.py -w 5 -c 4 -W 3 -C 2
WARNING: Download=9.03 Upload=2.46|Download=9.03;5;4;; Upload=2.46;3;2;;
```
