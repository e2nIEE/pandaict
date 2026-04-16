'''
Created on 22.12.2025
@author: fnuetz
'''

import unittest
import numpy as np
from monte_carlo_test_nets import *
from pandaict.reliability.monte_carlo import estimate_mttf_mttr, NUMBA_AVAILABLE

class ReliabilityNetTest(unittest.TestCase):
    """Tests for Reliability Monte-Carlo-Simulation"""

    @classmethod
    def setUpClass(cls):
        """Init all tests"""

        # declare tolerance for stochastic approximation
        cls.TOL = 2e-2 # 2%

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

        cls.numba_only_configs = []
        if NUMBA_AVAILABLE:
            cls.numba_only_configs.append(
                ("numba_serial", {"use_numba": True, "parallel": False})
            )
            cls.numba_only_configs.append(
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
                res = estimate_mttf_mttr(G, "S", "T", N=n_samples, depth=1, min_connected=-1, **method_kwargs)

                # unpack results
                MTTF_MC = res['mttf']
                MTTR_MC = res['mttr']

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
            **network_func**            - function to declare network
            **availability_formula**    - function for calculate availability (analytical
            **network_name**            - string, name of network (for error message)
            **n_samples**               - int, number of Monte-Carlo-Samples
            **depth**                   - int, number of MC-cycles (see MC-Doc)
        """
        # Get network
        G = network_func(1 / self.lam_n, 1 / self.lam_e, 1 / self.mu_n, 1 / self.mu_e)

        # calc availabilty from analytical solution
        A_analytical = availability_formula()

        for method_name, method_kwargs in self.method_configs:
            with self.subTest(method=method_name, network=network_name):

                # MonteCarlo sim
                res = estimate_mttf_mttr(
                    G, "S", "T", N=n_samples, depth=max_cycles, min_connected=-1, **method_kwargs
                )

                # Unpack results
                MTTF_MC = res['mttf']
                MTTR_MC = res['mttr']

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


    def _test_multi_source_non_repairable(self, network_func, mttf_func,
                                          sources, targets, min_connected,
                                          network_name, n_samples=int(1e6)):
        """
        helper for non-repairable multi-source/target tests
        :INPUT:
            **network_func**    - function to declare network
            **mttf_func**       - function to approximate mttf
            **sources**         - int, identifier of source node
            **targets**         - int, identifier of target node
            **network_name**    - string, name of network
            **n_samples**       - int, number of samples
        """
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available - skipping multi-source/target test")

        G = network_func(1 / self.lam_n, 1 / self.lam_e, 0, 0)
        MTTF_analytical = mttf_func(self.lam_n, self.lam_e)

        for method_name, method_kwargs in self.numba_only_configs:
            with self.subTest(method=method_name, network=network_name, min_connected=min_connected):
                res = estimate_mttf_mttr(
                    G, sources, targets,
                    N=n_samples, depth=200,
                    min_connected=min_connected,
                    **method_kwargs
                )

                MTTF_MC = res['mttf']
                MTTR_MC = res['mttr']

                self.assertIsNotNone(
                    MTTF_MC,
                    f"{network_name} ({method_name}, min_connected={min_connected}): MTTF is None"
                )

                self.assertTrue(
                    np.isinf(MTTR_MC),
                    f"{network_name} ({method_name}): Expected MTTR=inf, got {MTTR_MC}"
                )

                rel_error = abs(MTTF_MC - MTTF_analytical) / MTTF_analytical

                self.assertLess(
                    rel_error,
                    self.TOL,
                    f"{network_name} ({method_name}, min_connected={min_connected}): "
                    f"MTTF_MC={MTTF_MC:.4f} vs MTTF_analytical={MTTF_analytical:.4f} "
                    f"(error={rel_error:.2%})"
                )

    def _test_multi_source_repairable(self, network_func, availability_func,
                                      sources, targets, min_connected,
                                      network_name, n_samples=1000, max_cycles=200):
        """
        Helper for repairable Multi-Source/Target Tests.
        """
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available - skipping multi-source/target test")

        G = network_func(1 / self.lam_n, 1 / self.lam_e, 1 / self.mu_n, 1 / self.mu_e)
        A_analytical = availability_func()

        for method_name, method_kwargs in self.numba_only_configs:
            with self.subTest(method=method_name, network=network_name, min_connected=min_connected):
                res = estimate_mttf_mttr(
                    G, sources, targets,
                    N=n_samples, depth=max_cycles,
                    min_connected=min_connected,
                    **method_kwargs
                )

                MTTF_MC = res['mttf']
                MTTR_MC = res['mttr']

                self.assertIsNotNone(MTTF_MC)
                self.assertIsNotNone(MTTR_MC)

                A_MC = MTTF_MC / (MTTF_MC + MTTR_MC)
                rel_error = abs(A_analytical - A_MC) / A_analytical

                self.assertLess(
                    rel_error,
                    self.TOL,
                    f"{network_name} ({method_name}, min_connected={min_connected}): "
                    f"A_MC={A_MC:.4f} vs A_analytical={A_analytical:.4f} "
                    f"(error={rel_error:.2%})"
                )


    # === call tests for specific nets ===

    def test_6n_serial_non_repairable(self):
        """Test 6N-Seriell (non-repairable)"""
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
            "3N-parallel (non-repairable)"
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
            "2N-parallel (non-repairable)"
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

    # ==========================================================================
    # Multi-Source/Target Tests (min_connected>1, Numba only)
    # ==========================================================================
    def test_two_sources_independent_require_all_non_repairable(self):
        """
        Test: Two independent paths, min_connected=-1 (all) (non-repairable).
        """
        def mttf_require_all(lam_n, lam_e):
            return 1 / (2 * lam_n + 4 * lam_e)

        self._test_multi_source_non_repairable(
            network_func=two_sources_independent,
            mttf_func=mttf_require_all,
            sources=["S1", "S2"],
            targets="T",
            min_connected=-1,
            network_name="Two independent sources (min_connected=-1, non-rep)"
        )

    def test_two_sources_independent_require_all_repairable(self):
        """
        Test: Two independent paths, min_connected=-1 (repairable).

        Availability = (A_n * A_e**2)**2 = A_n**2 * A_e**4

        """
        def availability_require_all():
            A_path = self.A_n * self.A_e ** 2
            return A_path ** 2

        self._test_multi_source_repairable(
            network_func=two_sources_independent,
            availability_func=availability_require_all,
            sources=["S1", "S2"],
            targets="T",
            min_connected=-1,
            network_name="Two independent sources (min_connected=-1, rep)"
        )

    def test_two_sources_require_all_vs_require_any(self):
        """
        Comparison test: min_connected=1 should have higher reliability than min_connected=-1 (all required).

        min_connected=1 (parallel): R = 1 - (1 - R_path)**2
        min_connected=-1 (series): R = R_path**2

        Since 1 - (1-x)**2 > x**2 for x in (0,1), MTTF(min_connected=1) > MTTF(min_connected=-1)
        """
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available")

        G = two_sources_independent(1 / self.lam_n, 1 / self.lam_e, 0, 0)

        for method_name, method_kwargs in self.numba_only_configs:
            with self.subTest(method=method_name):
                res_any = estimate_mttf_mttr(
                    G, ["S1", "S2"], "T", N=int(1e6),
                    min_connected=1, **method_kwargs
                )
                res_all = estimate_mttf_mttr(
                    G, ["S1", "S2"], "T", N=int(1e6),
                    min_connected=-1, **method_kwargs
                )

                self.assertGreater(
                    res_any['mttf'], res_all['mttf'],
                    "min_connected=1 (any) should have higher MTTF than min_connected=-1 (all)"
                )

    def test_shared_component_require_all_non_repairable(self):
        """
        Test: Shared component, min_connected=-1 (non-repairable).
        """
        def mttf_require_all(lam_n, lam_e):
            return 1 / (3 * lam_n + 5 * lam_e)

        self._test_multi_source_non_repairable(
            network_func=two_sources_shared_component,
            mttf_func=mttf_require_all,
            sources=["S1", "S2"],
            targets="T",
            min_connected=-1,
            network_name="Shared component (require_all=True, non-rep)"
        )

    def test_shared_component_require_all_repairable(self):
        """
        Test: Shared component, min_connected=-1 (repairable).

        Availability = A_n**3 * A_e**5
        """
        def availability_require_all():
            return self.A_n ** 3 * self.A_e ** 5

        self._test_multi_source_repairable(
            network_func=two_sources_shared_component,
            availability_func=availability_require_all,
            sources=["S1", "S2"],
            targets="T",
            min_connected=-1,
            network_name="Shared component (min_connected=-1, rep)"
        )

    def test_shared_component_require_all_vs_require_any(self):
        """
        Comparison test for shared component.

        min_connected=1 > min_connected=-1 (due to redundancy at A, B)
        """
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available")

        G = two_sources_shared_component(1 / self.lam_n, 1 / self.lam_e,
                                         1 / self.mu_n, 1 / self.mu_e)

        for method_name, method_kwargs in self.numba_only_configs:
            with self.subTest(method=method_name):
                res_any = estimate_mttf_mttr(
                    G, ["S1", "S2"], "T", N=500, depth=200,
                    min_connected=1, **method_kwargs
                )
                res_all = estimate_mttf_mttr(
                    G, ["S1", "S2"], "T", N=500, depth=200,
                    min_connected=-1, **method_kwargs
                )

                A_any = res_any['mttf'] / (res_any['mttf'] + res_any['mttr'])
                A_all = res_all['mttf'] / (res_all['mttf'] + res_all['mttr'])

                self.assertGreater(A_any, A_all)

    # ==========================================================================
    # Multiple Sources AND Multiple Targets (min_connected=-1)
    # ==========================================================================

    def test_two_sources_two_targets_require_all_non_repairable(self):
        """
        Test: 4 independent paths, min_connected=-1 (non-repairable).

        min_connected=-1: All 4 paths must work.

        """
        def mttf_require_all(lam_n, lam_e):
            return 1 / (4 * lam_n + 8 * lam_e)

        self._test_multi_source_non_repairable(
            network_func=two_sources_two_targets_independent,
            mttf_func=mttf_require_all,
            sources=["S1", "S1", "S2", "S2"],
            targets=["T1_a", "T2_a", "T1_b", "T2_b"],
            min_connected=-1,
            network_name="4 independent paths (min_connected=-1, non-rep)"
        )

    def test_two_sources_two_targets_require_all_repairable(self):
        """
        Test: 4 independent paths, min_connected=-1 (repairable).

        Availability = (A_n * A_e**2)**4 = A_n**4 * A_e**8
        """
        def availability_require_all():
            A_path = self.A_n * self.A_e ** 2
            return A_path ** 4

        self._test_multi_source_repairable(
            network_func=two_sources_two_targets_independent,
            availability_func=availability_require_all,
            sources=["S1", "S1", "S2", "S2"],
            targets=["T1_a", "T2_a", "T1_b", "T2_b"],
            min_connected=-1,
            network_name="4 independent paths (min_connected=-1, rep)"
        )

    # =============================================================================
    # Special case: Single source/target should work with both min_connected=-1, =1
    # =============================================================================

    def test_single_source_target_require_all_equivalence(self):
        """
        Test: With single source and target, min_connected=1 and min_connected=-1 should be equivalent.
        """
        G = N4_11(1 / self.lam_n, 1 / self.lam_e, 0, 0)

        for method_name, method_kwargs in self.method_configs:
            with self.subTest(method=method_name):
                res_true = estimate_mttf_mttr(
                    G, "S", "T", N=int(1e6),
                    min_connected=-1, **method_kwargs
                )
                res_false = estimate_mttf_mttr(
                    G, "S", "T", N=int(1e6),
                    min_connected=1, **method_kwargs
                )

                # Both should be (nearly) equal
                rel_diff = abs(res_true['mttf'] - res_false['mttf']) / res_true['mttf']
                self.assertLess(
                    rel_diff, self.TOL,
                    f"min_connected=1 and min_connected=-1 should be equivalent for single source/target"
                )


if __name__ == '__main__':
    unittest.main()