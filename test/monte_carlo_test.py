'''
# Copyright (c) 2016-2025 by University of Kassel and Fraunhofer Institute for Energy Economics
and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.12.2025
@author: fnuetz
'''

import unittest
import numpy as np
from monte_carlo_test_nets import *
from monte_carlo import estimate_mttf_mttr, NUMBA_AVAILABLE


class ReliabilityNetTest(unittest.TestCase):
    """Tests for Reliability Monte-Carlo-Simulation"""

    @classmethod
    def setUpClass(cls):
        """Init all tests"""

        # declare tolerance for stochastic approximation
        cls.TOL = 2e-2 # 1%

        # Failure and Repair Rates.
        cls.lam_n = 1
        cls.lam_e = 0.1
        cls.mu_n = 10
        cls.mu_e = 1


        # calc availability of nodes and edges
        cls.A_n = (1 / cls.lam_n) / (1 / cls.lam_n + 1 / cls.mu_n)
        cls.A_e = (1 / cls.lam_e) / (1 / cls.lam_e + 1 / cls.mu_e)

        # config different methods of calculation
        cls.method_configs = []

        # python-fallback (Union-Find)
        cls.method_configs.append(
            ("python_union_find", {"use_numba": False, "parallel": False})
        )

        # numba variants, if available
        if NUMBA_AVAILABLE:
            cls.method_configs.append(
                ("numba_serial", {"use_numba": True, "parallel": False})
            )
            cls.method_configs.append(
                ("numba_parallel", {"use_numba": True, "parallel": True})
            )

    def _test_non_repairable(self, network_func, mttf_func, network_name,
                             n_samples=int(1e6)):
        """
        helper for non-repairable tests

        :INPUT:
            **network_func**   function to declare network
            **mttf_func**      function to approximate mttf
            **network_name**   string, name of network
            **n_samples**      int, number of samples
        """
        # get non-repairable network (µ = 0)
        G = network_func(1 / self.lam_n, 1 / self.lam_e, 0, 0)

        # calc MTTF analytically
        MTTF_analytical = mttf_func(self.lam_n, self.lam_e)

        for method_name, method_kwargs in self.method_configs:
            with self.subTest(method=method_name, network=network_name):

                # calc MTTF using Monte-Carlo
                MTTF_MC, MTTR_MC = estimate_mttf_mttr(G, "S", "T", N=n_samples, depth=1, **method_kwargs)

                self.assertIsNotNone(MTTF_MC,
                                     f"{network_name} ({method_name}): estimate_mttf_mttr returned None for MTTF.")

                self.assertTrue(
                    np.isinf(MTTR_MC),
                f"{network_name} ({method_name}): Expected MTTR=inf for non-repairable system, "
                    f"got {MTTR_MC} instead.")

                # relative error
                rel_error = abs(MTTF_MC - MTTF_analytical) / MTTF_analytical

                self.assertLess(
                    rel_error,
                    self.TOL,
                    f"Test failed for {network_name}: MonteCarlo (MTTF = {MTTF_MC:.4f}) deviates by more than {self.TOL*100}% from "
                    f"analytical solution (MTTF = {MTTF_analytical:.4f}) "
                    f"(relative Error: {rel_error:.2%})."
                )

    def _test_repairable(self, network_func, availability_formula,
                         network_name, n_samples=1000, max_cycles=200):
        """
        helper for repairable tests

        :INPUT:
            **network_func**        - function to declare network
            availability_formula:   - function for calculate availability (analytical
            network_name:           - string, name of network (for error message)
            n_samples:              - int, number of Monte-Carlo-Samples
            depth:                  - int, number of MC-cycles (see MC-Doc)
        """
        # Get network
        G = network_func(1 / self.lam_n, 1 / self.lam_e, 1 / self.mu_n, 1 / self.mu_e)

        # calc availabilty from analytical solution
        A_analytical = availability_formula()

        for method_name, method_kwargs in self.method_configs:
            with self.subTest(method=method_name, network=network_name):

                # MonteCarlo sim
                MTTF_MC, MTTR_MC = estimate_mttf_mttr(
                    G, "S", "T", N=n_samples, depth=max_cycles, **method_kwargs
                )

                self.assertIsNotNone(
                    MTTF_MC,
                    f"{network_name} ({method_name}): estimate_mttf_mttr returned None for MTTF."
                )

                self.assertIsNotNone(
                    MTTR_MC,
                    f"{network_name} ({method_name}): estimate_mttf_mttr returned None for MTTR."
                )

                # calc availability from MonteCarlo
                A_MC = MTTF_MC / (MTTF_MC + MTTR_MC)

                # relative error
                rel_error = abs(A_analytical - A_MC) / A_analytical

                # Assertion
                self.assertLess(
                    rel_error,
                    self.TOL,
                    f"Test failed for {network_name}: Monte-Carlo (Availabilty = {A_MC:.4f}) deviates by more than {self.TOL*100}% from "
                    f"analytical solution (Availability = {A_analytical:.4f}) "
                    f"(relative error = {rel_error:.2%})."
                )

    # === call tests for specific nets ===

    def test_6n_serial_non_repairable(self):
        """Test 6N-Seriell (non-repairable)"""
        # Analytische MTTF-Formeln
        MTTF_6N = lambda lam_n, lam_e: 1 / (7 * lam_n + 6 * lam_e)
        self._test_non_repairable(
            N6_seriell,
            MTTF_6N,
            "6N-seriell (non-repairable)"
        )

    def test_6n_serial_repairable(self):
        """Test 6N-Seriell (repairable)"""
        availability_formula = lambda: (self.A_n ** 7) * (self.A_e ** 6)
        self._test_repairable(
            N6_seriell,
            availability_formula,
            "6N-seriell (repairable)"
        )

    def test_3n_parallel_non_repairable(self):
        """Test 3N-parallel (non-repairable)"""
        MTTF_3N = lambda lam_n, lam_e: (
                3 / (2 * lam_e + 3 * lam_n) - 3 / (4 * lam_n + 4 * lam_e) + 1 / (6 * lam_e + 5 * lam_n)
        )
        self._test_non_repairable(
            N3_parallel,
            MTTF_3N,
            "3N-parallel (non-repairable)",
            n_samples=100000  # Mehr Samples für genauere Approximation
        )

    def test_3n_parallel_repairable(self):
        """Test 3N-parallel (repairable)"""
        availability_formula = lambda: (
                self.A_n ** 2 * (1 - (1 - self.A_n * self.A_e ** 2) ** 3)
        )
        self._test_repairable(
            N3_parallel,
            availability_formula,
            "3N-parallel (repairable)"
        )

    def test_2n_parallel_non_repairable(self):
        """Test 2N-parallel (N4_11, non-repairable) """
        MTTF_2N = lambda lam_n, lam_e: (
                2 / (3 * lam_n + 2 * lam_e) - 1 / (4 * lam_n + 4 * lam_e)
        )
        self._test_non_repairable(
            N4_11,
            MTTF_2N,
            "2N-parallel (non-repairable)",
            n_samples=100000
        )

    def test_2n_parallel_repairable(self):
        """Test 2N-parallel (N4_11, repairable)"""

        def availability_formula():
            A_alpha = self.A_e ** 2 * self.A_n
            A_N4 = 1 - (1 - A_alpha) ** 2
            return A_N4 * self.A_n ** 2

        self._test_repairable(
            N4_11,
            availability_formula,
            "2N-parallel (repairable)"
        )

if __name__ == '__main__':
    unittest.main()