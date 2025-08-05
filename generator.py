### todo:
# move simdata to json files
# add generation of departures too
# customizable arrivals (intervals, directions, destinations)
# customizable departures (directions)
# prepare ~40 arrivals and departures from real life data
# add EPKK/EPKT support


import json

from simdata import pseudopilot_data, airport_alt, runway_data, holding_data, controller_data, \
                    inbound_spawns, requested_altitude_departures, requested_altitude_arrivals, \
                    initial_pseudopilot, arrivals_star_waypoints

from defaults import DEFAULT_HDG, DEFAULT_SPAWN, DEFAULT_TAXI_SPEED, DEFAULT_TAXIWAY_USAGE, \
                     DEFAULT_OBJECT_EXTENT, DEFAULT_REQ_ALT_DEPARTURE, DEFAULT_REQ_ALT_ARRIVAL, \
                     DEFAULT_WAVE_INTERVAL, DEFAULT_WAVE_START

from templates import HOLDING_TEMPLATE, POSITION_TEMPLATE, FPL_TEMPLATE, PSEUDOPILOT_TEMPLATE, \
                      SIMDATA_TEMPLATE, ROUTE_TEMPLATE, REQUALT_TEMPLATE, FLIGHT_TEMPLATE, \
                      SCENARIO_TEMPLATE, RUNWAY_TEMPLATE


def import_simdata(simdata_path):
    with open(simdata_path, 'r', encoding='utf-8') as simdata_file:
        return json.load(simdata_file)

def generate_runways(runway_data):
    runways = []
    for runway in runway_data:
        runways.append(RUNWAY_TEMPLATE.format(runway["name"][-2:], runway["lat1"], runway["lon1"], runway["lat2"], runway["lon2"]))
    return '\n'.join(runways)

def generate_holdings(holding_data):
    holdings = []
    for holding in holding_data:
        turn_direction = '-1' if holding['turn'] == 'left' else '1'
        holdings.append(HOLDING_TEMPLATE.format(holding["fix"], holding["inbound_track"], turn_direction))
    return '\n'.join(holdings)

def generate_controllers(controller_data, pseudopilot_data):
    controllers = []
    for controller in controller_data:
        controllers.append(PSEUDOPILOT_TEMPLATE.format(pseudopilot_data, controller["name"], controller["frequency"]))
    return '\n'.join(controllers)

def transform_heading(flight_data):
    initial_heading = float(flight_data.get('initial_heading', DEFAULT_HDG))
    transformed_heading = int(initial_heading * 2.88 + 0.5) << 2  # per Euroscope docs
    return transformed_heading

def get_spawn_coordinates(flight_data):
    if not flight_data['latitude'] or not flight_data['longitude']:
        tma_boundary = flight_data['fpl_route'].split()[-1]  # last wpt is the TMA boundary
        spawn_latitude, spawn_longitude = inbound_spawns.get(tma_boundary, DEFAULT_SPAWN)
    else:
        spawn_latitude, spawn_longitude = flight_data['latitude'], flight_data['longitude']
    return spawn_latitude, spawn_longitude

def generate_position_data(flight_data):
    spawn_latitude, spawn_longitude = get_spawn_coordinates(flight_data)
    transformed_heading = transform_heading(flight_data)
    return POSITION_TEMPLATE.format(flight_data['transponder'], flight_data['callsign'], 
                                    flight_data['squawk'], spawn_latitude, spawn_longitude,
                                    flight_data['altitude'], transformed_heading)

def generate_fpl_data(flight_data):
    return FPL_TEMPLATE.format(flight_data['callsign'], flight_data['flight_plan_type'],
                               flight_data['aircraft_type'], flight_data['true_air_speed'],
                               flight_data['origin_airport'], flight_data['departure_time_est'],
                               flight_data['departure_time_act'], flight_data['final_cruising_altitude'],
                               flight_data['destination_airport'], flight_data['hrs_en_route'],
                               flight_data['mins_en_route'], flight_data['hrs_fuel'], flight_data['mins_fuel'],
                               flight_data['alternate_airport'], flight_data['remarks'], flight_data['fpl_route'])

