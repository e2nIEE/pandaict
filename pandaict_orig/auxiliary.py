from pandapower.auxiliary import ADict, get_free_id, _preserve_dtypes
import pandaict_orig as pi
import pandas as pd
import random

class pandaictNet(ADict):
    def __init__(self, *args, **kwargs):
        super(pandaictNet, self).__init__(*args, **kwargs)

    def __repr__(self):
        r = "This pandaict network includes the following parameter tables:"
        par = []
        for tb in list(self.keys()):
            if isinstance(self[tb], pd.DataFrame) and len(self[tb]) > 0:
                par.append(tb)
        for tb in par:
            length = len(self[tb])
            r += "\n   - %s (%s %s)" % (tb, length, "elements" if length > 1 else "element")
        return r


def create_wireless_ict_links(net, from_node, to_nodes):
    nodes = net.node.index
    if from_node not in nodes:
        raise UserWarning("'from_node' %s doesn't exist in ict network" % from_node)

    missing_nodes = set(to_nodes) - set(nodes)
    if missing_nodes:
        raise UserWarning("'to_nodes' %s don't exist in ict network" % missing_nodes)

    new_links = []
    for to_node in to_nodes:
        idx = pi.create_ict_link(net, from_node=from_node, to_node=to_node, type="wireless")
        new_links.append(idx)

    return new_links


