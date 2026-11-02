'''
Created on 03.08.2026
@author: fnuetz
'''

import unittest
import numpy as np
import matplotlib
matplotlib.use('Agg')

from reliability_tests.test_networks_pi import (
    build_test_ict_network,
    build_series_network_with_rates,
    build_parallel_network_with_rates,
)
from reliability_tests.reference import (
    reference_values,
    reference_criticality_series,
    reference_criticality_parallel_1oo2
)

from pandaict.reliability.monte_carlo import NUMBA_AVAILABLE   
from pandaict.reliability.reliability import (
    estimate_mtbf_mttr_for_conn,
    empirical_reliability_function,
    analyze_critical_components_for_conn
)


class ReliabilityTest(unittest.TestCase):
    """Compare MC results against analytical reference values."""

    @classmethod
    def setUpClass(cls):
        # relative tolerance for stochastic approximation (2%)
        cls.TOL = 2e-2

        # reliability parameters (only nodes fail)
        cls.mttf_h = 1000.0
        cls.mttr_h = 100.0

        # numba config
        cls.method_config           = {"use_numba": True, "parallel": True}
        cls.method_config_serial    = {"use_numba": True, "parallel": False}

        # case matrix: (n paths, m nodes per path, min_connected, label)
        cls.cases = [
            (1, 1, -1, 'single'),
            (1, 5, -1, 'serial5'),
            (3, 1, 1, 'parallel3_any1'),    # 1oo3
            (3, 1, 2, '2oo3')               # 2oo3
        ]

        # sample counts
        cls.N_nonrep    = int(1e7)
        cls.N_rep       = int(1e4)
        cls.depth       = 200
        cls.N_rel       = cls.N_nonrep

    def _require_numba(self):
        """Skip test if Numba is not available."""
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available")

    def _rel_err(self, mc, ref, quantity, label):
        """Assert relative error of mc vs ref is below TOL."""
        rel = abs(mc - ref) / ref
        self.assertLess(rel, self.TOL,
            f"{label}: {quantity}_MC={mc:.4f} vs analytical={ref:.4f} (err={rel:.2%})")

    # ==========================================================================
    # MTBF / MTTR Tests
    # ==========================================================================
    def test_mtbf_mttr(self):
        """Monte-Carlo MTBF/MTTR against analytical reference for all cases."""
        self._require_numba()

        for n, m, mc, label in self.cases:
            for repairable in (False, True):
                with self.subTest(case=label, repairable=repairable):
                    mttr_h = self.mttr_h if repairable else 0.0
                    net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)
                    ref = reference_values(n, m, self.mttf_h, mttr_h, min_connected=mc)

                    if repairable:
                        res = estimate_mtbf_mttr_for_conn(
                            net, conns, N=self.N_rep, depth=self.depth,
                            min_connected=mc, **self.method_config)

                        A_mc = res['mttf_h'] / (res['mttf_h'] + res['mttr_h'])
                        self._rel_err(A_mc, ref['availability'], "A", label)
                        self._rel_err(res['mtbf_h'], ref['mtbf_h'], "MTBF", label)
                    else:
                        res = estimate_mtbf_mttr_for_conn(
                            net, conns, N=self.N_nonrep, depth=1,
                            min_connected=mc, **self.method_config)

                        self.assertIsNotNone(res['mttf_h'], f"{label}: MTTF is None")
                        self.assertTrue(np.isinf(res['mttr_h']),
                            f"{label}: expected MTTR=inf for non-repairable, got {res['mttr_h']}")
                        self._rel_err(res['mttf_h'], ref['mttf_h'], "MTTF", label)   

    # ==========================================================================
    # Serial (non-parallel) Execution Tests
    # ==========================================================================
    def test_mtbf_mttr_serial_execution(self):
        """Cover the serial (non-parallel) numba path; single-component only."""
        self._require_numba()

        n, m, mc, label = 1, 1, -1, 'single'
        for repairable in (False, True):
            with self.subTest(repairable=repairable):
                mttr_h = self.mttr_h if repairable else 0.0
                net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)
                ref = reference_values(n, m, self.mttf_h, mttr_h, min_connected=mc)

                if repairable:
                    res = estimate_mtbf_mttr_for_conn(
                        net, conns, N=self.N_rep, depth=self.depth,
                        min_connected=mc, **self.method_config_serial)

                    A_mc = res['mttf_h'] / (res['mttf_h'] + res['mttr_h'])
                    self._rel_err(A_mc, ref['availability'], "A(serial)", label)
                    self._rel_err(res['mtbf_h'], ref['mtbf_h'], "MTBF(serial)", label)
                else:
                    res = estimate_mtbf_mttr_for_conn(
                        net, conns, N=self.N_nonrep,
                        min_connected=mc, **self.method_config_serial)

                    self.assertIsNotNone(res['mttf_h'], f"{label}: MTTF is None")
                    self.assertTrue(np.isinf(res['mttr_h']),
                        f"{label}: expected MTTR=inf for non-repairable, got {res['mttr_h']}")
                    self._rel_err(res['mttf_h'], ref['mttf_h'], "MTTF(serial)", label)

    # ==========================================================================
    # Empirical Reliability Function Tests (non-repairable only)
    # ==========================================================================
    def test_empirical_reliability(self):
        """Monte-Carlo R(T) against analytical reference (non-repairable)."""
        self._require_numba()

        for n, m, mc, label in self.cases:
            with self.subTest(case=label):
                net, conns = build_test_ict_network(n, m, self.mttf_h, 0.0)
                ref = reference_values(n, m, self.mttf_h, 0.0, min_connected=mc)
                mttf = ref['mttf_h']

                # evaluate at 0, 0.5, 1, 2, 4 times the analytical MTTF
                T = mttf * np.array([0.0, 0.5, 1.0, 2.0, 4.0])
                ref_R = reference_values(n, m, self.mttf_h, 0.0,
                                         min_connected=mc, T=T)['reliability']

                R = empirical_reliability_function(
                    net, conns, T=T, N=self.N_rel, min_connected=mc, **self.method_config)

                self.assertIsInstance(R, np.ndarray)
                self.assertEqual(len(R), len(T))

                for t, r_mc, r_ref in zip(T, R, ref_R):
                    self._rel_err(r_mc, r_ref, f"R({t:.1f})", label)

    # ==========================================================================
    # Critical Component Analysis Tests
    # ==========================================================================
    def _path_node_crit(self, res, key='node_criticality'):
        """Return {name: criticality} for path nodes only (exclude devices)."""
        crit = res[key]
        if crit is None:
            self.fail(f"criticality '{key}' is None (no critical data collected)")
        elements = res['node_elements']
        names = res['node_names']
        return {names[i]: float(crit[i])
                for i in range(len(names))
                if elements[i][0] == 'node'}

    def test_criticality_symmetric(self):
        """T1: identical rates => every path-node criticality == 1.0."""
        self._require_numba()

        for n, m, mc, label in self.cases:
            for repairable in (False, True):
                with self.subTest(case=label, repairable=repairable):
                    mttr_h = self.mttr_h if repairable else 0.0
                    net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)

                    if repairable:
                        N, depth = self.N_rep, self.depth
                    else:
                        N, depth = self.N_nonrep, 1

                    res = analyze_critical_components_for_conn(
                        net, conns, N=N, depth=depth, min_connected=mc,
                        plot=False, verbose=False, **self.method_config)

                    # --- failure criticality (rate_adjustment=True default) ---
                    node_crit = self._path_node_crit(res, 'node_criticality')
                    self.assertTrue(node_crit, f"{label}: no path nodes tracked")
                    K = len(node_crit)
                    for name, c in node_crit.items():
                        self._rel_err(c, 1.0, f"nodeCrit[{name}]", label)
                    # symmetric + RA=True => sum of scores == K
                    self._rel_err(sum(node_crit.values()), float(K),
                                  "sumNodeCrit", label)

                    # edges are ideal => criticality exactly 0
                    self.assertTrue(np.all(res['edge_criticality'] == 0.0),
                        f"{label}: expected edge crit 0, got {res['edge_criticality']}")

                    # --- repair criticality (repairable only) ---
                    if repairable:
                        node_rep = self._path_node_crit(res, 'node_repair_criticality')
                        for name, c in node_rep.items():
                            self._rel_err(c, 1.0, f"nodeRepCrit[{name}]", label)
                        self.assertTrue(np.all(res['edge_repair_criticality'] == 0.0),
                            f"{label}: expected edge rep crit 0, "
                            f"got {res['edge_repair_criticality']}")

    def test_criticality_series_rates(self):
        """T2: 2-node series, rates 1:10 => BP_i = lam_i/sum(lam)."""
        self._require_numba()

        mttf_list = [1000.0, 100.0]   # lam1 : lam2 = 1 : 10
        net, conns, node_names = build_series_network_with_rates(mttf_list, mttr_h=0.0)

        for ra in (True, False):
            with self.subTest(rate_adjustment=ra):
                ref = reference_criticality_series(mttf_list, ra)

                res = analyze_critical_components_for_conn(
                    net, conns, N=self.N_nonrep, depth=1, min_connected=-1,
                    plot=False, verbose=False, rate_adjustment=ra,
                    **self.method_config)

                crit_by_name = self._path_node_crit(res, 'node_criticality')
                for name, r_ref in zip(node_names, ref):
                    self._rel_err(crit_by_name[name], r_ref,
                                  f"seriesCrit[{name}]", f"series_RA={ra}")

                self.assertTrue(np.all(res['edge_criticality'] == 0.0),
                    f"series_RA={ra}: expected edge crit 0, "
                    f"got {res['edge_criticality']}")

    def test_criticality_parallel_rates(self):
        """T3: 1oo2 parallel, rates 1:10 => BP_i = lam_j/(lam_i+lam_j)."""
        self._require_numba()

        mttf_list = [1000.0, 100.0]   # lam1 : lam2 = 1 : 10
        net, conns, node_names = build_parallel_network_with_rates(mttf_list, mttr_h=0.0)

        for ra in (True, False): # repairable
            with self.subTest(rate_adjustment=ra):
                ref = reference_criticality_parallel_1oo2(mttf_list, ra)

                res = analyze_critical_components_for_conn(
                    net, conns, N=self.N_nonrep, depth=1, min_connected=1,
                    plot=False, verbose=False, rate_adjustment=ra,
                    **self.method_config)

                crit_by_name = self._path_node_crit(res, 'node_criticality')
                for name, r_ref in zip(node_names, ref):
                    self._rel_err(crit_by_name[name], r_ref,
                                  f"parCrit[{name}]", f"parallel_RA={ra}")

                # Assert link criticality == 0
                self.assertTrue(np.all(res['edge_criticality'] == 0.0),
                    f"parallel_RA={ra}: expected edge crit 0, "
                    f"got {res['edge_criticality']}")



if __name__ == '__main__':
    unittest.main()