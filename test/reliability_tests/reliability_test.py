'''
Created on 03.08.2026
@author: fnuetz
'''


import tempfile
import os
from PIL import Image, ImageChops
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
    analyze_critical_components_for_conn,
    plot_graph
)


class ReliabilityTest:
    """Compare MC results against analytical reference values."""

    @classmethod
    def set_up_class(cls):
        # relative tolerance for stochastic approximation (2%)
        print("Init...")
        cls.TOL = 10e-2

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
        cls.n_nonrep    = int(1e6) #7
        cls.n_rep       = int(1e4) #4
        cls.depth       = 200
        cls.n_rel       = cls.n_nonrep
        
        cls.test_verbose_plot_repair = True
        cls.test_verbose_plot_norepair = True

    def set_test_python_fallback(self, pfb):
        if pfb:
            self.method_config.update({'use_numba': False})
            self.n_nonrep    = int(1e3)
            self.n_rep       = int(1e3)
        else:
            self.method_config.update({'use_numba': True})
            self.n_nonrep    = int(1e6)
            self.n_rep       = int(1e4)
    
    def _require_numba(self):
        """Skip test if Numba is not available."""
        if not NUMBA_AVAILABLE:
            self.skipTest("Numba not available")

    def _rel_err(self, utest, mc, ref, quantity, label):
        """Assert relative error of mc vs ref is below TOL."""
        rel = abs(mc - ref) / ref
        if self.method_config['use_numba']:
            utest.assertLess(rel, self.TOL,
            f"{label}: {quantity}_MC={mc:.4f} vs analytical={ref:.4f} (err={rel:.2%})")
        else:
            return # Don't test for accuracy in case of python fallback for now

    # ==========================================================================
    # MTBF / MTTR Tests
    # ==========================================================================
    def test_mtbf_mttr(self, utest):
        """Monte-Carlo MTBF/MTTR against analytical reference for all cases."""        
        self._require_numba()        
        for n, m, mc, label in self.cases:
            for repairable in (False, True):
                with utest.subTest(case=label, repairable=repairable):
                    mttr_h = self.mttr_h if repairable else 0.0
                    net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)
                    ref = reference_values(n, m, self.mttf_h, mttr_h, min_connected=mc)

                    if repairable:
                        res = estimate_mtbf_mttr_for_conn(
                            net, conns, n=self.n_rep, depth=self.depth,
                            min_connected=mc, **self.method_config)

                        a_mc = res['mttf_h'] / (res['mttf_h'] + res['mttr_h'])
                        self._rel_err(utest, a_mc, ref['availability'], "A", label)
                        self._rel_err(utest, res['mtbf_h'], ref['mtbf_h'], "MTBF", label)
                    else:
                        res = estimate_mtbf_mttr_for_conn(
                            net, conns, n=self.n_nonrep, depth=1,
                            min_connected=mc, **self.method_config)

                        utest.assertIsNotNone(res['mttf_h'], f"{label}: MTTF is None")
                        utest.assertTrue(np.isinf(res['mttr_h']),
                            f"{label}: expected MTTR=inf for non-repairable, got {res['mttr_h']}")
                        self._rel_err(utest, res['mttf_h'], ref['mttf_h'], "MTTF", label)   

    # ==========================================================================
    # Serial (non-parallel) Execution Tests
    # ==========================================================================
    def test_mtbf_mttr_serial_execution(self, utest):
        """Cover the serial (non-parallel) numba path; single-component only."""
        self._require_numba()
        
        n, m, mc, label = 1, 1, -1, 'single'
        for repairable in (False, True):
            with utest.subTest(repairable=repairable):
                mttr_h = self.mttr_h if repairable else 0.0
                net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)
                ref = reference_values(n, m, self.mttf_h, mttr_h, min_connected=mc)

                if repairable:
                    res = estimate_mtbf_mttr_for_conn(
                        net, conns, n=self.n_rep, depth=self.depth,
                        min_connected=mc, **self.method_config_serial)

                    a_mc = res['mttf_h'] / (res['mttf_h'] + res['mttr_h'])
                    self._rel_err(utest, a_mc, ref['availability'], "A(serial)", label)
                    self._rel_err(utest, res['mtbf_h'], ref['mtbf_h'], "MTBF(serial)", label)
                else:
                    res = estimate_mtbf_mttr_for_conn(
                        net, conns, n=self.n_nonrep,
                        min_connected=mc, **self.method_config_serial)

                    utest.assertIsNotNone(res['mttf_h'], f"{label}: MTTF is None")
                    utest.assertTrue(np.isinf(res['mttr_h']),
                        f"{label}: expected MTTR=inf for non-repairable, got {res['mttr_h']}")
                    self._rel_err(utest, res['mttf_h'], ref['mttf_h'], "MTTF(serial)", label)

    # ==========================================================================
    # Empirical Reliability Function Tests (non-repairable only)
    # ==========================================================================
    def test_empirical_reliability(self, utest):
        """Monte-Carlo R(T) against analytical reference (non-repairable)."""
        self._require_numba()

        for n, m, mc, label in self.cases:
            with utest.subTest(case=label):
                net, conns = build_test_ict_network(n, m, self.mttf_h, 0.0)
                ref = reference_values(n, m, self.mttf_h, 0.0, min_connected=mc)
                mttf = ref['mttf_h']

                # evaluate at 0, 0.5, 1, 2, 4 times the analytical MTTF
                T = mttf * np.array([0.0, 0.5, 1.0, 2.0, 4.0])
                ref_r = reference_values(n, m, self.mttf_h, 0.0,
                                         min_connected=mc, t=T)['reliability']

                R = empirical_reliability_function(
                    net, conns, t=T, n=self.n_rel, min_connected=mc, **self.method_config)

                utest.assertIsInstance(R, np.ndarray)
                utest.assertEqual(len(R), len(T))

                for t, r_mc, r_ref in zip(T, R, ref_r):
                    self._rel_err(utest, r_mc, r_ref, f"R({t:.1f})", label)

    # ==========================================================================
    # Critical Component Analysis Tests
    # ==========================================================================
    def _path_node_crit(self, utest, res, key='node_criticality'):
        """Return {name: criticality} for path nodes only (exclude devices)."""
        crit = res[key]
        if crit is None:
            utest.fail(f"criticality '{key}' is None (no critical data collected)")
        elements = res['node_elements']
        names = res['node_names']
        return {names[i]: float(crit[i])
                for i in range(len(names))
                if elements[i][0] == 'node'}
        
    def _do_plot_test(self, utest, net, test_idx, res=None):        
        if res:
            plt = plot_graph(net, edge_criticality=res['edge_criticality'], node_criticality=res['node_criticality'], show=False)                                                         
        else:
            plt = plot_graph(net, show=False)
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:    
            plt.savefig(tmp_file.name)
             
            image1 = Image.open(tmp_file.name)
            # load the saved figure to compare
            image2 = Image.open(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'plt_nxg' + str(test_idx) + '.png')                         
            # compare the size
            assert image1.size == image2.size 
            # compare the content
            diff = ImageChops.difference(image1, image2)
            utest.assertTrue(diff.getbbox() is None)

    def _do_test_criticality_symmetric(self, utest, label, repairable, n, m, mc):
        with utest.subTest(case=label, repairable=repairable):
            mttr_h = self.mttr_h if repairable else 0.0
            net, conns = build_test_ict_network(n, m, self.mttf_h, mttr_h)

            if repairable:
                N, depth = self.n_rep, self.depth
            else:
                N, depth = self.n_nonrep, 1
            
            vpflag = self.test_verbose_plot_repair or self.test_verbose_plot_norepair
            res = analyze_critical_components_for_conn(
                net, conns, n=N, depth=depth, min_connected=mc,
                plot=vpflag, verbose=vpflag, **self.method_config)
            # test verbose one time only for each repairable and non-repairable
            if repairable: 
                self.test_verbose_plot_repair = False 
            else:
                self.test_verbose_plot_norepair = False 
            
            # --- failure criticality (rate_adjustment=True default) ---
            node_crit = self._path_node_crit(utest, res, 'node_criticality')
            utest.assertTrue(node_crit, f"{label}: no path nodes tracked")
            K = len(node_crit)
            for name, c in node_crit.items():
                self._rel_err(utest, c, 1.0, f"nodeCrit[{name}]", label)
            # symmetric + RA=True => sum of scores == K
            self._rel_err(utest, sum(node_crit.values()), float(K),
                          "sumNodeCrit", label)

            # edges are ideal => criticality exactly 0
            utest.assertTrue(np.allclose(res['edge_criticality'], 0.0),
                f"{label}: expected edge crit 0, got {res['edge_criticality']}")

            # --- repair criticality (repairable only) ---
            if repairable:
                node_rep = self._path_node_crit(utest, res, 'node_repair_criticality')
                for name, c in node_rep.items():
                    self._rel_err(utest, c, 1.0, f"nodeRepCrit[{name}]", label)
                    
                utest.assertTrue(np.allclose(res['edge_repair_criticality'], 0.0),
                    f"{label}: expected edge rep crit 0, "
                    f"got {res['edge_repair_criticality']}")
        if label=="serial5" and repairable:             
            self._do_plot_test(utest, net, 2, res=res)
    
    def test_criticality_symmetric(self, utest):
        """T1: identical rates => every path-node criticality == 1.0."""
        self._require_numba()

        for n, m, mc, label in self.cases:
            for repairable in (False, True):
                self._do_test_criticality_symmetric(utest, label, repairable, n, m, mc)

    def test_criticality_series_rates(self, utest):
        """T2: 2-node series, rates 1:10 => BP_i = lam_i/sum(lam)."""
        self._require_numba()

        mttf_list = [1000.0, 100.0]   # lam1 : lam2 = 1 : 10
        net, conns, node_names = build_series_network_with_rates(mttf_list, mttr_h=0.0)                
        for ra in (True, False):
            with utest.subTest(rate_adjustment=ra):
                ref = reference_criticality_series(mttf_list, ra)

                res = analyze_critical_components_for_conn(
                    net, conns, n=self.n_nonrep, depth=1, min_connected=-1,
                    plot=False, verbose=False, rate_adjustment=ra,
                    **self.method_config)

                crit_by_name = self._path_node_crit(utest, res, 'node_criticality')
                for name, r_ref in zip(node_names, ref):
                    self._rel_err(utest, crit_by_name[name], r_ref,
                                  f"seriesCrit[{name}]", f"series_RA={ra}")

                utest.assertTrue(np.allclose(res['edge_criticality'], 0.0),
                    f"series_RA={ra}: expected edge crit 0, "
                    f"got {res['edge_criticality']}")

    def test_criticality_parallel_rates(self, utest):
        """T3: 1oo2 parallel, rates 1:10 => BP_i = lam_j/(lam_i+lam_j)."""
        self._require_numba()
        mttf_list = [1000.0, 100.0]   # lam1 : lam2 = 1 : 10
        net, conns, node_names = build_parallel_network_with_rates(mttf_list, mttr_h=0.0)
        self._do_plot_test(utest, net, 1)
        for ra in (True, False): # repairable
            with utest.subTest(rate_adjustment=ra):
                ref = reference_criticality_parallel_1oo2(mttf_list, ra)

                res = analyze_critical_components_for_conn(
                    net, conns, n=self.n_nonrep, depth=1, min_connected=1,
                    plot=False, verbose=False, rate_adjustment=ra,
                    **self.method_config)

                crit_by_name = self._path_node_crit(utest, res, 'node_criticality')
                for name, r_ref in zip(node_names, ref):
                    self._rel_err(utest, crit_by_name[name], r_ref,
                                  f"parCrit[{name}]", f"parallel_RA={ra}")

                # Assert link criticality == 0
                utest.assertTrue(np.allclose(res['edge_criticality'], 0.0),
                    f"parallel_RA={ra}: expected edge crit 0, "
                    f"got {res['edge_criticality']}")
        