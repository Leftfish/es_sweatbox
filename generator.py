'''Functions for generating a scenario of departing and arriving flights.
Uses JSON data about flights and TMA data.'''

import json
import random

from defaults import DEFAULT_HDG, DEFAULT_SPAWN, DEFAULT_TAXI_SPEED, DEFAULT_TAXIWAY_USAGE, \
                     DEFAULT_OBJECT_EXTENT, DEFAULT_REQ_ALT_DEPARTURE, DEFAULT_REQ_ALT_ARRIVAL, \
                     DEFAULT_WAVE_START, DEFAULT_LAST_WAVE, \
                     EXCEPTION_MSG_SID_AND_STAR, EXCEPTION_MSG_SID_OR_STAR, \
                     SPAWN_OFFSET_LO, SPAWN_OFFSET_HI

from templates import HOLDING_TEMPLATE, POSITION_TEMPLATE, FPL_TEMPLATE, PSEUDOPILOT_TEMPLATE, \
                      SIMDATA_TEMPLATE, ROUTE_TEMPLATE, REQUALT_TEMPLATE, FLIGHT_TEMPLATE, \
                      SCENARIO_TEMPLATE, RUNWAY_TEMPLATE


def import_data(data_path):
    with open(data_path, 'r', encoding='utf-8') as data_file:
        return json.load(data_file)



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

def get_spawn_coordinates(flight_data, arrival_spawns):
    if not flight_data['latitude'] or not flight_data['longitude']:
        tma_boundary = flight_data['fpl_route'].split()[-1]  # last wpt is the TMA boundary
        spawn_latitude, spawn_longitude = arrival_spawns.get(tma_boundary, DEFAULT_SPAWN)
    else:
        spawn_latitude, spawn_longitude = flight_data['latitude'], flight_data['longitude']
    return spawn_latitude, spawn_longitude

