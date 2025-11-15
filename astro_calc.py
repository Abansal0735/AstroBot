#astro_calc.py - Swiss Ephemeris calculations + Vedic rules
# This module contains:
# PLACE_DICT: the offline place->lat/lon dictionary used by the app.
# AstroCalc: computes Julian Day, planetary longitudes, ascendant, moon sign, and house placements using pyswisseph.
# ManglikRule: checks Mars position for Manglik dosha.
# MoonSignRule: identifies Moon sign.
# Vimshottari_dasha: simplified Mahadasha calculation (approx).

import swisseph as swe
from datetime import datetime, timedelta
import json

swe.set_ephe_path('.')  # ensure Swiss Ephemeris data files are available here or adjust path

# Offline place dictionary (imported by app)
PLACE_DICT = {
    "delhi": {
        "lat": 28.7041,
        "lon": 77.1025
    },
    "new delhi": {
        "lat": 28.6139,
        "lon": 77.209
    },
    "kolkata": {
        "lat": 22.5726,
        "lon": 88.3639
    },
    "mumbai": {
        "lat": 19.076,
        "lon": 72.8777
    },
    "chennai": {
        "lat": 13.0827,
        "lon": 80.2707
    },
    "bangalore": {
        "lat": 12.9716,
        "lon": 77.5946
    },
    "hyderabad": {
        "lat": 17.385,
        "lon": 78.4867
    },
    "jaipur": {
        "lat": 26.9124,
        "lon": 75.7873
    },
    "lucknow": {
        "lat": 26.8467,
        "lon": 80.9462
    },
    "kanpur": {
        "lat": 26.4499,
        "lon": 80.3319
    },
    "punjab": {
        "lat": 31.1471,
        "lon": 75.3412
    },
    "chandigarh": {
        "lat": 30.7333,
        "lon": 76.7794
    },
    "agra": {
        "lat": 27.1767,
        "lon": 78.0081
    },
    "varanasi": {
        "lat": 25.3176,
        "lon": 82.9739
    },
    "ahmedabad": {
        "lat": 23.0225,
        "lon": 72.5714
    },
    "kochi": {
        "lat": 9.9312,
        "lon": 76.2673
    },
    "patna": {
        "lat": 25.5941,
        "lon": 85.1376
    },
    "gurgaon": {
        "lat": 28.4595,
        "lon": 77.0266
    },
    "noida": {
        "lat": 28.5355,
        "lon": 77.391
    },
    "person a": {
        "lat": 28.6139,
        "lon": 77.209
    },
    "person b": {
        "lat": 28.7041,
        "lon": 77.1025
    },
    "person c": {
        "lat": 31.1471,
        "lon": 75.3412
    },
    "rajasthan": {
        "lat": 27.0238,
        "lon": 74.2179
    },
    "madhya pradesh": {
        "lat": 22.9734,
        "lon": 78.6569
    },
    "uttar pradesh": {
        "lat": 26.8467,
        "lon": 80.9462
    },
    "bengal": {
        "lat": 22.9786,
        "lon": 87.7478
    }
}
PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN
}
ZODIAC = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

