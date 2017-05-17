#!/usr/bin/env python3

import json
import math
from typing import NamedTuple #typing==3.6.1
import requests # requests==2.2.1
from lxml import html #lxml==3.3.3

ETTU_JSON = 'ettu2.json'

EttuStation = NamedTuple('EttuStation', [
    ('letter', str),
    ('name', str),
    ('letter_url', str),
    ('url', str),
    ('markerLat', float),
    ('markerLon', float)
])

class Ettu():
    def __init__(self, logger):
        self.stations = self.parse_stations()
        self.logger = logger

    def parse_stations(self):
        levels = dict(one=list(), two=list(), three=list())
        errors = 0
        with open(ETTU_JSON, 'r') as ettujson:
            raw = json.load(ettujson)
            for station in raw['main']:
                if not station.get('error', None):
                    if station['level'] == 1:
                        levels['one'].append(
                            dict(
                                link=station['link'], 
                                name=station['name']
                            )
                        )
                    if station['level'] == 2:
                        levels['two'].append(
                            dict(
                                link=station['link'], 
                                parent_url=station['parent_url'], 
                                name=station['name']
                            )
                        )
                    if station['level'] == 3:
                        lat, lon = (tuple(map(float, station['marker_coords'].split(','))) 
                            if station['marker_coords'] 
                            else (-1.0, -1.0))
                        levels['three'].append(
                            dict(
                                url=station['url'],
                                lat=lat,
                                lon=lon
                            )
                        )
                elif station['error'] == True:
                    errors += 1
        self.logger.info('Parsed stations. Errors count: {}'.format(errors))

        for station in levels['three']:
            level1 = [
                x for y in levels['two'] if y['url'] == station['url'] 
                for x in levels['one'] if x['url'] == y['parent_url']
            ][0]
            yield EttuStation(
                letter=level1['name'],
                name=[x['name'] for x in levels['two'] if x['url'] == station['url']],
                letter_url=level1['url'],
                url=station['url'],
                markerLat=station['markerLat'],
                markerLon=station['markerLon']
            )

    def find_nearest(self, lat, lon, count):
        self.logger.info("finding nearest...")
        dists = map(lambda lat0, lon0: harvesine_dist(lat0, lon0, lat, lon), self.stations)
        nearest = sorted(zip(self.stations, dists), key=lambda s: s[1])[:count]
        return [z[1] for z in nearest]

    def harvesine_dist(lat1, lon1, lat2, lon2):
        R = 6371e3
        f1 = deg_to_rad(lat1)
        f2 = deg_to_rad(lat2)
        df = deg_to_rad((lat2 - lat1))
        dl = deg_to_rad((lon2 - lon1))
        a = (math.sin(df / 2) * math.sin(df / 2) +
            math.cos(f1) * math.cos(f2) *
            math.sin(dl / 2) * math.sin(dl / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def deg_to_rad(deg):
        return math.pi * angle / 180.0

    def get_info(self, station: EttuStation):
        resp = requests.get(stations.url)
        tree = html.fromstring(resp.content)
        type_a = tree.xpath("//a[@href='/m/Main']")[0].text.strip().split()[1]
        stop_name_time = tree.xpath("//p[preceding-sibling::h2][1]")[0].text_content().strip()
        routes_dists_times = map(
            lambda x: x.text_content(),
            tree.xpath("//div[contains(@style,'display:inline-block;')]")
        )
        if routes_dists_times:
            glued_info = []
            for i in range(0, len(routes_dists_times), 3):
                glued_info.append(
                    ', '.join(routes_dists_times[i:i+3])
                )
            return '{} ({})\n{}'.format(stop_name_time, type_a, glued_info)
        else:
            return '{} ({})\n{}'.format(stop_name_time, type_a, 'нет транспорта')


