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

# Same circuit as VALID_VOLTAGE_DIVIDER, entered in ohms instead of kOhm.
VALID_VOLTAGE_DIVIDER_OHM = {
    "bias_type": "voltage-divider",
    "unit_r": "ohm",
    "vcc": "12",
    "r1": "100000",
    "r2": "22000",
    "rc": "2200",
    "re": "1000",
    "beta": "100",
    "vbe": "0.70",
}

# Same circuit entered in MOhm.
VALID_VOLTAGE_DIVIDER_MOHM = {
    "bias_type": "voltage-divider",
    "unit_r": "mohm",
    "vcc": "12",
    "r1": "0.1",
    "r2": "0.022",
    "rc": "0.0022",
    "re": "0.001",
    "beta": "100",
    "vbe": "0.70",
}


class TestWebApp(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    # ---------- GET ----------
    def test_get_index_shows_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BJT DC Bias Web App", response.data)
        self.assertIn("Lab 03".encode("utf-8"), response.data)
        self.assertIn(b"Calculate DC Bias", response.data)
        self.assertIn(b"Circuit: Common-Emitter Amplifier", response.data)
        for field in (b'name="vcc"', b'name="r1"', b'name="beta"'):
            self.assertIn(field, response.data)

    def test_get_index_shows_unit_selectors(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        for name in (b'name="unit_i"', b'name="unit_v"'):
            self.assertIn(name, response.data)
        for name in (b'name="unit_r1"', b'name="unit_r2"',
                     b'name="unit_rc"', b'name="unit_re"'):
            self.assertIn(name, response.data)

    def test_get_fixed_bias_has_unit_per_resistor(self):
        response = self.client.get("/?bias=fixed")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="unit_rb"', response.data)
        self.assertIn(b'name="unit_rc"', response.data)
        self.assertNotIn(b'name="unit_re"', response.data)

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

    # ---------- POST: default kOhm / mA / V ----------
    def test_post_valid_voltage_divider(self):
        response = self.client.post("/", data=VALID_VOLTAGE_DIVIDER)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)  # VB
        self.assertIn(b"1.242", response.data)  # VE
        self.assertIn(b"9.294", response.data)  # VC
        self.assertIn(b"8.052", response.data)  # VCE
        self.assertIn(b"1.230", response.data)  # IC mA
        self.assertIn(b"0.012", response.data)  # IB mA

    def test_post_valid_fixed(self):
        response = self.client.post("/", data=VALID_FIXED)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"0.700", response.data)  # VB
        self.assertIn(b"6.711", response.data)  # VC/VCE
        self.assertIn(b"2.404", response.data)  # IC mA
        self.assertIn(b"0.024", response.data)  # IB mA

    def test_post_valid_emitter(self):
        response = self.client.post("/", data=VALID_EMITTER)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"2.699", response.data)  # VB
        self.assertIn(b"1.999", response.data)  # VE / IE
        self.assertIn(b"7.646", response.data)  # VC
        self.assertIn(b"5.647", response.data)  # VCE
        self.assertIn(b"1.979", response.data)  # IC mA

    # ---------- POST: selectable units ----------
    def test_post_resistance_in_ohm(self):
        response = self.client.post("/", data=VALID_VOLTAGE_DIVIDER_OHM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)          # VB unchanged
        self.assertIn(b"9.294", response.data)          # VC unchanged
        self.assertIn(b"18032.787", response.data)      # RTH in Ohm
        self.assertIn("Ω".encode("utf-8"), response.data)

    def test_post_resistance_in_mohm(self):
        response = self.client.post("/", data=VALID_VOLTAGE_DIVIDER_MOHM)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)          # VB unchanged
        self.assertIn(b"0.018033", response.data)       # RTH in MOhm
        self.assertIn("MΩ".encode("utf-8"), response.data)

    def test_post_current_in_microamp(self):
        data = dict(VALID_VOLTAGE_DIVIDER, unit_i="ua")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1229.858", response.data)  # IC in uA
        self.assertIn("µA".encode("utf-8"), response.data)

    def test_post_current_in_amp(self):
        data = dict(VALID_VOLTAGE_DIVIDER, unit_i="a")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"0.001230", response.data)  # IC in A

    def test_post_voltage_in_millivolt(self):
        data = dict(VALID_VOLTAGE_DIVIDER, unit_v="mv")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1942.157", response.data)  # VB in mV
        self.assertIn(b"8052.155", response.data)  # VCE in mV
        self.assertIn(b"mV", response.data)

    def test_post_voltage_in_microvolt(self):
        data = dict(VALID_VOLTAGE_DIVIDER, unit_v="uv")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1942156.728", response.data)  # VB in uV

    def test_invalid_unit_falls_back_to_default(self):
        data = dict(VALID_VOLTAGE_DIVIDER, unit_r="parsec", unit_i="furlong", unit_v="stone")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)
        self.assertIn(b"1.230", response.data)

    def test_unit_choice_persists_in_form(self):
        data = dict(VALID_VOLTAGE_DIVIDER_OHM, unit_i="ua", unit_v="mv")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<option value="ohm" selected>', response.data)
        self.assertIn(b'<option value="ua" selected>', response.data)
        self.assertIn(b'<option value="mv" selected>', response.data)

    # ---------- POST: one unit per resistor ----------
    def test_each_resistor_uses_its_own_unit(self):
        data = {
            "bias_type": "voltage-divider",
            "vcc": "12",
            "unit_r1": "kohm", "r1": "100",
            "unit_r2": "ohm", "r2": "22000",
            "unit_rc": "mohm", "rc": "0.0022",
            "unit_re": "ohm", "re": "1000",
            "beta": "100",
            "vbe": "0.70",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)  # VB
        self.assertIn(b"8.052", response.data)  # VCE
        self.assertIn(b"1.230", response.data)  # IC mA
        self.assertIn(b"18.033", response.data)  # RTH in R1's unit (kOhm)

    def test_per_field_unit_overrides_global_default(self):
        # unit_r=ohm sets the fallback, but R1 explicitly asks for kOhm.
        data = {
            "bias_type": "voltage-divider",
            "vcc": "12",
            "unit_r": "ohm",
            "unit_r1": "kohm", "r1": "100",
            "unit_r2": "kohm", "r2": "22",
            "unit_rc": "kohm", "rc": "2.2",
            "unit_re": "kohm", "re": "1",
            "beta": "100",
            "vbe": "0.70",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"1.942", response.data)
        self.assertIn(b"8.052", response.data)

    def test_mixed_units_selected_in_form(self):
        data = {
            "bias_type": "fixed",
            "vcc": "12",
            "unit_rb": "mohm", "rb": "0.47",
            "unit_rc": "ohm", "rc": "2200",
            "beta": "100",
            "vbe": "0.70",
        }
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"6.711", response.data)      # VC
        self.assertIn(b"0.470000", response.data)   # RB shown in its own unit
        # Schematic labels follow each resistor's own unit.
        self.assertIn("0.47 MΩ".encode("utf-8"), response.data)
        self.assertIn("2200 Ω".encode("utf-8"), response.data)

    # ---------- POST: validation ----------
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

    def test_error_message_uses_selected_unit(self):
        data = dict(VALID_VOLTAGE_DIVIDER_OHM, r1="abc")
        response = self.client.post("/", data=data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("R1 (Ω)".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
