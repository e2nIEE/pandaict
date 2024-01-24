from anaplan import MeasureHandler


class ICTMeasureHandler(MeasureHandler):
    def __init__(self, net, ict_net, loadcases=list(), gh_substation_buses_all=True):
        super().__init__(net, loadcases)
        self.ict_net = ict_net
