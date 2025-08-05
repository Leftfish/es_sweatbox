'''Templates for generating sweatbox scenarios according to the Euroscope format
For more information, see: https://www.euroscope.hu/wp/scenario-file/'''

POSITION_TEMPLATE = '@{0}:{1}:{2}:1:{3}:{4}:{5}:0:{6}:0'
FPL_TEMPLATE = '$FP{0}:*A:{1}:{2}:{3}:{4}:{5}:{6}:{7}:{8}:{9}:{10}:{11}:{12}:{13}:{14}:{15}'
SIMDATA_TEMPLATE = 'SIMDATA:{0}:*:*:{1}:{2}:{3}'
ROUTE_TEMPLATE = '$ROUTE:{0}'
REQUALT_TEMPLATE = 'REQALT:{0}:{1}'

RUNWAY_TEMPLATE = 'ILS{0}:{1}:{2}:{3}:{4}'

HOLDING_TEMPLATE = 'HOLDING:{0}:{1}:{2}'

PSEUDOPILOT_TEMPLATE = 'PSEUDOPILOT:{0}\nCONTROLLER:{1}:{2}'

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