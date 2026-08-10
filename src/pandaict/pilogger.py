import logging

# Create logger
pilogger = logging.getLogger("pandaICT_Core")
pilogger.setLevel(logging.DEBUG)

# Create formatters
console_formatter = logging.Formatter('%(levelname)s - %(message)s')
file_formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')

# File handler (DEBUG and above)
fh = logging.FileHandler('pandaICT_Core.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(file_formatter)

# Console handler (INFO and above)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
ch.setFormatter(console_formatter)

# Add handlers to logger
pilogger.addHandler(fh)
pilogger.addHandler(ch)

pilogger.info("-------------- pandaICT_Core startup ---------------")