def generate_simdata(flight_data):
    taxi_speed = flight_data['max_taxi_speed'] if flight_data['max_taxi_speed'] else DEFAULT_TAXI_SPEED
    taxiway_usage = flight_data['taxiway_usage'] if flight_data['taxiway_usage'] else DEFAULT_TAXIWAY_USAGE
    object_extent = flight_data['object_extent'] if flight_data['object_extent'] else DEFAULT_OBJECT_EXTENT
    simdata = SIMDATA_TEMPLATE.format(flight_data['callsign'], taxi_speed, taxiway_usage, object_extent)
    return simdata

def generate_route(flight_data, sid_waypoints='', star_waypoints=''):
    assert sid_waypoints or star_waypoints, "Either SID or STAR waypoints must be provided for each flight."
    assert not (sid_waypoints and star_waypoints), "Only one of SID or STAR waypoints should be provided for each flight."

    route = ''
    if star_waypoints:
        route += ROUTE_TEMPLATE.format(flight_data['fpl_route'].split()[-1] + ' ' + star_waypoints)
    elif sid_waypoints:
        route += ROUTE_TEMPLATE.format(sid_waypoints + ' ' + flight_data['fpl_route'])
    return route

def generate_reqalt(flight_data, sid_waypoints='', star_waypoints=''):
    assert sid_waypoints or star_waypoints, "Either SID or STAR waypoints must be provided for each flight."
    assert not (sid_waypoints and star_waypoints), "Only one of SID or STAR waypoints should be provided for each flight."

    tma_boundary = flight_data['fpl_route'].split()[-1]  # assumes that last wpt in the route is the TMA boundary
    destination_rwy = flight_data.get('destination_rwy', None)

    if star_waypoints:
        try:
            reqalt = REQUALT_TEMPLATE.format(tma_boundary, requested_altitude_arrivals[destination_rwy][tma_boundary])
        except KeyError:
            reqalt = REQUALT_TEMPLATE.format('', DEFAULT_REQ_ALT_ARRIVAL)
    elif sid_waypoints:
        reqalt = REQUALT_TEMPLATE.format('', requested_altitude_departures.get(flight_data['origin_airport'], DEFAULT_REQ_ALT_DEPARTURE))
    else:
        reqalt = REQUALT_TEMPLATE.format('', DEFAULT_REQ_ALT_DEPARTURE)

    return reqalt

def generate_single_flight(flight_data, pseudopilot_data, initial_pseudopilot, start, \
                    sid_waypoints = '', star_waypoints = ''):
    position = generate_position_data(flight_data)
    flight_plan = generate_fpl_data(flight_data)
    simdata = generate_simdata(flight_data)
    route = generate_route(flight_data, sid_waypoints, star_waypoints)
    reqalt = generate_reqalt(flight_data, sid_waypoints, star_waypoints)

    flight = FLIGHT_TEMPLATE.format(pseudopilot_data, position, flight_plan,
                                    simdata, route, str(start),
                                    reqalt, initial_pseudopilot)

    return flight

def generate_flights_from_json(path_flights_file):
    with open(path_flights_file, 'r', encoding='utf-8') as flights_file:
        all_flights_data = json.load(flights_file)

    flights = []
    start = DEFAULT_WAVE_START

    for flight_data in all_flights_data:
        destination_rwy = flight_data.get('destination_rwy', None)
        tma_boundary = flight_data['fpl_route'].split()[-1]
        star_waypoints = arrivals_star_waypoints[destination_rwy][tma_boundary]
        flight = generate_single_flight(flight_data, pseudopilot_data, initial_pseudopilot, start, star_waypoints=star_waypoints)
        flights.append(flight)

        start += DEFAULT_WAVE_INTERVAL

    return flights

def make_test_scenario(path_flights_file, runway_data, holding_data, controller_data, pseudopilot_data):
    runways, holdings, controllers = generate_runways(runway_data), generate_holdings(holding_data), generate_controllers(controller_data, pseudopilot_data)
    flight = '\n'.join(generate_flights_from_json(path_flights_file))
    return SCENARIO_TEMPLATE.format(pseudopilot_data, airport_alt, runways, holdings, controllers, flight)

with open('test_scenario.txt', 'w', encoding='utf-8') as scenario_file:
    scenario_file.write(make_test_scenario('flights.json', runway_data, holding_data, controller_data, pseudopilot_data))