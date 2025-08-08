'''Default settings for Euroscope scenario generation'''

DEFAULT_SPAWN = ('51.0', '20.0')
# +/- in the middle of Poland

DEFAULT_HDG = '180'

DEFAULT_REQ_ALT_ARRIVAL = '10000'
# FL100 which is typically the lowest available in controlled airspace outside of TMAs in Poland

DEFAULT_REQ_ALT_DEPARTURE = '6000'
# the most common initial climb altitude for departures in Poland

DEFAULT_TAXI_SPEED = '20'
DEFAULT_TAXIWAY_USAGE = '1'
DEFAULT_OBJECT_EXTENT = '0.010'

DEFAULT_WAVE_START = 0
DEFAULT_WAVE_INTERVAL = 4
DEFAULT_LAST_WAVE = 30

EXCEPTION_MSG_SID_OR_STAR = "Either SID or STAR waypoints must be provided for each flight."
EXCEPTION_MSG_SID_AND_STAR = "Only one of SID or STAR waypoints should be provided for each flight."

SPAWN_OFFSET_LO, SPAWN_OFFSET_HI = -0.1, 0.1
MIN_FLIGHTS_PER_WAVE = 2
MAX_FLIGHTS_PER_WAVE = 4
