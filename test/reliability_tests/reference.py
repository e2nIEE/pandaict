'''
Created on 28.07.2026
@author: fnuetz

Ground truth for testsuite: Analytical reference formula
'''

import math
import numpy as np


def reference_values(n, m, mttf_h, mttr_h, min_connected=-1, T=None):
    """
    Calculate analytical reference values for test cases build from build_test_network(n, m, ...).
    
    Topology: n independent paths of m nodes each.
    System UP if >= k paths are connected (k=min_connected).

    :INPUT:
        n, m, mttf_h, mttr_h    - identical to build_test_network
        min_connected           - int, k-out-of-n requirement
        T                       - float / array, optional for R(T) (only non-repairable)

    :OUTPUT:
        dict of mttf_h, mttr_h, mtbf_h, availability A and reliability R (if T not None)
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
    lam_path = m * lam                          # R(T) = R1 * ... * Rm

    repairable = (mttr_h != 0)

    # === non-repairable (mu=0) ===
    if not repairable:
        
        mttf = sum(1.0 / i for i in range(k, n + 1)) / lam_path

        # prepare output dict
        out = {'mttf_h': mttf, 'mttr_h': np.inf,
               'mtbf_h': mttf, 'availability': 0.0}

        if T is not None:
            tt = np.asarray(T, dtype=float)
            p = np.exp(-lam_path * tt)
            R = sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))

            out['reliability'] = float(R) if np.ndim(T)==0 else R

        return out

    # === repairable ===
    mu = 1.0 / mttr_h
    A_comp = mu / (lam + mu)    # availability per component
    A_path = A_comp ** m
    U_path = 1.0 - A_path

    # System-Availability: P(# UP paths >= k)
    A_sys = sum(math.comb(n,j) * U_path**j * A_path**(n-j) for j in range(0, n - k + 1))

    # expected frequency of system-level failure
    nu = math.comb(n,k) * A_path**k * U_path**(n - k) * k * lam_path

    return {
        'mttf_h': A_sys / nu,
        'mttr_h': (1-A_sys) / nu,
        'mtbf_h': 1.0 / nu,
        'availability': A_sys
    }