def generate_inbound_spawn(flight_data, arrival_spawns):
    raw_spawn_latitude, raw_spawn_longitude = get_spawn_coordinates(flight_data, arrival_spawns)
    spawn_latitude = str(float(raw_spawn_latitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    spawn_longitude = str(float(raw_spawn_longitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    return spawn_latitude, spawn_longitude

def generate_departure_spawns(init_lat, init_lon, offset_lat, offset_lon):
    i = 0
    while True:
        dot_lat, dot_lon = init_lat.find('.'), init_lon.find('.')
        latitude = f'{init_lat[:dot_lat]}.{int(init_lat[dot_lat+1:]) + i * int(offset_lat)}'
        longitude = f'{init_lon[:dot_lon]}.{int(init_lon[dot_lon+1:]) + i * int(offset_lon)}'
        yield (latitude, longitude)
        i += 1

def generate_position_data(flight_data, spawn, squawk):
    spawn_latitude, spawn_longitude = spawn
    transformed_heading = transform_heading(flight_data)
    raw_altitude = int(flight_data['altitude'])
    if raw_altitude >= 1000:
        altitude = str(raw_altitude + random.choice([-100, -0, 100]) * random.randint(0, 9))
    else:
        altitude = str(raw_altitude)
    return POSITION_TEMPLATE.format(flight_data['transponder'], flight_data['callsign'],
                                    squawk, spawn_latitude, spawn_longitude,
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
                    requested_altitude_departures,
                    sid_waypoints='', star_waypoints=''):

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

def generate_single_flight(flight_data, spawn, pseudopilot_data,
                           initial_pseudopilot, start, squawk,
                           requested_altitude_arrivals = None,
                           requested_altitude_departures = None,
                           sid_waypoints = '', star_waypoints = ''):

    position = generate_position_data(flight_data, spawn, squawk)
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

def filter_flights_by_entry_point(flights, entry_point):
    filtered = [flight for flight in flights['arrivals'] if flight['fpl_route'].split()[-1] == entry_point]
    return random.sample(filtered, k=len(filtered)) if filtered else []

def generate_arrival_wave(flight_data, runway, inbound_spawn_points, min_size, max_size):
    max_wave_size = random.randint(min_size, max_size)
    random.shuffle(inbound_spawn_points)
    fix_to_flights = {fix: filter_flights_by_entry_point(flight_data, fix) for fix in inbound_spawn_points}
    print(f"Generating wave with max size {max_wave_size}.")
    wave = []
    for fix in inbound_spawn_points:
        if fix_to_flights[fix]:
            flight = fix_to_flights[fix][-1]
            if flight['destination_rwy'] == runway:
                wave.append(fix_to_flights[fix].pop())
                print(f"Added flight {flight['callsign']} as arrival from fix {fix}.")
            if len(wave) >= max_wave_size:
                break
    return wave

def convert_arrival_wave_to_string(wave, sim_data, squawk_generator, start_time = 0):
    flight_strings = []
    for flight in wave:
        entry_fix = flight['fpl_route'].split()[-1]
        runway = flight['destination_rwy']
        spawn = generate_inbound_spawn(flight, sim_data['arrival_spawns'])
        squawk = next(squawk_generator)
        flight_string = generate_single_flight(flight,
                                               spawn,
                                               sim_data['pseudopilot_data'],
                                               sim_data['initial_pseudopilot'],
                                               start_time,
                                               squawk,
                                               requested_altitude_arrivals=sim_data['requested_altitude_arrivals'],
                                               star_waypoints=sim_data['arrivals_star_waypoints'][runway][entry_fix])
        flight_strings.append(flight_string)
    return '\n'.join(flight_strings)


def generate_flights_in_waves(runway, sim_data, flight_data, squawk_generator,
                              min_size, max_size, wave_interval,
                              start, last_wave):

    capacity = sim_data['arrivals_max_capacity'][runway]
    inbound_spawn_points = list(sim_data['arrival_spawns'].keys())

    plane_count = 0
    wave_num = 0
    all_planes = ''

    while True:
        wave_num += 1
        wave = generate_arrival_wave(flight_data, runway, inbound_spawn_points, min_size, max_size)
        plane_count += len(wave)

        string_wave = convert_arrival_wave_to_string(wave, sim_data, squawk_generator, start_time=start)
        all_planes += string_wave + '\n'

        if start >= last_wave or plane_count >= capacity:
            break
        wave_interval = wave_interval + random.choice([-1, 0, 1])
        print(f'Break beteen waves: {wave_interval} minutes.')
        start += wave_interval

    print(f'{plane_count} arriving planes generated in {wave_num} waves.')
    return all_planes

def generate_squawk():
    max_squawk = 3583 #up to 6777, does not ignore 1000, 1200 etc.
    squawk = 1
    while squawk < max_squawk:
        yield str(oct(squawk))[2:].zfill(4)
        squawk += 1

def generate_departures_string(n,runway, flight_data, sim_data, squawk_generator):
    departures_string = ''
    spawns = generate_departure_spawns(*sim_data['departures_first_spawn'][runway], *sim_data['departures_spawn_offset'][runway])
    departures = random.sample(flight_data['departures'], n)
    departure_sid_waypoints = sim_data['departures_sid_waypoints'][runway]
    for flight in departures:
        spawn = next(spawns)
        squawk = next(squawk_generator)
        exit_fix = flight['fpl_route'].split()[0]
        departures_string += generate_single_flight(flight,
                                                    spawn,
                                                    sim_data['pseudopilot_data'],
                                                    sim_data['initial_pseudopilot'],
                                                    start=0,
                                                    squawk=squawk,
                                                    sid_waypoints=departure_sid_waypoints[exit_fix],
                                                    requested_altitude_departures=sim_data['requested_altitude_departures'])
        departures_string += '\n'
        print(f"Added flight {flight['callsign']} as departure to fix {exit_fix}.")
    print(f'Generated {n} departures from runway {runway}.')
    return departures_string

def generate_scenario(flights_data_path,
                      simulation_data_path,
                      arrival_runways,
                      departure_runways,
                      start = DEFAULT_WAVE_START,
                      last_wave = DEFAULT_LAST_WAVE,
                      departure_number = 0):
    sim_data = import_data(simulation_data_path)
    flight_data = import_data(flights_data_path)

    runways = generate_runways(sim_data['runway_data'])
    holdings = generate_holdings(sim_data['holding_data'])
    controllers = generate_controllers(sim_data['controller_data'], sim_data['pseudopilot_data'])

    squawk_generator = generate_squawk()

    all_flights = ''

    arrivals = ''

    for runway in arrival_runways:
        arrivals += generate_flights_in_waves(runway,
                                              sim_data,
                                              flight_data,
                                              squawk_generator=squawk_generator,
                                              start=start,
                                              last_wave=last_wave,
                                              wave_interval=sim_data['arrivals_wave_intervals'][runway],
                                              min_size=sim_data['arrivals_wave_minimum'][runway],
                                              max_size=sim_data['arrivals_wave_maximum'][runway])
    all_flights += arrivals

    for runway in departure_runways:
        all_flights += generate_departures_string(departure_number,
                                                  runway,
                                                  flight_data,
                                                  sim_data,
                                                  squawk_generator)

    return SCENARIO_TEMPLATE.format(sim_data['pseudopilot_data'],
                                    sim_data['airport_alt'],
                                    runways,
                                    holdings,
                                    controllers,
                                    all_flights)

def save_scenario(output_path, scenario):
    with open(output_path, 'w', encoding='utf-8') as scenario_file:
        scenario_file.write(scenario)

def test():
    simulated_flights = 'flights_epwa.json'
    config = 'config_wa33.json'
    output = 'test_scenario.txt'
    arwys = ['WA33']
    drwys = ['WA29']
    #rwys = ['WA33', 'MO26', 'LL25']
    save_scenario(output, generate_scenario(simulated_flights, config, arwys, drwys, departure_number=8))
    print(f'Generated a test scenario and saved it to {output}.')

if __name__ == "__main__":
    test()
