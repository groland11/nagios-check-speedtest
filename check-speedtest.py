#!/usr/bin/env python3

import argparse
import logging
import sys
from subprocess import run, TimeoutExpired

# Nagios return codes: https://nagios-plugins.org/doc/guidelines.html#AEN78
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
return_codes = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']


class LogFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.DEBUG, logging.INFO, logging.WARNING)


def parseargs() -> argparse.Namespace:
    """ Defining command-line arguments """
    parser = argparse.ArgumentParser(description='Nagios check for internet connection speed')
    parser.add_argument(
        '-w', '--warning', nargs='?', required=False,
        help='Lower download speed warning limit (Mbit/s), default: 0 (no warning)',
        dest='mindownload_warning', type=int, default=0)
    parser.add_argument(
        '-c', '--critical', nargs='?', required=False,
        help='Lower download speed critical limit (Mbit/s), default: 0 (no critical)',
        dest='mindownload_critical', type=int, default=0)
    parser.add_argument(
        '-W', '--Warning', nargs='?', required=False,
        help='Lower upload speed warning limit (Mbit/s), default: 0 (no warning)',
        dest='minupload_warning', type=int, default=0)
    parser.add_argument(
        '-C', '--Critical', nargs='?', required=False,
        help='Lower Upload speed critical limit (Mbit/s), default: 0 (no critical',
        dest='minupload_critical', type=int, default=0)
    parser.add_argument(
        '-v', '--verbose', required=False,
        help='enable verbose output', dest='verbose',
        action='store_true')
    parser.add_argument(
        '--log-file', nargs=1, required=False,
        help='file to log to, default: <stdout>',
        dest='logfile', type=str)

    args = parser.parse_args()

    return args


def get_logger(verbose: bool = False) -> logging.Logger:
    """Retrieve logging object"""
    logger = logging.getLogger()
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.DEBUG)
    h1.setFormatter(logging.Formatter(fmt='%(asctime)s [%(process)d] %(levelname)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    h1.addFilter(LogFilter())

    h2 = logging.StreamHandler(sys.stderr)
    h2.setFormatter(logging.Formatter(fmt='%(asctime)s [%(process)d] %(levelname)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    h2.setLevel(logging.ERROR)

    logger.addHandler(h1)
    logger.addHandler(h2)

    return logger


def get_thresholds(args: argparse.Namespace) -> tuple:
    wdown = max(int(args.mindownload_warning), 0)
    cdown = max(int(args.mindownload_critical), 0)
    if wdown < cdown:
        wdown = cdown

    wup = max(int(args.minupload_warning), 0)
    cup = max(int(args.minupload_critical), 0)
    if wup < cup:
        wup = cup

    return wdown, cdown, wup, cup


def main():
    """Main program flow"""
    result = OK

    args = parseargs()
    logger = get_logger(args.verbose)

    # Checking command line arguments
    warning_download, critical_download, warning_upload, critical_upload =  get_thresholds(args)

    # Run speedtest-cli command
    try:
        cmd_df = ['speedtest-cli', '--csv']
        logger.debug(f'Running OS command line: {cmd_df} ...')
        process = run(cmd_df, check=True, timeout=30, capture_output=True)
        stats_line = process.stdout.decode('utf-8').strip()
        logger.debug(stats_line)
    except (TimeoutExpired, ValueError) as e:
        logger.warning(f'{e}')
        sys.exit(UNKNOWN)
    except Exception as e:
        if e.errno == 2:
            logger.critical(f'CRITICAL: Missing program "speedtest-cli" ({e})')
        else:
            logger.critical(f'CRITICAL: {e}')
        sys.exit(CRITICAL)

    download = float(stats_line.split(',')[6]) / 1000000
    upload = float(stats_line.split(',')[7]) / 1000000
    logger.debug(f'Download: {download:.2f} Mbit/s; Upload: {upload:.2f} Mbit/s')

    # Verify result and print output in Nagios format
    if download <= critical_download and critical_download > 0:
        result = CRITICAL
    if download <= warning_download and warning_download > 0:
        result = WARNING

    if upload <= critical_upload and critical_upload > 0:
        result = CRITICAL
    if upload <= warning_upload and warning_upload > 0 and result != CRITICAL:
        result = WARNING

    msg = f'{return_codes[result]}: Download={download:.2f} Upload={upload:.2f}'
    perfdata = f'Download={download:.2f};' \
               f'{str(warning_download) if warning_download > 0 else ""};' \
               f'{str(critical_download) if critical_download > 0 else ""};; ' \
               f'Upload={upload:.2f};' \
               f'{str(warning_upload) if warning_upload > 0 else ""};' \
               f'{str(critical_upload) if critical_upload > 0 else ""};;'
    logger.debug(f'{msg}|{perfdata}')
    print(f'{msg}|{perfdata}')

    return result


if __name__ == '__main__':
    main()
