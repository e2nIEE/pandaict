import logging
pilogger = logging.getLogger("pandaICT_Core")
fh = logging.FileHandler('pandaICT_Core.log')
# fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
pilogger.setLevel(logging.DEBUG)
pilogger.addHandler(fh)

pilogger.info("-------------- pandaICT_Core startup ---------------")

