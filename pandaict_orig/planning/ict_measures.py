from anaplan.measures import REPLMeasure


class SwitchAutomationMeasure(object):
    def __init__(self, net, ict_net, client, automated_switch_time_min=0, cost=1, name=None):
        self.net = net
        self.ict_net = ict_net
        self.client = client
        self.switch = ict_net.client.element.loc[client]
        self.name = name or "automated_switch_%s" % self.switch
        self.switch_time_min = automated_switch_time_min
#        self.orig_switch_time = net.switch.time_min.loc[self.switch]
        self.cost_per_unit = cost

    def apply(self):
#        self.net.switch.time_min.loc[self.switch] = self.switch_time_min
        self.ict_net.client.in_service.loc[self.client] = True

    def undo_apply(self):
#        self.net.switch.time_min.loc[self.switch] = self.net.switch.time_manual_min.loc[self.switch]
        self.ict_net.client.in_service.loc[self.client] = False

    def cost(self):
        return self.cost_per_unit

    def __repr__(self):
        return "Automated switch measure for switch %s" % self.switch


class ICTLinkMeasure(object):
    """
    Base class for all ict_link-related measures.
    """

    def __init__(self, ict_net, link, name=None, cost_per_km=1.):
        self.ict_net = ict_net
        self.cost_per_km = cost_per_km
        self.name = name or "ict_link_%s" % link
        self.link = link
        self.length =  self.length_km()

    def apply(self):
        self.ict_net.link.in_service.loc[self.link] = True

    def undo_apply(self):
        self.ict_net.link.in_service.loc[self.link] = False

    def length_km(self):
        return self.ict_net.link.length_km.loc[self.link]

    def cost(self):
        return self.length * self.cost_per_km


class ICTAntennaMeasure(object):
    def __init__(self, ict_net, antenna, name=None, cost_per_antenna=1.):
        self.ict_net = ict_net
        self.cost_per_antenna = cost_per_antenna
        self.name = name or "ict_antenna_%s" % antenna
        self.antenna = antenna

    def apply(self):
        self.ict_net.antenna.in_service.loc[self.antenna] = True

    def undo_apply(self):
        self.ict_net.antenna.in_service.loc[self.antenna] = False

    def cost(self):
        return self.cost_per_antenna


class REPLMeasureWithHazardRate(REPLMeasure):
    def __init__(self, net, line, std_type, h_per_km=0.03, name=None, cost_per_km=1., cost_dynamic=None, **kwargs):
#        self.orig_age = net.line.age.loc[line]
#        if cost_dynamic == "age":
#            cost_per_km *= max(1/100, 1-self.orig_age/100)
#        elif cost_dynamic == "age_wo_length":
#            cost_per_km *= max(1/100, 1-self.orig_age/100)/net.line.length_km.loc[line]
        REPLMeasure.__init__(self, net, line, std_type, name=name or "REPL_with_hazard_%s" % line, cost_per_km=cost_per_km, **kwargs)
        self.orig_h_per_km = self.net.line.h_per_km.loc[self.line]
        self.h_per_km = h_per_km

    def apply(self):
#        self.orig_h_per_km = self.net.line.h_per_km.loc[self.line]
#        self.orig_age = self.net.line.age.loc[self.line]
        self.net.line.at[self.line, "h_per_km"] = self.h_per_km
#        self.net.line.at[self.line, "age"] = 0
        REPLMeasure.apply(self)

    def undo_apply(self):
        self.net.line.at[self.line, "h_per_km"] = self.orig_h_per_km
#        self.net.line.at[self.line, "age"] = self.orig_age
        REPLMeasure.undo_apply(self)
