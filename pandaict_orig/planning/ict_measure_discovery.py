from pandaict_orig.planning.ict_measures import REPLMeasureWithHazardRate
from pandaict_orig.planning.ict_measures import SwitchAutomationMeasure
from pandaict_orig.planning.ict_measures import ICTLinkMeasure
from pandaict_orig.planning.ict_measures import ICTAntennaMeasure
from anaplan import GroupMeasure

# logging
import pplog
logger = pplog.getLogger(__name__)

def create_repl_measures_with_hazard_rate(mh, lines=None, repl_std_type=None, h_per_km=0.03,
                                          cost_per_km=1, cost_dynamic=None,
                                          measure_type=REPLMeasureWithHazardRate):
    created_measures = set()
    lines = lines if lines is not None else mh.net.line.index
    for line in lines:
        if mh.net.line.h_per_km.loc[line] <= h_per_km:
            continue
        m = create_repl_measure_with_hazard_rate(mh, line, repl_std_type, h_per_km, cost_per_km,
                                                 cost_dynamic)
        if m:
            created_measures |= {m}
    logger.info("created %u REPL measures with hazard rate" % len(created_measures))
    return created_measures

def create_repl_measure_with_hazard_rate(mh, line, repl_std_type, h_per_km, cost_per_km,
                                         cost_dynamic, measure_type=REPLMeasureWithHazardRate):
    if not repl_std_type:
        repl_std_type = mh.net.line.std_type.loc[line]
    m = measure_type(mh.net, line, repl_std_type, h_per_km=h_per_km,
                     cost_per_km=cost_per_km, cost_dynamic=cost_dynamic)
    mh.add_measure(m)
    return m.name

def create_automated_switch_measures(mh, switches=None, cost=1,
                                     measure_type=SwitchAutomationMeasure):
    net = mh.net
    ict_net = mh.ict_net

    if switches is not None:
        switch_clients = ict_net.client.index[(ict_net.client.et=="switch") &
                        (ict_net.client.element.isin(switches))]
    else:
        switch_clients = ict_net.client.index[ict_net.client.et=="switch"]
    created_measures = set()
    for cl in switch_clients:
        m = create_automated_switch_measure(mh, cl, 0, cost)
        if m:
            mh.add_measure(m)
            created_measures |= {m}

    logger.info("created %u automated switch measures" % len(created_measures))
    return created_measures


def create_automated_switch_group_measures(mh, switches=None, automated_switch_time=0, cost=1,
                                           measure_type=SwitchAutomationMeasure):
    net = mh.net
    ict_net = mh.ict_net
    if switches is None:
        switches = net.switch.index
    switch_clients = ict_net.client[(ict_net.client.et=="switch") & ict_net.client.element.isin(switches)]
    nodes_with_clients = set(switch_clients.node)
    for nwc in nodes_with_clients:
        grouped_clients = list(switch_clients.index[switch_clients.node==nwc])
        measures = []
        for cl in grouped_clients:
            m = create_automated_switch_measure(mh, cl, automated_switch_time, cost)
            measures.append(m)
        group_measure = GroupMeasure(measures,
                name="GroupMeasure_ict_clients_at_node_" + str(nwc))
        mh.add_measure(group_measure)


def create_automated_switch_measure(mh, client, automated_switch_time, cost,
                                    measure_type=SwitchAutomationMeasure):
    m = measure_type(mh.net, mh.ict_net, client, automated_switch_time, cost=cost)
#    mh.add_measure(m)
    return m


def create_ict_link_measures(mh, links=None, cost_per_km_wired=1, cost_wireless=1,
                             measure_type=ICTLinkMeasure):
    ict_net = mh.ict_net
    if links is None:
        links = ict_net.link.index

    created_measures = set()
    for link in links:
        m = create_ict_link_measure(mh, link, cost_per_km_wired, cost_wireless)
        if m:
            created_measures |= {m}
    logger.info("created %u ict link measures" % len(created_measures))
    return created_measures




def create_ict_link_measure(mh, link, cost_per_km_wired, cost_wireless,
                            measure_type=ICTLinkMeasure):
    type = mh.ict_net.link.type.loc[link]
    cost = None
    if type == "wired":
        cost = cost_per_km_wired
    elif type == "wireless":
        cost = cost_wireless
    m = measure_type(mh.ict_net, link, cost_per_km=cost)
    mh.add_measure(m)
    return m.name

def create_ict_antenna_measures(mh, cost_per_antenna=1, measure_type=ICTAntennaMeasure):
    ict_net = mh.ict_net

    created_measures = set()
    for antenna in ict_net.antenna.index:
        m = create_ict_antenna_measure(mh, antenna, cost_per_antenna)
        if m:
            created_measures |= {m}
    logger.info("created %u ict antenna measures" % len(created_measures))
    return created_measures

def create_ict_antenna_measure(mh, antenna, cost_per_antenna, measure_type=ICTAntennaMeasure):
    m = measure_type(mh.ict_net, antenna=antenna, cost_per_antenna=cost_per_antenna)
    mh.add_measure(m)
    return m.name
