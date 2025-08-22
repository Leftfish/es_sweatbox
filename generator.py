'''Functions for generating a scenario of departing and arriving flights.
Uses JSON data about flights and TMA data. Tailored for approach training scenarios
on Vatsim (S3 level)'''

import argparse
import json
import random
import itertools

from defaults import MINIMUM_ARRIVAL_ALTITUDE, DEFAULT_SPAWN, DEFAULT_TAXI_SPEED, \
                     DEFAULT_TAXIWAY_USAGE, DEFAULT_OBJECT_EXTENT, \
                     DEFAULT_REQ_ALT_DEPARTURE, DEFAULT_REQ_ALT_ARRIVAL, \
                     DEFAULT_WAVE_START, DEFAULT_LAST_WAVE, \
                     EXCEPTION_MSG_SID_AND_STAR, EXCEPTION_MSG_SID_OR_STAR, \
                     SPAWN_OFFSET_LO, SPAWN_OFFSET_HI, \
                     FIR_PREFIX

from templates import HOLDING_TEMPLATE, POSITION_TEMPLATE, FPL_TEMPLATE, PSEUDOPILOT_TEMPLATE, \
                      SIMDATA_TEMPLATE, ROUTE_TEMPLATE, REQUALT_TEMPLATE, FLIGHT_TEMPLATE, \
                      SCENARIO_TEMPLATE, RUNWAY_TEMPLATE


def import_data(data_path):
    '''A simple JSON opener'''

    with open(data_path, 'r', encoding='utf-8') as data_file:
        return json.load(data_file)

def generate_runways(runway_data, arrival_runways, departure_runways):
    '''Generates runway definitions for the scenario. Formula per ES docs.
    ILS<runway name>:<threshold latitude>:<threshold longitude>:<far end latitude>:<far end longitude>'''

    simulated_runways = list(set(arrival_runways + [rwy_name for rwy_name, _ in departure_runways]))

    runways = []
    for runway_name, runway_info in runway_data.items():
        if runway_name not in simulated_runways:
            continue

        runways.append(RUNWAY_TEMPLATE.format(runway_name[-2:],
                                              runway_info["lat1"],
                                              runway_info["lon1"],
                                              runway_info["lat2"],
                                              runway_info["lon2"]))
    return '\n'.join(runways)

def generate_holdings(holding_data):
    '''Generates holding definitions for the scenario. Formula per ES docs.
    HOLDING:<fix name>:<inbound course>:<direction>'''

    holdings = []
    for holding in holding_data:
        turn_direction = '-1' if holding['turn'] == 'left' else '1'
        holdings.append(HOLDING_TEMPLATE.format(holding["fix"],
                                                holding["inbound_track"],
                                                turn_direction))
    return '\n'.join(holdings)

def generate_controllers(controller_data, pseudopilot_data):
    '''Generates controller definitions for the scenario. Fornula per ES docs.
    CONTROLLER:<callsign>:<frequency>'''

    controllers = []
    for controller in controller_data:
        controllers.append(PSEUDOPILOT_TEMPLATE.format(pseudopilot_data,
                                                       controller["name"],
                                                       controller["frequency"]))
    return '\n'.join(controllers)

def transform_heading(initial_heading):
    '''Transforms a heading given as int or str in degrees into an integer
    accepted by Euroscope/sweatbox. Formula per Euroscope docs.'''

    transformed_heading = int(float(initial_heading) * 2.88 + 0.5) << 2
    return transformed_heading

def get_spawn_coordinates(flight_data, arrival_spawns):
    '''Reads the flight data and determines the spawn coordinates.'''
    latitude = flight_data.get('latitude', None)
    longitude = flight_data.get('longitude', None)
    if not latitude or not longitude:
        tma_boundary = flight_data['fpl_route'].split()[-1]  # last wpt is the TMA boundary
        spawn_latitude, spawn_longitude = arrival_spawns.get(tma_boundary, DEFAULT_SPAWN)
    else:
        spawn_latitude, spawn_longitude = latitude, longitude
    return spawn_latitude, spawn_longitude

