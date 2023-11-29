from pandaplan.core.outage.resupply import resupplier
from pandaplan.core.outage.toolbox import find_protection_areas
import pandas as pd
from pandaplan.core import pplog
import pandaict as pi
import numpy as np
logger = pplog.getLogger(__name__)


def get_extended_protection_infos(net, lines=None, substation_buses=None):
    if lines is None:
        lines = net.line.index  # if no lines are given, calculate reliability for all lines
    prot = find_protection_areas(net)
    nr_areas = len(prot)
    logger.debug("found %u protection areas" % nr_areas)
    rs = resupplier(net, substation_buses=substation_buses)
    orig_open = set(net.switch[net.switch.closed == 0].index)

    extended_line_information = dict()
    weighted_hazard_rates = pi.pandas_to_dict(net.line.index,
                                              net.line.h_per_km.values * net.line.length_km.values)

    for area_nr, (area, buses, iso) in enumerate(prot):
        if len(set(area) & set(lines)) == 0:
            logger.debug("protection area %u / %u: No lines to analyze" %
                         (area_nr + 1, nr_areas))
            continue
        logger.debug("analyzing protection area %u / %u" %
                     (area_nr + 1, nr_areas))
        rs.reset()
        rs.isolation_switches = set(iso)
        rs.ln = area
        rs.resupply_isolated_areas(consider_ats=True)

        for l in area:
            if not l in lines:
                continue
#            h = net.line.at[l, "h_per_km"] * net.line.at[l, "length_km"]
            h = weighted_hazard_rates[l]

            info = {
                    "h": h,
                    "protection_switches": rs.ls,
                    "isolation_switches": iso - orig_open,
                    "resupply_switches": rs.os | (rs.ls - iso),
                    "isolated_loads": rs.piso,
                    "protected_loads": rs.ppr,
                    "resupplied_loads": rs.pre
                    }
            extended_line_information[l] = info

    rs.reset()
    return extended_line_information


def update_extended_line_information_hazard_rates(extended_line_information, net):
    weighted_hazard_rates = net.line.h_per_km * net.line.length_km
    for i, h in weighted_hazard_rates.iteritems():
        extended_line_information[i]["h"] = h
    return extended_line_information


def calc_asidi(res_load_rel):
    out_kwh_expect_sum = 0
    p_kw_sum = 0
    for data in res_load_rel.values():
        if data["out_kwh_expect"] > 0:
            out_kwh_expect_sum += data["out_kwh_expect"]
            p_kw_sum += data["p_kw"]
    return out_kwh_expect_sum / p_kw_sum * 60


def set_switch_times_for_ict_clients(net, ict_net):
    for client in ict_net.client.index[ict_net.client.et == "switch"]:
        switch = ict_net.client.element.loc[client]
        if ict_net.client.in_service.loc[client]:
            net.switch.time_min.loc[switch] = 0
        else:
            net.switch.time_min.loc[switch] = net.switch.time_manual_min.loc[switch]
