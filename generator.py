import json

from simdata import pseudopilot_data, airport_alt, runway_data, holding_data, controller_data, \
                    inbound_spawns, requested_altitude_departures, requested_altitude_arrivals, \
                    initial_pseudopilot, arrivals_star_waypoints, \
                    DEFAULT_REQ_ALT, DEFAULT_SPAWN

from templates import POSITION_TEMPLATE, FPL_TEMPLATE, SIMDATA_TEMPLATE, ROUTE_TEMPLATE, REQUALT_TEMPLATE, FLIGHT_TEMPLATE, SCENARIO_TEMPLATE

def generate_runways(runway_data):
    runways = []
    for runway in runway_data:
        runways.append(f'ILS{runway["name"][-2:]}:{runway["lat1"]}:{runway["lon1"]}:{runway["lat2"]}:{runway["lon2"]}')
    return '\n'.join(runways)

def generate_holdings(holding_data):
    holdings = []
    for holding in holding_data:
        turn_direction = '-1' if holding['turn'] == 'left' else '1'
        holdings.append(f'HOLDING:{holding["fix"]}:{holding["inbound_track"]}:{turn_direction}')
    return '\n'.join(holdings)

def generate_controllers(controller_data, pseudopilot_data):
    controllers = []
    for controller in controller_data:
        controllers.append(f'PSEUDOPILOT:{pseudopilot_data}\nCONTROLLER:{controller["name"]}:{controller["frequency"]}')
    return '\n'.join(controllers)

def generate_flight(flight_data, sid_waypoints = '', star_waypoints = '', start = 0, initial_pseudopilot=initial_pseudopilot):
    initial_heading = float(flight_data.get('initial_heading', '0'))
    transformed_heading = int(initial_heading * 2.88 + 0.5 ) << 2  # per Euroscope docs

    destination_rwy = flight_data.get('destination_rwy', None)
    tma_boundary = flight_data['fpl_route'].split()[-1]

    if not flight_data['latitude'] and not flight_data['longitude']:
        spawn_latitude, spawn_longitude = inbound_spawns.get(tma_boundary, DEFAULT_SPAWN)

    else:
        spawn_latitude, spawn_longitude = flight_data['latitude'], flight_data['longitude']

    position = POSITION_TEMPLATE.format(flight_data['transponder'], flight_data['callsign'], flight_data['squawk'],
                                        spawn_latitude, spawn_longitude, flight_data['altitude'], transformed_heading)

    flight_plan = FPL_TEMPLATE.format(flight_data['callsign'], flight_data['flight_plan_type'], flight_data['aircraft_type'],
                                      flight_data['true_air_speed'], flight_data['origin_airport'], flight_data['departure_time_est'],
                                      flight_data['departure_time_act'], flight_data['final_cruising_altitude'], flight_data['destination_airport'],
                                      flight_data['hrs_en_route'], flight_data['mins_en_route'], flight_data['hrs_fuel'], 
                                      flight_data['mins_fuel'], flight_data['alternate_airport'], flight_data['remarks'], flight_data['fpl_route'])

    simdata = SIMDATA_TEMPLATE.format(flight_data['callsign'], flight_data['max_taxi_speed'], flight_data['taxiway_usage'], flight_data['object_extent'])

    assert not (sid_waypoints and star_waypoints)

    route = ''
    reqalt = DEFAULT_REQ_ALT

    if star_waypoints:
        route += ROUTE_TEMPLATE.format(flight_data['fpl_route'].split()[-1] + ' ' + star_waypoints)

    elif sid_waypoints:
        route += ROUTE_TEMPLATE.format(sid_waypoints + ' ' + flight_data['fpl_route'])

    if star_waypoints:
        try:
            reqalt = REQUALT_TEMPLATE.format(tma_boundary, requested_altitude_arrivals[destination_rwy][tma_boundary])
        except KeyError:
            reqalt = REQUALT_TEMPLATE.format('', DEFAULT_REQ_ALT)

    elif sid_waypoints:
        reqalt = requested_altitude_departures.get(flight_data['origin_airport'], '6000')

    flight = FLIGHT_TEMPLATE.format(pseudopilot_data, position, flight_plan,
                                    simdata, route, str(start),
                                    reqalt, initial_pseudopilot)

    return flight

def generate_flights_from_json(path):
    with open(path, 'r', encoding='utf-8') as flights_file:
        all_flights_data = json.load(flights_file)

    flights = []
    start = 0

    for flight_data in all_flights_data:
        destination_rwy = flight_data.get('destination_rwy', None)
        tma_boundary = flight_data['fpl_route'].split()[-1]
        star_waypoints = arrivals_star_waypoints[destination_rwy][tma_boundary]
        flight = generate_flight(flight_data, star_waypoints=star_waypoints, start=start, initial_pseudopilot=initial_pseudopilot)

        flights.append(flight)

        start += 5

    return flights


def make_test_scenario(path, runway_data=runway_data, holding_data=holding_data, controller_data=controller_data, pseudopilot_data=pseudopilot_data):
    runways, holdings, controllers = generate_runways(runway_data), generate_holdings(holding_data), generate_controllers(controller_data, pseudopilot_data)
    flight = '\n'.join(generate_flights_from_json(path))
    return SCENARIO_TEMPLATE.format(pseudopilot_data, airport_alt, runways, holdings, controllers, flight)

with open('test_scenario.txt', 'w', encoding='utf-8') as scenario_file:
    scen = make_test_scenario(path='flights.json')
    scenario_file.write(scen)