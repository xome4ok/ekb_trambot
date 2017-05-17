#!/usr/bin/env python3

import json
import math
from typing import NamedTuple
import requests
from lxml import html

ETTU_JSON = 'ettu2.json'

EttuStation = NamedTuple('EttuStation', [
    ('letter', str),
    ('name', str),
    ('letter_url', str),
    ('url', str),
    ('lat', float),
    ('lon', float)
])

class Ettu():
    """Interface for dealing with m.ettu.ru's parsed data.

    NOTE: needs ETTU_JSON file, obtained via ./scripts/process.py
    """
    def __init__(self, logger):
        self.logger = logger
        self.stations = list(self.parse_stations())

    def parse_stations(self):
        '''Parse stations from previously scraped json file.'''
        levels = dict(one=list(), two=list(), three=list())
        errors = 0
        with open(ETTU_JSON, 'r') as ettujson:
            raw = json.load(ettujson)
            for station in raw['main']:
                if station['level'] == 1:
                    levels['one'].append(
                        dict(
                            url=station['link'],
                            name=station['name']
                        )
                    )
                if station['level'] == 2:
                    levels['two'].append(
                        dict(
                            url=station['link'],
                            parent_url=station['parent_url'],
                            name=station['name']
                        )
                    )
                if station['level'] == 3:
                    if station['error'] == 'False':
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
                    elif station['error'] == 'True':
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
                lat=station['lat'],
                lon=station['lon']
            )

    def find_nearest(self, lat, lon, count):
        """Find some nearby stations by distance on globe.

        :param lat: latitude of user
        :param lon: longitude of user
        :param count: how many nearby stations you want
        """
        dists = map(lambda station: Ettu.harvesine_dist(station.lat, station.lon, lat, lon), self.stations)
        nearest = sorted(zip(self.stations, dists), key=lambda s: s[1])[:count]
        return [z[0] for z in nearest]

    @staticmethod
    def harvesine_dist(lat1, lon1, lat2, lon2):
        """Distance on globe.

        https://en.wikipedia.org/wiki/Haversine_formula
        """
        R = 6371e3
        f1 = Ettu.deg_to_rad(lat1)
        f2 = Ettu.deg_to_rad(lat2)
        df = Ettu.deg_to_rad((lat2 - lat1))
        dl = Ettu.deg_to_rad((lon2 - lon1))
        a = (math.sin(df / 2) * math.sin(df / 2) +
            math.cos(f1) * math.cos(f2) *
            math.sin(dl / 2) * math.sin(dl / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @staticmethod
    def deg_to_rad(angle):
        """Converts degrees to radians"""
        return math.pi * angle / 180.0

    @staticmethod
    def get_info(station: EttuStation):
        """Fetches information about current situation of transport on given station.

        :return: name of station and time of query, type of transport, information on nearby transport (if any)
        """
        resp = requests.get(station.url)
        tree = html.fromstring(resp.text)
        type_a = tree.xpath("//a[@href='/m/Main']")[0].text.strip().split()[1]
        stop_name_time = tree.xpath("//p[preceding-sibling::h2][1]")[0].text_content().strip()
        routes_dists_times = list(map(
            lambda x: x.text_content(),
            tree.xpath("//div[contains(@style,'display:inline-block;')]")
        ))
        if routes_dists_times:
            glued_info = []
            for i in range(0, len(routes_dists_times), 3):
                glued_info.append(
                    routes_dists_times[i:i+3]
                )
            return stop_name_time, type_a, glued_info
        else:
            return stop_name_time, type_a, None
