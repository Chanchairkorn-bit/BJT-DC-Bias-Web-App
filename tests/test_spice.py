"""Unit tests for the SPICE simulation engine (spice_engine.py)."""

import unittest
from spice_engine import CircuitParams, run_simulation, validate_params


class TestSpiceValidation(unittest.TestCase):
    def test_valid_params(self):
        p = CircuitParams()
        errors = validate_params(p)
        self.assertEqual(errors, [])

    def test_invalid_re_zero(self):
        p = CircuitParams(re=0.0)
        errors = validate_params(p)
        self.assertTrue(any("RE" in e for e in errors))

    def test_invalid_negative_vcc(self):
        p = CircuitParams(vcc=-12.0)
        errors = validate_params(p)
        self.assertTrue(any("VCC" in e for e in errors))

    def test_invalid_negative_freq(self):
        p = CircuitParams(frequency=-1000)
        errors = validate_params(p)
        self.assertTrue(any("frequency" in e for e in errors))


class TestSpiceExecution(unittest.TestCase):
    def test_dc_simulation(self):
        p = CircuitParams()
        res = run_simulation(p, mode="dc")
        self.assertEqual(res["status"], "success")
        self.assertIn("dc", res)
        dc = res["dc"]
        self.assertAlmostEqual(dc["vb"], 1.94, delta=0.1)
        self.assertAlmostEqual(dc["ve"], 1.28, delta=0.1)
        self.assertAlmostEqual(dc["vc"], 9.19, delta=0.2)
        self.assertAlmostEqual(dc["vce"], 7.90, delta=0.3)
        self.assertAlmostEqual(dc["ic"] * 1e3, 1.27, delta=0.1)
        self.assertIn("analytical", res)

    def test_ac_simulation(self):
        p = CircuitParams()
        res = run_simulation(p, mode="ac")
        self.assertEqual(res["status"], "success")
        self.assertIn("ac", res)
        ac = res["ac"]
        self.assertIn("meta", ac)
        self.assertIn("midband_gain_db", ac["meta"])
        self.assertIn("<svg", ac["svg"])
        self.assertGreater(ac["data_points"], 10)

    def test_tran_simulation(self):
        p = CircuitParams(amplitude=0.01, frequency=1000.0)
        res = run_simulation(p, mode="tran")
        self.assertEqual(res["status"], "success")
        self.assertIn("tran", res)
        tran = res["tran"]
        self.assertIn("meta", tran)
        self.assertTrue(tran["meta"].get("phase_inverted", False))
        self.assertIn("<svg", tran["svg"])
        self.assertGreater(tran["data_points"], 50)

    def test_change_re_affects_operating_point(self):
        p1 = CircuitParams(re=1000.0)
        res1 = run_simulation(p1, mode="dc")
        p2 = CircuitParams(re=2000.0)
        res2 = run_simulation(p2, mode="dc")
        self.assertNotEqual(res1["dc"]["ve"], res2["dc"]["ve"])
        self.assertNotEqual(res1["dc"]["ic"], res2["dc"]["ic"])


if __name__ == "__main__":
    unittest.main()
