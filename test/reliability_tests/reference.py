'''
Created on 28.07.2026
@author: fnuetz

Ground truth for testsuite: Analytical reference formula
'''

import math
import numpy as np


def reference_values(n, m, mttf_h, mttr_h, min_connected=-1, t=None):
    """
    Calculate analytical reference values for test cases build from build_test_network(n, m, ...).
    
    Topology: n independent paths of m nodes each.
    System UP if >= k paths are connected (k=min_connected).

    :INPUT:
        n, m, mttf_h, mttr_h    - identical to build_test_network
        min_connected           - int, k-out-of-n requirement
        t                       - float / array, optional for R(t) (only non-repairable)

    :OUTPUT:
        dict of mttf_h, mttr_h, mtbf_h, availability A and reliability R (if t not None)
    """
    if min_connected > n:
        print('ERROR: min_connected > n')
        return 1

    # get k from min_connected
    if min_connected == -1:
        k = n
    else:
        k = min_connected

    lam = 0.0 if mttf_h == 0 else 1.0 / mttf_h  # get failure rate
    lam_path = m * lam                          # using R(t) = R1 * ... * Rm

    repairable = (mttr_h != 0)

    # === non-repairable (mu=0) ===
    if not repairable:
        
        mttf = sum(1.0 / i for i in range(k, n + 1)) / lam_path

        # prepare output dict
        out = {'mttf_h': mttf, 'mttr_h': np.inf,
               'mtbf_h': mttf, 'availability': 0.0}

        if t is not None:
            tt = np.asarray(t, dtype=float)
            p = np.exp(-lam_path * tt)
            R = sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

            out['reliability'] = float(R) if np.ndim(t)==0 else R

        return out

    # === repairable ===
    mu = 1.0 / mttr_h
    a_comp = mu / (lam + mu)    # availability per component
    a_path = a_comp ** m
    u_path = 1.0 - a_path

    # System-Availability: P(# UP paths >= k)
    a_sys = sum(math.comb(n,j) * u_path**j * a_path**(n-j) for j in range(0, n - k + 1))

    # expected frequency of system-level failure
    nu = math.comb(n,k) * a_path**k * u_path**(n - k) * k * lam_path

    return {
        'mttf_h': a_sys / nu,
        'mttr_h': (1-a_sys) / nu,
        'mtbf_h': 1.0 / nu,
        'availability': a_sys
    }

def reference_criticality_series(mttf_list, rate_adjustment):
    """
    Exact Barlow-Proschan criticality for a pure series of K independent
    non-repairable components with per-component MTTF.

    For a series system the system fails at the first component failure, so
    component i is the "last straw" with probability

        BP_i = lam_i / sum(lam)        (competing exponentials).

    :INPUT:
        mttf_list       - list of K MTTF values [h] (K >= 1)
        rate_adjustment - bool, score mode (see module docstring)

    :OUTPUT:
        list of K criticality scores, same order as mttf_list.
    """
    lam = np.array([0.0 if t == 0 else 1.0 / t for t in mttf_list], dtype=float)
    total = lam.sum()
    if total == 0:
        return [0.0] * len(mttf_list)

    bp = lam / total                      # BP_i
    if rate_adjustment:
        # (lam_i / total) / (lam_i / total) = 1.0 for every component
        return [1.0] * len(mttf_list)
    # raw mode: score_i = BP_i * K  (sum = K)
    K = len(mttf_list)
    return (bp * K).tolist()

def reference_criticality_parallel_1oo2(mttf_list, rate_adjustment):
    """
    Exact Barlow-Proschan criticality for a 1-out-of-2 parallel system of two
    independent non-repairable components with per-component MTTF.

    For a 1ooN parallel system the system fails when ALL components have
    failed, so the "last straw" is the *last* component to fail.  For N=2 with
    failure rates lam1, lam2:

        BP_1 = lam2 / (lam1 + lam2)   (component 1 is last to fail iff 2 fails
                                       before 1, i.e. component 2 was the first)
        BP_2 = lam1 / (lam1 + lam2)

    The slower component is more likely to be the last to fail, hence the
    cross-rate dependence.  This contrasts with the series case (first to
    fail) and is the key topology-distinguishing test.

    :INPUT:
        mttf_list       - list of exactly 2 MTTF values [h]
        rate_adjustment - bool, score mode

    :OUTPUT:
        list of 2 criticality scores [score_1, score_2], same order as input.
    """
    if len(mttf_list) != 2:
        raise ValueError("reference_criticality_parallel_1oo2 needs exactly 2 components")

    lam = np.array([0.0 if t == 0 else 1.0 / t for t in mttf_list], dtype=float)
    total = lam.sum()
    if total == 0:
        return [0.0, 0.0]

    bp = np.array([lam[1], lam[0]]) / total

    if rate_adjustment:
        # score_i = BP_i / (lam_i / total) = BP_i * total / lam_i
        #         = lam_j / lam_i   (cross-rate ratio)
        return (bp * total / lam).tolist()
    # raw mode: score_i = BP_i * K, K = 2
    return (bp * 2).tolist()