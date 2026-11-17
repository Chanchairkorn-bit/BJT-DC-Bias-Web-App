"""Flask HTTP tests using the test client."""

import unittest

from app import app

VALID_VOLTAGE_DIVIDER = {
    "bias_type": "voltage-divider",
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.70",
}

VALID_FIXED = {
    "bias_type": "fixed",
    "vcc": "12",
    "rb": "470",
    "rc": "2.2",
    "beta": "100",
    "vbe": "0.70",
}

VALID_EMITTER = {
    "bias_type": "emitter",
    "vcc": "12",
    "rb": "470",
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

    def test_get_fixed_bias_shows_rb(self):
        response = self.client.get("/?bias=fixed")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="rb"', response.data)
        self.assertIn(b"Fixed Bias", response.data)

    def test_get_emitter_bias_shows_re(self):
        response = self.client.get("/?bias=emitter")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="rb"', response.data)
        self.assertIn(b'name="re"', response.data)
        self.assertIn(b"Emitter Bias", response.data)

    def test_post_valid_voltage_divider(self):
        response = self.client.post("/", data=VALID_VOLTAGE_DIVIDER)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)  # VB
        self.assertIn(b"1.242", response.data)  # VE
        self.assertIn(b"9.294", response.data)  # VC
        self.assertIn(b"8.052", response.data)  # VCE
        self.assertIn(b"1.230", response.data)  # IC mA

    def test_post_valid_fixed(self):
        response = self.client.post("/", data=VALID_FIXED)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"0.700", response.data)  # VB
        self.assertIn(b"6.711", response.data)  # VC/VCE
        self.assertIn(b"2.404", response.data)  # IC mA
        self.assertIn(b"24.043", response.data)  # IB uA

    def test_post_valid_emitter(self):
        response = self.client.post("/", data=VALID_EMITTER)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2.699", response.data)  # VB
        self.assertIn(b"1.999", response.data)  # VE / IE
        self.assertIn(b"7.646", response.data)  # VC
        self.assertIn(b"5.647", response.data)  # VCE
        self.assertIn(b"1.979", response.data)  # IC mA

    def test_post_non_numeric_shows_error(self):
        data = dict(VALID_VOLTAGE_DIVIDER, r1="abc")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ตัวเลข".encode("utf-8"), response.data)

    def test_post_zero_resistor_shows_error(self):
        data = dict(VALID_VOLTAGE_DIVIDER, r2="0")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode("utf-8"), response.data)

    def test_post_fixed_missing_rb_shows_error(self):
        data = dict(VALID_FIXED)
        data.pop("rb")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอกค่า".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
