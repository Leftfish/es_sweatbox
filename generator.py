import json
import random

from defaults import DEFAULT_HDG, DEFAULT_SPAWN, DEFAULT_TAXI_SPEED, DEFAULT_TAXIWAY_USAGE, \
                     DEFAULT_OBJECT_EXTENT, DEFAULT_REQ_ALT_DEPARTURE, DEFAULT_REQ_ALT_ARRIVAL, \
                     DEFAULT_WAVE_INTERVAL, DEFAULT_WAVE_START, EXCEPTION_MSG_SID_AND_STAR, \
                     EXCEPTION_MSG_SID_OR_STAR, SPAWN_OFFSET_LO, SPAWN_OFFSET_HI

from templates import HOLDING_TEMPLATE, POSITION_TEMPLATE, FPL_TEMPLATE, PSEUDOPILOT_TEMPLATE, \
                      SIMDATA_TEMPLATE, ROUTE_TEMPLATE, REQUALT_TEMPLATE, FLIGHT_TEMPLATE, \
                      SCENARIO_TEMPLATE, RUNWAY_TEMPLATE


def import_simdata(simdata_path):
    with open(simdata_path, 'r', encoding='utf-8') as simdata_file:
        return json.load(simdata_file)

def generate_runways(runway_data):
    runways = []
    for runway in runway_data:
        runways.append(RUNWAY_TEMPLATE.format(runway["name"][-2:],
                                              runway["lat1"],
                                              runway["lon1"],
                                              runway["lat2"],
                                              runway["lon2"]))
    return '\n'.join(runways)

def generate_holdings(holding_data):
    holdings = []
    for holding in holding_data:
        turn_direction = '-1' if holding['turn'] == 'left' else '1'
        holdings.append(HOLDING_TEMPLATE.format(holding["fix"],
                                                holding["inbound_track"],
                                                turn_direction))
    return '\n'.join(holdings)

def generate_controllers(controller_data, pseudopilot_data):
    controllers = []
    for controller in controller_data:
        controllers.append(PSEUDOPILOT_TEMPLATE.format(pseudopilot_data,
                                                       controller["name"],
                                                       controller["frequency"]))
    return '\n'.join(controllers)

def transform_heading(flight_data):
    initial_heading = float(flight_data.get('initial_heading', DEFAULT_HDG))
    transformed_heading = int(initial_heading * 2.88 + 0.5) << 2  # per Euroscope docs
    return transformed_heading

def get_spawn_coordinates(flight_data, inbound_spawns):
    if not flight_data['latitude'] or not flight_data['longitude']:
        tma_boundary = flight_data['fpl_route'].split()[-1]  # last wpt is the TMA boundary
        spawn_latitude, spawn_longitude = inbound_spawns.get(tma_boundary, DEFAULT_SPAWN)
    else:
        spawn_latitude, spawn_longitude = flight_data['latitude'], flight_data['longitude']
    return spawn_latitude, spawn_longitude

