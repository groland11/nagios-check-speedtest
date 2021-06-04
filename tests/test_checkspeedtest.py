#!/usr/bin/env python3

import io
import unittest
import importlib
st = importlib.import_module("check-speedtest")


class SpeedTestOutput(unittest.TestCase):
    def test_output_norun_noparms(self):
        expected_result = st.UNKNOWN
        expected_message = f'UNKNOWN: Download=? Upload=?'

        speedtest = st.SpeedTest()
        result, message = speedtest.create_output()

        self.assertEqual(result, expected_result)
        self.assertEqual(message, expected_message)

    def test_output_norun_parms01(self):
        expected_result = st.UNKNOWN
        expected_message = f'UNKNOWN: Download=? Upload=?'

        speedtest = st.SpeedTest(1,2)
        result, message = speedtest.create_output()

        self.assertEqual(result, expected_result)
        self.assertEqual(message, expected_message)

    def test_output_norun_parms02(self):
        expected_result = st.UNKNOWN
        expected_message = f'UNKNOWN: Download=? Upload=?'

        speedtest = st.SpeedTest(1, 2, 3, 4)
        result, message = speedtest.create_output()

        self.assertEqual(result, expected_result)
        self.assertEqual(message, expected_message)

if __name__ == "__main__":
    unittest.main()
