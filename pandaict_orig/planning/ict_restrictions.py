from anaplan import Restriction
import pandaict_orig.simulation as sim
import pandaict_orig.topology as ict_top
import networkx
import sys
# sys.path.append("/media/D/Workspace/Programmieren/scripts/ENSURE/Versuchsskripte")
# from failure_combinations_2019_08_08 import reliability_ps_ict
# import copy

import outage
# import outage.reliability_new


class ReliabilityWithICTRestriction(Restriction):
    def __init__(self, mh, initial_asidi, target_asidi=None, improve_percent=None, extended_line_information=None):
        Restriction.__init__(self, mh)
        self._name = "ReliabilityWithICTRestriction"
        self.mh = mh
        self.initial_asidi = initial_asidi
        self.extended_line_information = extended_line_information

        if target_asidi and improve_percent:
            raise UserWarning("'target_asidi' and 'improve_percent' are both specified."
                              " Please specify only one")
        elif not target_asidi and improve_percent is None:
            raise UserWarning("Please specify either 'target_asidi' or 'improve_percent'")

        self.improve_percent = improve_percent
        self.target_asidi = target_asidi if target_asidi else initial_asidi * (1 - improve_percent/100)

    def _fitness(self):
        violated = True

        self.extended_line_information = sim.update_extended_line_information_hazard_rates(self.extended_line_information, self.mh.net)
        res_load_rel, res_line_rel = sim.calculate_reliability(self.mh.net, self.mh.ict_net, self.extended_line_information)
        asidi = sim.calc_asidi(res_load_rel)

        asidi_delta = asidi - self.target_asidi
        if asidi_delta > 0:
            violation = asidi_delta
        else:
            violated = False
            violation = 0

        #        file = open("output/rel_comparison.csv", "a")
        #        file.write("%s;%s\n" % (asidi_exa, asidi_sim))
        #        file.write("%s;%s;%s;%s\n" % (asidi_exa, asidi_sim, self.target_asidi_exa, self.target_asidi_sim))
        #        file.close()
        return violated, violation

class ReliabilityWithICTRestriction2(Restriction):
    def __init__(self, mh, initial_asidi_load, initial_asidi_sgen, target_asidi_load=None, target_asidi_sgen=None, improve_percent=None):
        Restriction.__init__(self, mh)
        self._name = "ReliabilityWithICTRestriction"
        self.mh = mh
        self.initial_asidi_load = initial_asidi_load
        self.evaluations = 0

#        if target_asidi_load or target_a and improve_percent:
#            raise UserWarning("'target_asidi' and 'improve_percent' are both specified."
#                              " Please specify only one")
#        elif not target_asidi and improve_percent is None:
#            raise UserWarning("Please specify either 'target_asidi' or 'improve_percent'")

        self.improve_percent = improve_percent
        self.target_asidi_load = target_asidi_load if target_asidi_load else initial_asidi_load * (1 - improve_percent/100)
        self.target_asidi_sgen = target_asidi_sgen if target_asidi_sgen else initial_asidi_sgen * (1 - improve_percent/100)

    def _fitness(self):
        violated = True

        self.evaluations += 1

        asidi_load, asidi_sgen = reliability_ps_ict(self.mh.net, self.mh.ict_net)

        asidi_load_delta = asidi_load - self.target_asidi_load
        asidi_sgen_delta = asidi_sgen - self.target_asidi_sgen

        if asidi_load_delta > 0 or asidi_sgen_delta > 0:
            violation = asidi_load_delta + asidi_sgen_delta
        else:
            violated = False
            violation = 0

        #        file = open("output/rel_comparison.csv", "a")
        #        file.write("%s;%s\n" % (asidi_exa, asidi_sim))
        #        file.write("%s;%s;%s;%s\n" % (asidi_exa, asidi_sim, self.target_asidi_exa, self.target_asidi_sim))
        #        file.close()
        return violated, violation


class ReliabilityComparisonRestriction(Restriction):
    def __init__(self, mh, initial_asidi_load, target_asidi_load=None, improve_percent=None):
        Restriction.__init__(self, mh)
        self._name = "ReliabilityCompatibilityRestriction"
        self.mh = mh
        self.initial_asidi_load = initial_asidi_load
        self.evaluations = 0

#        if target_asidi_load or target_a and improve_percent:
#            raise UserWarning("'target_asidi' and 'improve_percent' are both specified."
#                              " Please specify only one")
#        elif not target_asidi and improve_percent is None:
#            raise UserWarning("Please specify either 'target_asidi' or 'improve_percent'")

        self.improve_percent = improve_percent
        self.target_asidi_load = target_asidi_load if target_asidi_load else initial_asidi_load * (1 - improve_percent/100)

    def _fitness(self):
        violated = True

        self.evaluations += 1

#        asidi_load, asidi_sgen = reliability_ps_ict(self.mh.net, self.mh.ict_net)
        net_e = copy.deepcopy(self.mh.net)
        net_s = copy.deepcopy(self.mh.net)
        net_se = copy.deepcopy(self.mh.net)

        asidi_load_exact = outage.reliability(net_e)
        asidi_simplified = outage.reliability_simplified(net_s)
#         asidi_simp_exact = outage.reliability_new.reliability_new(net_se)

        asidi_load_delta = asidi_load_exact - self.target_asidi_load
#        asidi_load_delta = asidi_simp_exact - self.target_asidi_load

        if asidi_load_delta > 0:
            violation = asidi_load_delta
        else:
            violated = False
            violation = 0

        file = open("rel_comparison.csv", "a")
        file.write("%s;%s;%s\n" % (asidi_load_exact, asidi_simplified, asidi_simp_exact))
#        file.write("%s;%s;%s;%s\n" % (asidi_exa, asidi_sim, self.target_asidi_exa, self.target_asidi_sim))
        file.close()
        return violated, violation


class ICTConnectionRestriction(Restriction):
    def __init__(self, mh, relevant_measures=None):
        Restriction.__init__(self, mh=mh, relevant_measures=relevant_measures)
        self._name = "ICTConnectionRestriction"

    def _fitness(self):
        mh = self.mh
        mg = ict_top.create_ict_graph(mh.ict_net)
        connected_nodes = list(networkx.connected_components(mg))

        is_servers = mh.ict_net.server[mh.ict_net.server.in_service]
        is_clients = mh.ict_net.client[mh.ict_net.client.in_service]

        connected_clients = set()
        for server in is_servers.index:
            server_node = is_servers.node.loc[server]
            clients = is_clients[is_clients.server == server]
            for cn in connected_nodes:
                if server_node in cn:
                    connected_clients.update(clients.index[clients.node.isin(cn)])
        unconnected_clients = set(is_clients.index) - connected_clients
        return len(unconnected_clients) > 0, len(unconnected_clients)