def generate_position_data(flight_data, inbound_spawns):
    raw_spawn_latitude, raw_spawn_longitude = get_spawn_coordinates(flight_data, inbound_spawns)
    spawn_latitude = str(float(raw_spawn_latitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    spawn_longitude = str(float(raw_spawn_longitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    transformed_heading = transform_heading(flight_data)
    raw_altitude = int(flight_data['altitude'])
    altitude = str(raw_altitude + random.choice([-100, -0, 100]) * random.randint(0, 9))
    return POSITION_TEMPLATE.format(flight_data['transponder'], flight_data['callsign'],
                                    flight_data['squawk'], spawn_latitude, spawn_longitude,
                                    altitude, transformed_heading)

def generate_fpl_data(flight_data):
    return FPL_TEMPLATE.format(flight_data['callsign'],
                               flight_data['flight_plan_type'],
                               flight_data['aircraft_type'],
                               flight_data['true_air_speed'],
                               flight_data['origin_airport'],
                               flight_data['departure_time_est'],
                               flight_data['departure_time_act'],
                               flight_data['final_cruising_altitude'],
                               flight_data['destination_airport'],
                               flight_data['hrs_en_route'],
                               flight_data['mins_en_route'],
                               flight_data['hrs_fuel'],
                               flight_data['mins_fuel'],
                               flight_data['alternate_airport'],
                               flight_data['remarks'],
                               flight_data['fpl_route'])

def generate_simdata(flight_data):
    taxi_speed = flight_data.get('max_taxi_speed', DEFAULT_TAXI_SPEED)
    taxiway_usage = flight_data.get('taxiway_usage', DEFAULT_TAXIWAY_USAGE)
    object_extent = flight_data.get('object_extent', DEFAULT_OBJECT_EXTENT)
    simdata = SIMDATA_TEMPLATE.format(flight_data['callsign'],
                                      taxi_speed,
                                      taxiway_usage,
                                      object_extent)
    return simdata

def generate_route(flight_data, sid_waypoints='', star_waypoints=''):
    assert sid_waypoints or star_waypoints, EXCEPTION_MSG_SID_OR_STAR
    assert not (sid_waypoints and star_waypoints), EXCEPTION_MSG_SID_AND_STAR

    route = ''
    if star_waypoints:
        route += ROUTE_TEMPLATE.format(flight_data['fpl_route'].split()[-1] + ' ' + star_waypoints)
    elif sid_waypoints:
        route += ROUTE_TEMPLATE.format(sid_waypoints + ' ' + flight_data['fpl_route'])
    return route

def generate_reqalt(flight_data, requested_altitude_arrivals,
                    requested_altitude_departures, sid_waypoints='', star_waypoints=''):
    assert sid_waypoints or star_waypoints, EXCEPTION_MSG_SID_OR_STAR
    assert not (sid_waypoints and star_waypoints), EXCEPTION_MSG_SID_AND_STAR

    # assumes that last wpt in the route is the TMA boundary
    tma_boundary = flight_data['fpl_route'].split()[-1]

    destination_rwy = flight_data.get('destination_rwy', None)

    if star_waypoints:
        try:
            entry_fix = requested_altitude_arrivals[destination_rwy][tma_boundary]
            reqalt = REQUALT_TEMPLATE.format(tma_boundary, entry_fix)
        except KeyError:
            reqalt = REQUALT_TEMPLATE.format('', DEFAULT_REQ_ALT_ARRIVAL)
    elif sid_waypoints:
        departure_icao = flight_data['origin_airport']
        reqalt = REQUALT_TEMPLATE.format('', requested_altitude_departures.get(departure_icao, DEFAULT_REQ_ALT_DEPARTURE))
    else:
        reqalt = REQUALT_TEMPLATE.format('', DEFAULT_REQ_ALT_DEPARTURE)

    return reqalt

def generate_single_flight(flight_data, requested_altitude_arrivals, requested_altitude_departures,\
                           inbound_spawns, pseudopilot_data, initial_pseudopilot, start,\
                           sid_waypoints = '', star_waypoints = ''):

    position = generate_position_data(flight_data, inbound_spawns)
    flight_plan = generate_fpl_data(flight_data)
    simdata = generate_simdata(flight_data)
    route = generate_route(flight_data, sid_waypoints, star_waypoints)
    reqalt = generate_reqalt(flight_data, requested_altitude_arrivals,
                             requested_altitude_departures, sid_waypoints, star_waypoints)

    flight = FLIGHT_TEMPLATE.format(pseudopilot_data, position,
                                    flight_plan, simdata,
                                    route, str(start),
                                    reqalt, initial_pseudopilot)

    return flight

def generate_flights_from_json(path_flights_file,
                               pseudopilot_data,
                               initial_pseudopilot,
                               arrivals_star_waypoints,
                               requested_altitude_arrivals,
                               requested_altitude_departures,
                               inbound_spawns,
                               wave_interval=DEFAULT_WAVE_INTERVAL):
    with open(path_flights_file, 'r', encoding='utf-8') as flights_file:
        all_flights_data = json.load(flights_file)
        arrivals_data = all_flights_data.get('arrivals', [])

    flights = []
    start = DEFAULT_WAVE_START

    for flight_data in arrivals_data:
        destination_rwy = flight_data.get('destination_rwy', None)
        tma_boundary = flight_data['fpl_route'].split()[-1]
        star_waypoints = arrivals_star_waypoints[destination_rwy][tma_boundary]
        flight = generate_single_flight(flight_data, requested_altitude_arrivals,
                                        requested_altitude_departures,
                                        inbound_spawns,pseudopilot_data,
                                        initial_pseudopilot, start, star_waypoints=star_waypoints)
        flights.append(flight)

        start += wave_interval

    return flights

def generate_scenario(path_flights_file, simulation_data_path):
    sim_data = import_simdata(simulation_data_path)

    runways = generate_runways(sim_data['runway_data'])
    holdings = generate_holdings(sim_data['holding_data'])
    controllers = generate_controllers(sim_data['controller_data'], sim_data['pseudopilot_data'])
    flight = '\n'.join(generate_flights_from_json(path_flights_file,
                                                  pseudopilot_data=sim_data['pseudopilot_data'],
                                                  initial_pseudopilot=sim_data['initial_pseudopilot'],
                                                  arrivals_star_waypoints=sim_data['arrivals_star_waypoints'],
                                                  requested_altitude_arrivals=sim_data['requested_altitude_arrivals'],
                                                  requested_altitude_departures=sim_data['requested_altitude_departures'],
                                                  inbound_spawns=sim_data['inbound_spawns']))

    return SCENARIO_TEMPLATE.format(sim_data['pseudopilot_data'],
                                    sim_data['airport_alt'],
                                    runways,
                                    holdings,
                                    controllers,
                                    flight)


def save_scenario_to_file(path_flights_file, simulation_data_path, output_path):
    with open(output_path, 'w', encoding='utf-8') as scenario_file:
        scenario_file.write(generate_scenario(path_flights_file, simulation_data_path))


if __name__ == "__main__":
    save_scenario_to_file('flights_wa33.json', 'config_wa33.json', 'test_scenario.txt')