def generate_inbound_spawn(flight_data, arrival_spawns):
    '''Generates the inbound spawn coordinates and randomizes them by an offset.'''

    raw_spawn_latitude, raw_spawn_longitude = get_spawn_coordinates(flight_data, arrival_spawns)
    spawn_latitude = str(float(raw_spawn_latitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    spawn_longitude = str(float(raw_spawn_longitude) + random.uniform(SPAWN_OFFSET_LO, SPAWN_OFFSET_HI))[:10]
    return spawn_latitude, spawn_longitude

def generate_departure_spawns(init_lat, init_lon, offset_lat, offset_lon):
    '''Generates infinite spawn position on a single axis (e.g. runway axis or taxiway axis),
    starting from (init_lat, init_lon) and moving along the specified offsets.'''

    i = 0
    while True:
        dot_lat, dot_lon = init_lat.find('.'), init_lon.find('.')
        latitude = f'{init_lat[:dot_lat]}.{int(init_lat[dot_lat+1:]) + i * int(offset_lat)}'
        longitude = f'{init_lon[:dot_lon]}.{int(init_lon[dot_lon+1:]) + i * int(offset_lon)}'
        yield (latitude, longitude)
        i += 1

def is_proper_arrival(flight_data, sim_data):
    '''Checks if the last waypoint is an entry fix to TMA. If it is, it is a properly
    defined arrival.'''

    if sim_data:
        return flight_data['fpl_route'].split()[-1] in sim_data['arrivals_fix_headings'].keys()
    return False

def generate_initial_heading(flight_data, sim_data=None, runway=None):
    '''For arrivals, reads the heading from the simulation data according to the TMA entry fix.
    For departures, reads the heading from the runway data.
     
    Caution: for departures it is assumed that the departures spawn on the runway!'''

    if is_proper_arrival(flight_data, sim_data):
        heading = sim_data['arrivals_fix_headings'][flight_data['fpl_route'].split()[-1]]

    else:
        assert sim_data and runway, 'When no initial heading is provided, sim data and runway are required.'
        heading = sim_data['runway_data'][runway]['heading']
    return transform_heading(heading)

def generate_initial_altitude(flight_data):
    '''Generates the initial altitude for the flight. For arrival, slightly randomizes
    the altitude to simulate the ongoing descent'''

    raw_altitude = int(flight_data['altitude'])
    if raw_altitude >= MINIMUM_ARRIVAL_ALTITUDE:
        altitude = str(raw_altitude + random.choice([-100, -0, 100]) * random.randint(0, 9))
    else:
        altitude = str(raw_altitude)
    return altitude

def generate_position_data(flight_data, spawn, squawk, sim_data=None, runway=None):
    '''Generates position data for the given flight. Formula per ES docs.
    @<transponder flag>:<callsign>:<squawk code>:1:<latitude>:<longitude>:<altitude>:0:<heading>:0'''

    spawn_latitude, spawn_longitude = spawn
    heading = generate_initial_heading(flight_data, sim_data, runway)
    altitude = generate_initial_altitude(flight_data)
    return POSITION_TEMPLATE.format(flight_data['transponder'], flight_data['callsign'],
                                    squawk, spawn_latitude, spawn_longitude,
                                    altitude, heading)

def generate_fpl_data(flight_data):
    '''Generates flight plan data for the given flight. Formula per ES docs.
    $FP<callsign>:*A:<flight plan type>:<aircraft type>:<true air speed>:<origin airport>:
    <departure time EST>:<departure time ACT>:<final cruising altitude>:<destination airport>:
    <HRS en route>:<MINS en route>:<HRS fuel>:<MINS fuel>:<alternate airport>:<remarks>:<route>'''

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
    '''Generates simulation data for the given flight. Formula per ES docs.
    SIMDATA:<callsign>:<plane type>:<livery>:<maximum taxi speed>:<taxiway usage>:<object extent>'''

    taxi_speed = flight_data.get('max_taxi_speed', DEFAULT_TAXI_SPEED)
    taxiway_usage = flight_data.get('taxiway_usage', DEFAULT_TAXIWAY_USAGE)
    object_extent = flight_data.get('object_extent', DEFAULT_OBJECT_EXTENT)
    simdata = SIMDATA_TEMPLATE.format(flight_data['callsign'],
                                      taxi_speed,
                                      taxiway_usage,
                                      object_extent)
    return simdata

def generate_route(flight_data, sid_waypoints='', star_waypoints=''):
    '''Generates route data for the given flight. Formula per ES docs, but simplified (route only).
    $ROUTE:<point by point route>'''
    assert sid_waypoints or star_waypoints, EXCEPTION_MSG_SID_OR_STAR
    assert not (sid_waypoints and star_waypoints), EXCEPTION_MSG_SID_AND_STAR

    route = ''
    if star_waypoints:
        route += ROUTE_TEMPLATE.format(flight_data['fpl_route'].split()[-1] + ' ' + star_waypoints)
    elif sid_waypoints:
        route += ROUTE_TEMPLATE.format(sid_waypoints + ' ' + flight_data['fpl_route'])
    return route

def generate_reqalt(flight_data, requested_altitude_arrivals,
                    requested_altitude_departures, destination_runway = None,
                    sid_waypoints='', star_waypoints=''):
    '''Generates requested altitude data for the given flight. Formula per ES docs.
    $REQALT:<fix>:<altitude>
    
    If star_waypoints are provided, assumes it is an arrival and the last waypoint
    in the route is the TMA boundary used as <fix>. If sid_waypoints are provided,
    omits the <fix> and uses the default initial climb.'''

    assert sid_waypoints or star_waypoints, EXCEPTION_MSG_SID_OR_STAR
    assert not (sid_waypoints and star_waypoints), EXCEPTION_MSG_SID_AND_STAR

    tma_boundary = flight_data['fpl_route'].split()[-1]

    if star_waypoints:
        try:
            entry_fix = requested_altitude_arrivals[destination_runway][tma_boundary]
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
                           sim_data = None,
                           departure_runway = None,
                           destination_runway = None,
                           requested_altitude_arrivals = None,
                           requested_altitude_departures = None,
                           sid_waypoints = '', star_waypoints = ''):

    '''Puts together the various data to generate a single string with flight data
    formatted per ES docs.'''

    position = generate_position_data(flight_data,
                                      spawn,
                                      squawk,
                                      sim_data=sim_data,
                                      runway=departure_runway)
    flight_plan = generate_fpl_data(flight_data)
    simdata = generate_simdata(flight_data)
    route = generate_route(flight_data, sid_waypoints, star_waypoints)
    reqalt = generate_reqalt(flight_data,
                             requested_altitude_arrivals,
                             requested_altitude_departures,
                             destination_runway,
                             sid_waypoints,
                             star_waypoints)

    flight = FLIGHT_TEMPLATE.format(pseudopilot_data,
                                    position,
                                    flight_plan,
                                    simdata,
                                    route,
                                    str(start),
                                    reqalt,
                                    initial_pseudopilot)

    return flight

def filter_flights_by_entry_point(flights, entry_point):
    '''Filters the list of flights by the last waypoint in their flight plan,
    assumed to be the TMA entry fix.'''

    filtered = [flight for flight in flights['arrivals'] if flight['fpl_route'].split()[-1] == entry_point]
    return random.sample(filtered, k=len(filtered)) if filtered else []

def generate_arrival_wave(flight_data, runway, inbound_spawn_points, min_size, max_size):
    '''Generates a wave of arrival flights for a specific runway.
    Expects runway defined as final two letters and number, e.g. WA33 or KK25.

    1) Shuffles the inbound spawn points to ensure more diverse scenarios.
    2) Filters all flights in flight_data by the TMA entry points.
    3) Generates a wave of size between min_size and max_size (inclusive)
    4) Returns a list of dictionaries with flight data.'''

    max_wave_size = random.randint(min_size, max_size)
    random.shuffle(inbound_spawn_points)
    fix_to_flights = {fix: filter_flights_by_entry_point(flight_data, fix) for fix in inbound_spawn_points}
    print(f"Generating wave with max size {max_wave_size}.")
    wave = []
    for fix in inbound_spawn_points:
        if fix_to_flights[fix]:
            flight = fix_to_flights[fix][-1]
            destination = FIR_PREFIX + runway[:2] #e.g. EP + WA (from WA33)
            if flight['destination_airport'] == destination:
                wave.append(fix_to_flights[fix].pop())
                print(f"Added flight {flight['callsign']} as arrival from fix {fix}.")
            if len(wave) >= max_wave_size:
                break
    return wave

def convert_arrival_wave_to_string(wave, sim_data, squawk_generator, runway, start_time = 0):
    '''Converts a list of dictionaries representing flight data into a string format,
    formatted per ES docs.'''

    flight_strings = []
    for flight in wave:
        entry_fix = flight['fpl_route'].split()[-1]
        spawn = generate_inbound_spawn(flight, sim_data['arrival_spawns'])
        squawk = next(squawk_generator)
        flight_string = generate_single_flight(flight,
                                               spawn,
                                               sim_data['pseudopilot_data'],
                                               sim_data['initial_pseudopilot'],
                                               start_time,
                                               squawk,
                                               sim_data=sim_data,
                                               destination_runway=runway,
                                               requested_altitude_arrivals=sim_data['requested_altitude_arrivals'],
                                               star_waypoints=sim_data['arrivals_star_waypoints'][runway][entry_fix])
        flight_strings.append(flight_string)
    return '\n'.join(flight_strings)


def generate_flights_in_waves(runway, sim_data, flight_data, squawk_generator,
                              min_size, max_size, wave_interval,
                              start, last_wave):

    '''Generates a series of arrival flight waves for a specific runway.
    The waves stops after last_wave (minute) is reached or exceeded, 
    or the total number of planes reaches or exceeds the runway capacity.'''

    capacity = sim_data['arrivals_max_capacity'][runway]
    inbound_spawn_points = list(sim_data['arrival_spawns'].keys())

    plane_count = 0
    wave_num = 0
    all_planes = ''

    while True:
        wave_num += 1
        wave = generate_arrival_wave(flight_data, runway, inbound_spawn_points, min_size, max_size)
        plane_count += len(wave)

        string_wave = convert_arrival_wave_to_string(wave, sim_data, squawk_generator, runway, start_time=start)
        all_planes += string_wave + '\n'

        if start >= last_wave or plane_count >= capacity:
            break
        wave_interval = wave_interval + random.choice([-1, 0, 1])
        print(f'Break between waves: {wave_interval} minutes.')
        start += wave_interval

    print(f'{plane_count} arriving planes to {FIR_PREFIX+runway[:2]} generated in {wave_num} waves.')
    return all_planes

def generate_squawk():
    '''Generates a sequence of squawk codes. Simple to the fault, 
    generates codes from 0001 to 6777, but does not ignore 1000, 1200 etc.'''

    max_squawk = 3583 #oct 6777
    squawk = 1
    while squawk <= max_squawk:
        yield str(oct(squawk))[2:].zfill(4)
        squawk += 1

def generate_departures_string(n, runway, flight_data, sim_data, squawk_generator):
    '''Generates a string representation of departure flights for a specific runway.
    The flights are a sample of n from the departure flights defined in the flight data JSON.'''

    departures_string = ''
    spawns = generate_departure_spawns(*sim_data['departures_first_spawn'][runway], *sim_data['departures_spawn_offset'][runway])
    desired_destination = FIR_PREFIX + runway[:2]
    departures_to_target = [flight for flight in flight_data['departures'] if flight['origin_airport'] == desired_destination]
    departures = random.sample(departures_to_target, n)
    departure_sid_waypoints = sim_data['departures_sid_waypoints']

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
                                                    sim_data=sim_data,
                                                    departure_runway=runway,
                                                    sid_waypoints=departure_sid_waypoints[runway][exit_fix],
                                                    requested_altitude_departures=sim_data['requested_altitude_departures'])
        departures_string += '\n'
        print(f"Added flight {flight['callsign']} as departure to fix {exit_fix}.")
    print(f'Generated {n} departures from {FIR_PREFIX+runway[:2]} runway {runway[2:]}.')
    return departures_string

def generate_scenario(flights_data_path,
                      simulation_data_path,
                      arrival_runways,
                      departure_runways,
                      start = DEFAULT_WAVE_START,
                      last_wave = DEFAULT_LAST_WAVE):
    '''Generates a Euroscope sweatbox scenario with arrivals and departures.'''

    sim_data = import_data(simulation_data_path)
    flight_data = import_data(flights_data_path)

    runways = generate_runways(sim_data['runway_data'], arrival_runways, departure_runways)
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

    for runway, departure_number in departure_runways:
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
    '''Saves the scenario to output_path text file.'''

    with open(output_path, 'w', encoding='utf-8') as scenario_file:
        scenario_file.write(scenario)

if __name__ == "__main__":
    print("Generating a test scenario...")
    saved_scenario_path = 'test_scenario_EPWA_TMA.txt'
    flights_path = 'data\\EPWA_flights.json'
    config_path = 'data\\EPWA_config.json'
    save_scenario(saved_scenario_path, generate_scenario(flights_path, config_path, arrival_runways=['WA33', 'MO26'], departure_runways=[('WA29', 10), ('MO26', 3)]))
