"""Unit tests for the engineering module (dc_bias.py)."""

import unittest

from dc_bias import (
    calculate,
    calculate_by_type,
    calculate_emitter,
    calculate_fixed,
)


class TestVoltageDividerReference(unittest.TestCase):
    """Lab reference values: VCC=12, R1=100k, R2=22k, RC=2.2k, RE=1k,
    beta=100, VBE=0.70."""

    def setUp(self):
        self.r = calculate(
            vcc=12.0,
            r1=100_000.0,
            r2=22_000.0,
            rc=2_200.0,
            re=1_000.0,
            beta=100.0,
            vbe=0.70,
        )

    def test_thevenin(self):
        self.assertAlmostEqual(self.r.vth, 2.1639, places=3)
        self.assertAlmostEqual(self.r.rth, 18_032.7869, places=2)

    def test_currents(self):
        self.assertAlmostEqual(self.r.ib * 1e6, 12.2986, places=2)  # uA
        self.assertAlmostEqual(self.r.ic * 1e3, 1.2299, places=3)   # mA
        self.assertAlmostEqual(self.r.ie * 1e3, 1.2422, places=3)   # mA

    def test_voltages(self):
        self.assertAlmostEqual(self.r.vb, 1.9422, places=3)
        self.assertAlmostEqual(self.r.ve, 1.2422, places=3)
        self.assertAlmostEqual(self.r.vc, 9.2943, places=3)
        self.assertAlmostEqual(self.r.vce, 8.0522, places=3)

    def test_region_is_forward_active(self):
        self.assertEqual(self.r.region, "forward-active")
        self.assertEqual(self.r.warnings, [])


class TestFixedBias(unittest.TestCase):
    """Fixed bias: VCC=12, RB=470k, RC=2.2k, beta=100, VBE=0.70."""

    def setUp(self):
        self.r = calculate_fixed(
            vcc=12.0, rb=470_000.0, rc=2_200.0, beta=100.0, vbe=0.70
        )

    def test_currents(self):
        self.assertAlmostEqual(self.r.ib * 1e6, 24.0426, places=2)
        self.assertAlmostEqual(self.r.ic * 1e3, 2.4043, places=3)
        self.assertAlmostEqual(self.r.ie * 1e3, 2.4283, places=3)

    def test_voltages(self):
        self.assertAlmostEqual(self.r.vb, 0.700, places=3)
        self.assertAlmostEqual(self.r.ve, 0.0, places=3)
        self.assertAlmostEqual(self.r.vc, 6.7106, places=3)
        self.assertAlmostEqual(self.r.vce, 6.7106, places=3)

    def test_region_is_forward_active(self):
        self.assertEqual(self.r.region, "forward-active")
        self.assertEqual(self.r.warnings, [])


class TestEmitterBias(unittest.TestCase):
    """Emitter bias: VCC=12, RB=470k, RC=2.2k, RE=1k, beta=100, VBE=0.70."""

    def setUp(self):
        self.r = calculate_emitter(
            vcc=12.0, rb=470_000.0, rc=2_200.0, re=1_000.0,
            beta=100.0, vbe=0.70,
        )

    def test_currents(self):
        self.assertAlmostEqual(self.r.ib * 1e6, 19.7898, places=2)
        self.assertAlmostEqual(self.r.ic * 1e3, 1.9790, places=3)
        self.assertAlmostEqual(self.r.ie * 1e3, 1.9988, places=3)

    def test_voltages(self):
        self.assertAlmostEqual(self.r.vb, 2.6988, places=3)
        self.assertAlmostEqual(self.r.ve, 1.9988, places=3)
        self.assertAlmostEqual(self.r.vc, 7.6462, places=3)
        self.assertAlmostEqual(self.r.vce, 5.6475, places=3)

    def test_region_is_forward_active(self):
        self.assertEqual(self.r.region, "forward-active")
        self.assertEqual(self.r.warnings, [])


class TestValidation(unittest.TestCase):
    def test_zero_resistor_rejected(self):
        with self.assertRaises(ValueError):
            calculate(12, 0, 22_000, 2_200, 1_000, 100, 0.7)

    def test_zero_beta_rejected(self):
        with self.assertRaises(ValueError):
            calculate(12, 100_000, 22_000, 2_200, 1_000, 0, 0.7)

    def test_negative_vcc_rejected(self):
        with self.assertRaises(ValueError):
            calculate(-5, 100_000, 22_000, 2_200, 1_000, 100, 0.7)

    def test_vbe_not_below_vcc_rejected(self):
        with self.assertRaises(ValueError):
            calculate(5, 100_000, 22_000, 2_200, 1_000, 100, 5.0)

    def test_fixed_zero_rb_rejected(self):
        with self.assertRaises(ValueError):
            calculate_fixed(12, 0, 2_200, 100, 0.7)

    def test_emitter_zero_re_rejected(self):
        with self.assertRaises(ValueError):
            calculate_emitter(12, 470_000, 2_200, 0, 100, 0.7)


class TestRegionWarnings(unittest.TestCase):
    def test_voltage_divider_cutoff_warning(self):
        # VTH = 12 * 1k / (100k + 1k) = 0.1188 V < VBE, so cutoff.
        r = calculate(12, 100_000, 1_000, 2_200, 1_000, 100, 0.7)
        self.assertEqual(r.region, "cutoff")
        self.assertGreaterEqual(len(r.warnings), 1)
        self.assertAlmostEqual(r.ic, 0.0)

    def test_voltage_divider_saturation_warning(self):
        r = calculate(5, 10_000, 4_700, 4_700, 100, 100, 0.7)
        self.assertEqual(r.region, "saturation")
        self.assertGreaterEqual(len(r.warnings), 1)

    def test_fixed_saturation_warning(self):
        r = calculate_fixed(12, 100_000, 10_000, 100, 0.7)
        self.assertEqual(r.region, "saturation")
        self.assertGreaterEqual(len(r.warnings), 1)


class TestDispatcher(unittest.TestCase):
    def test_dispatch_voltage_divider(self):
        r = calculate_by_type(
            "voltage-divider", vcc=12, r1=100_000, r2=22_000,
            rc=2_200, re=1_000, beta=100, vbe=0.7,
        )
        self.assertEqual(r.bias_type, "voltage-divider")

    def test_dispatch_fixed(self):
        r = calculate_by_type(
            "fixed", vcc=12, rb=470_000, rc=2_200, beta=100, vbe=0.7
        )
        self.assertEqual(r.bias_type, "fixed")

    def test_dispatch_emitter(self):
        r = calculate_by_type(
            "emitter", vcc=12, rb=470_000, rc=2_200, re=1_000,
            beta=100, vbe=0.7,
        )
        self.assertEqual(r.bias_type, "emitter")

    def test_dispatch_unknown(self):
        with self.assertRaises(ValueError):
            calculate_by_type("unknown")


if __name__ == "__main__":
    unittest.main()
