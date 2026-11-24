"""Flask HTTP tests for Lab 04 CE SPICE simulator."""

import unittest
from app import app


VALID_CE_SIM = {
    "bias_type": "ce-amplifier",
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "rl": "10",
    "cin": "10",
    "cout": "10",
    "beta": "100",
    "amplitude": "10",
    "frequency": "1000",
    "analysis_mode": "dc",
}


class TestCEWebApp(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_get_ce_simulator_page(self):
        response = self.client.get("/?bias=ce-amplifier")
        self.assertEqual(response.status_code, 200)
        self.assertIn("CE SPICE Simulator".encode("utf-8"), response.data)
        self.assertIn(b"Analysis Mode (SPICE Directive)", response.data)
        self.assertIn(b"Run SPICE Simulation", response.data)
        for field in (b'name="vcc"', b'name="r1"', b'name="rl"', b'name="cin"', b'name="amplitude"'):
            self.assertIn(field, response.data)

    def test_post_ce_dc_simulation(self):
        data = dict(VALID_CE_SIM, analysis_mode="dc")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SPICE Simulation Results", response.data)
        self.assertIn(b"Engine: ngspice", response.data)
        self.assertIn(b"1. DC Operating Point", response.data)
        self.assertIn(b"1.94", response.data)  # VB
        self.assertIn(b"1.28", response.data)  # VE
        self.assertIn(b"9.19", response.data)  # VC

    def test_post_ce_ac_simulation(self):
        data = dict(VALID_CE_SIM, analysis_mode="ac")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2. AC Frequency Response", response.data)
        self.assertIn(b"Midband Gain", response.data)
        self.assertIn(b'<svg viewBox="0 0 700 300"', response.data)
        self.assertIn(b"Magnitude (dB)", response.data)

    def test_post_ce_tran_simulation(self):
        data = dict(VALID_CE_SIM, analysis_mode="tran")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"3. Transient Analysis", response.data)
        self.assertIn(b"Vin Peak:", response.data)
        self.assertIn(b"Vout Peak:", response.data)
        self.assertIn("180° Inverted".encode("utf-8"), response.data)
        self.assertIn(b'<svg viewBox="0 0 700 300"', response.data)

    def test_post_ce_invalid_re_zero(self):
        data = dict(VALID_CE_SIM, re="0")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("มากกว่า 0".encode("utf-8"), response.data)
        self.assertNotIn(b"Status: PASS", response.data)


if __name__ == "__main__":
    unittest.main()
