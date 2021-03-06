#!/usr/bin/env python3
""" Nagios check to test internet connection speed.

Requirements
    Python >= 3.8
    Package "speedtest-cli" (can be installed by package manager or pip)

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""
import argparse
import logging
import sys
from subprocess import run, TimeoutExpired

__license__ = "GPLv3"
__version__ = "0.9.1"

# Nagios return codes: https://nagios-plugins.org/doc/guidelines.html#AEN78
OK = 0
WARNING = 1
CRITICAL = 2
UNKNOWN = 3
return_codes = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']

# Global logging object
logger = logging.getLogger(__name__)


def parseargs() -> argparse.Namespace:
    """ Parse command-line arguments """
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
        help='Lower upload speed critical limit (Mbit/s), default: 0 (no critical)',
        dest='minupload_critical', type=int, default=0)
    parser.add_argument(
        '--log-file', nargs=1, required=False,
        help='file to log to, default: <stdout>',
        dest='logfile', type=str)
    parser.add_argument(
        '-v', '--verbose', required=False,
        help='enable verbose output', dest='verbose',
        action='store_true')
    parser.add_argument('-V', '--version', action='version', version='%(prog)s ' + __version__)

    args = parser.parse_args()
    return args


class SpeedTest:
    def __init__(self, download_warning=None, download_critical=None,
                 upload_warning=None, upload_critical=None):
        self.download: float = 0.0
        self.upload: float = 0.0
        self.download_warning: int = download_warning
        self.download_critical: int = download_critical
        self.upload_warning: int = upload_warning
        self.upload_critical: int = upload_critical
        self.rc = -1

    def run(self, cmd: list) -> tuple:
        """Run speedtest and return result"""
        try:
            logger.debug(f'Running OS command line: {cmd} ...')
            process = run(cmd, check=True, timeout=60, capture_output=True)
            self.rc = process.returncode
            stats_line = process.stdout.decode('utf-8').strip()
            logger.debug(stats_line)
        except (TimeoutExpired, ValueError) as e:
            logger.warning(f'{e}')
            sys.exit(UNKNOWN)
        except FileNotFoundError as e:
            logger.critical(f'CRITICAL: Missing program "speedtest-cli" ({e})')
            sys.exit(CRITICAL)
        except Exception as e:
            logger.critical(f'CRITICAL: {e}')
            sys.exit(CRITICAL)

        self.download = float(stats_line.split(',')[6]) / 1000000
        self.upload = float(stats_line.split(',')[7]) / 1000000
        logger.debug(f'Download: {self.download:.2f} Mbit/s; Upload: {self.upload:.2f} Mbit/s')
        return self.download, self.upload

    def create_output(self) -> tuple:
        """Verify result and return output in Nagios format"""
        if self.rc >= 0:
            result = OK
        else:
            return UNKNOWN, f'{return_codes[UNKNOWN]}: Download=? Upload=?'

        if self.download_critical is not None and \
                self.download <= self.download_critical and self.download_critical > 0:
            result = CRITICAL
        if self.download_warning is not None and self.download <= self.download_warning and self.download_warning > 0:
            result = WARNING

        if self.upload_critical is not None and \
                self.upload <= self.upload_critical and self.upload_critical > 0:
            result = CRITICAL
        if self.upload_warning is not None and \
                self.upload <= self.upload_warning and self.upload_warning > 0 and result != CRITICAL:
            result = WARNING

        msg = f'{return_codes[result]}: Download={self.download:.2f} Upload={self.upload:.2f}'
        perfdata = f'Download={self.download:.0f};' \
                   f'{str(self.download_warning) if self.download_warning > 0 else ""};' \
                   f'{str(self.download_critical) if self.download_critical > 0 else ""};; ' \
                   f'Upload={self.upload:.0f};' \
                   f'{str(self.upload_warning) if self.upload_warning > 0 else ""};' \
                   f'{str(self.upload_critical) if self.upload_critical > 0 else ""};;'

        message = f'{msg}|{perfdata}'
        logger.debug(message)
        return result, message


class LogFilterWarning(logging.Filter):
    """Logging filter >= WARNING"""
    def filter(self, record):
        return record.levelno in (logging.DEBUG, logging.INFO, logging.WARNING)


def get_logger(verbose: bool = False) -> logging.Logger:
    """Retrieve logging object"""
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Log everything >= WARNING to stdout
    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.DEBUG)
    h1.setFormatter(logging.Formatter(fmt='%(asctime)s [%(process)d] %(levelname)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    h1.addFilter(LogFilterWarning())

    # Log errors to stderr
    h2 = logging.StreamHandler(sys.stderr)
    h2.setFormatter(logging.Formatter(fmt='%(asctime)s [%(process)d] %(levelname)s: %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S'))
    h2.setLevel(logging.ERROR)

    logger.addHandler(h1)
    logger.addHandler(h2)

    return logger


def get_thresholds(args: argparse.Namespace) -> tuple:
    """Retrieve thresholds for check from command line parameters"""
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
    get_logger(args.verbose)

    # Check command line arguments
    download_warning, download_critical, upload_warning, upload_critical = get_thresholds(args)

    # Run speedtest-cli command
    speedtest = SpeedTest(download_warning, download_critical, upload_warning, upload_critical)
    speedtest.run(['speedtest-cli', '--csv'])
    result, message = speedtest.create_output()
    print(message)

    return result


if __name__ == '__main__':
    main()