class AstroCalc:
    """Compute planetary positions, ascendant, moon sign, and houses."""
    def __init__(self, birth):
        # birth: dictionary with keys date (YYYY-MM-DD), time (HH:MM), lat, lon, tz (hours offset)
        self.birth = birth
        self._compute_julian_day()

    def _compute_julian_day(self):
        year, month, day = [int(x) for x in self.birth['date'].split('-')]
        hour, minute = [int(x) for x in self.birth['time'].split(':')]
        tz = float(self.birth.get('tz', 0.0))
        dt_local = datetime(year, month, day, hour, minute)
        dt_ut = dt_local - timedelta(hours=tz)
        self.julian_day = swe.julday(dt_ut.year, dt_ut.month, dt_ut.day, dt_ut.hour + dt_ut.minute/60.0)
        self.lat = float(self.birth['lat'])
        self.lon = float(self.birth['lon'])

    def planet_longitudes(self):
        longs = {}
        for name, pid in PLANETS.items():
            res = swe.calc_ut(self.julian_day, pid)
            lon = res[0][0]
            longs[name] = lon % 360.0
        return longs

    def ascendant(self):    # houses() returns (cusps, ascmc); ascmc[0] is ascendant
        ascmc = swe.houses(self.julian_day, self.lat, self.lon)[0]
        asc = ascmc[0]
        return asc % 360.0

    def moon_sign(self):
        moon_lon = self.planet_longitudes()['Moon']
        sign_index = int(moon_lon // 30) % 12
        return ZODIAC[sign_index], moon_lon

    def house_of_planet(self, planet_long):
        asc = self.ascendant()
        diff = (planet_long - asc) % 360.0
        house = int(diff // 30) + 1
        return house

    def compute_all(self):
        longs = self.planet_longitudes()
        asc = self.ascendant()
        houses = {name: self.house_of_planet(lon) for name, lon in longs.items()}
        moon_sign, moon_lon = self.moon_sign()
        return {
            'julian_day': self.julian_day,
            'planetary_longitudes': longs,
            'ascendant': asc,
            'houses': houses,
            'moon_sign': moon_sign,
            'moon_longitude': moon_lon
        }

class ManglikRule:
    TRIGGER_HOUSES = {1,2,4,7,8,12}
    def __init__(self, astro_calc: AstroCalc):
        self.ac = astro_calc

    def check(self):
        longs = self.ac.planet_longitudes()
        mars_lon = longs['Mars']
        mars_house = self.ac.house_of_planet(mars_lon)
        is_manglik = mars_house in ManglikRule.TRIGGER_HOUSES
        conclusion = 'Manglik' if is_manglik else 'Not Manglik'
        explanation = f"Mars longitude = {mars_lon:.3f}° => house {mars_house}. Manglik houses: {sorted(list(ManglikRule.TRIGGER_HOUSES))}."
        return {'conclusion': conclusion, 'explanation': explanation, 'trigger': is_manglik, 'mars_longitude': mars_lon, 'mars_house': mars_house}

class MoonSignRule:
    def __init__(self, astro_calc: AstroCalc):
        self.ac = astro_calc
    def get(self):
        sign, moon_lon = self.ac.moon_sign()
        explanation = f"Moon longitude = {moon_lon:.3f}° => Moon in {sign}."
        return {'moon_sign': sign, 'moon_longitude': moon_lon, 'explanation': explanation}

class VimshottariDasha:
    SEQUENCE = ['Ketu','Venus','Sun','Moon','Mars','Rahu','Jupiter','Saturn','Mercury']
    LENGTHS = {'Ketu':7,'Venus':20,'Sun':6,'Moon':10,'Mars':7,'Rahu':18,'Jupiter':16,'Saturn':19,'Mercury':17}

    def __init__(self, astro_calc: AstroCalc):
        self.ac = astro_calc

    def current_dasha(self):
        moon_lon = self.ac.planet_longitudes()['Moon']
        nak_deg = 360.0 / 27.0
        nak_index = int(moon_lon // nak_deg)
        deg_into_nak = moon_lon - (nak_index * nak_deg)
        prop = deg_into_nak / nak_deg
        seq = VimshottariDasha.SEQUENCE[:]
        rot = nak_index % len(seq)
        seq = seq[rot:] + seq[:rot]
        first_lord = seq[0]
        remaining_years_first = VimshottariDasha.LENGTHS[first_lord] * (1 - prop)
        explanation = (f"Moon longitude {moon_lon:.3f}°, nakshatra index {nak_index}, degree into nakshatra {deg_into_nak:.3f}°. " +
                       f"Approx current Mahadasha lord (simplified) = {first_lord}, remaining approx = {remaining_years_first:.3f} years.")
        return {'mahadasha': first_lord, 'explanation': explanation, 'moon_longitude': moon_lon}

if __name__ == '__main__':
    birth = {'date':'2006-10-12','time':'20:27','lat':28.6139,'lon':77.2090,'tz':5.5}
    ac = AstroCalc(birth)
    print('Computed chart:')
    print(ac.compute_all())
    print('Manglik check:', ManglikRule(ac).check())
    print('Moon sign:', MoonSignRule(ac).get())
    print('Dasha:', VimshottariDasha(ac).current_dasha())

# -----------------------------------------------END_OF_CODE------------------------------------------------------------------------------------#