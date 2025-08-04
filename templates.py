POSITION_TEMPLATE = '@{0}:{1}:{2}:1:{3}:{4}:{5}:0:{6}:0'
FPL_TEMPLATE = '$FP{0}:*A:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}:{10}:{11}:{12}:{13}:{14}:{15}'
SIMDATA_TEMPLATE = 'SIMDATA:{0}:*:*:{1}:{2}:{3}'
ROUTE_TEMPLATE = '$ROUTE:{0}'
REQUALT_TEMPLATE = 'REQALT:{0}:{1}'


# @<transponder flag>:<callsign>:<squawk code>:1:<latitude>:<longitude>:<altitude>:0:<heading>:0
# $FP<callsign>:*A:<flight plan type>:<aircraft type>:<true air speed>:<origin airport>:<departure time EST>:<departure time ACT>:<final cruising altitude>:<destination airport>:<HRS en route>:<MINS en route>:<HRS fuel>:<MINS fuel>:<alternate airport>:<remarks>:<route>
# SIMDATA:<callsign>:<plane type>:<livery>:<maximum taxi speed>:<taxiway usage>:<object extent>
# $ROUTE:<point by point route>

FLIGHT_TEMPLATE = '''
PSEUDOPILOT:{0}
{1}
{2}
{3}
{4}
START:{5}
DELAY:1:2
{6}
INITIALPSEUDOPILOT:{7}'''

SCENARIO_TEMPLATE = '''
PSEUDOPILOT:{0}

AIRPORT_ALT:{1}

{2}

{3}

{4}

{5}
'''
