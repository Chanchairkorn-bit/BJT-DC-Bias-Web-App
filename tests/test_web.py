"""Flask HTTP tests using the test client."""

import unittest

from app import app

VALID_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}


class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_index_shows_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Calculate DC Bias", response.data)
        self.assertIn(b"Circuit: Common-Emitter Amplifier", response.data)
        for field in (b'name="vcc"', b'name="r1"', b'name="beta"'):
            self.assertIn(field, response.data)

    def test_post_valid_input_computes_result(self):
        response = self.client.post("/", data=VALID_FORM)
        self.assertEqual(response.status_code, 200)
        # VB, VE, VC, VCE in volts and IC in mA for the reference values.
        self.assertIn(b"1.942", response.data)  # VB
        self.assertIn(b"1.242", response.data)  # VE
        self.assertIn(b"9.294", response.data)  # VC
        self.assertIn(b"8.052", response.data)  # VCE
        self.assertIn(b"1.230", response.data)  # IC mA

    def test_post_non_numeric_shows_error(self):
        data = dict(VALID_FORM, r1="abc")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode("utf-8"), response.data)

    def test_post_zero_resistor_shows_error(self):
        data = dict(VALID_FORM, r2="0")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
