from sgp4 import io, earth_gravity, ext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from pymap3d import ecef2geodetic
import csv
from skyfield import sgp4lib
import numpy as np

'''

Define the path where the TLE could be found 
Open TLE and ensure it gets close 
Read and save every single line in the TLE

'''

tle = Path('/Users/Jose Herrera/Desktop/TFM/SW/TLEs/Global-4/sat25544-sept15.txt')
with open(tle) as file:
    lines = file.readlines()

# Initialize the satellite from the TLE by means of io.twoline2rv function
if len(lines) == 3:
    satellite = io.twoline2rv(lines[1], lines[2], earth_gravity.wgs72)
elif len(lines) == 2:
    satellite = io.twoline2rv(lines[0], lines[1], earth_gravity.wgs72)

'''

Define the initial and end desired dates for orbit propagation
It is supposed to get Local Time. Then it is transformed into UTC time to perform the propagation

NOTE: Better to get UTC time directly, so no conversion is needed
NOTE 2: .astimezone take the local time zone defined in the pc
NOTE 3: Some code may be included to introduce a more 'human-understanding' epoch (YYYY-MM-DD-TT:TT:TT.TTTT)
'''

# date_init_str = '2020-5-14 00:00:00.00' # Use in case a more human-understanding formulation is desired
# date_init = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')

date_init = datetime(2020, 9, 29, 2, 0, 0)  # Define a local initial time
date_init_utc = date_init.replace(tzinfo=None).astimezone(tz=timezone.utc)  # Initial local time to UTC

# date_end_str = '2020-5-14 23:59:59.00'
# date_end = datetime.strptime(date_end_str, '%Y-%m-%d %H:%M:%S.%f')

date_end = datetime(2020, 9, 30, 2, 0, 0)  # Define a local end time
date_end_utc = date_end.replace(tzinfo=None).astimezone(tz=timezone.utc)  # End local time to UTC

# Initialize the date for the propagation
date = date_init_utc

# CSV file is created with a header identifying what does each column represent
csvfile = open('/Users/Jose Herrera/Desktop/TFM/SW/TLEs/Global-4/Propagation/sat25544-sept15.csv', 'w', newline='')
fieldnames = ['Epoch [UTC Time]', 'X [km]', 'Y [km]', 'Z[km]', 'Vx [km/s]', 'Vy [km/s]', 'Vz [km/s]',
              'Latitude [deg]', 'Longitude [deg]', 'Altitude [km]']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='excel')
writer.writeheader()

# Orbit Propagation between the desired epochs
while date <= date_end_utc:
    r, v = satellite.propagate(date.year, date.month, date.day, date.hour, date.minute, date.second)

    '''
    SGP4 returns position and velocity in an inertial reference frame TEME (True Equator, Mean Equinox) 
    This frame does not takes into account Earth rotation movement and the apparent movement of vernal equinox 
    
    Skyfield library (it is related to SGP4) define a function which transform TEME coordinates to the ITRF 
    frame. As there is not much information about TEME frame, the conversion to another frames could introduce
    some imprecision
    
    The function TEME_to_ITRF performs the conversion and needs as parameters the julian date of the epoch and the
    position and velocity vectors as arrays. It returns then the position and velocity vectors in the ITRF frame
    
    Velocity needs to be given in units/day instead of units/second
    
    '''

    jdate = ext.jday(date.year, date.month, date.day, date.hour, date.minute, date.second) # Compute Julian Day
    r_ITRF, v_ITRF = sgp4lib.TEME_to_ITRF(jdate, np.array(r), np.array(v) * 86400)

    """
    Transform from absolute satellite coordinates centered in Earth to geographic coordinates

    One possible way is to implement analytically the following relations

    Latitude = arctan(Z) / sqrt(X^2 + Y^2)
    Longitude = arctan(|Y|/|X|)

    Longitude will need to be corrected: if x > 0, -90 < lon < 90, if x < 0, 90 < lon < 270. 
    Correction needed so that the sign of the denominator X is equal to the sign of cos(lon)

    dist = sqrt(X^2 + Y^2 + Z^2) - Measured from the center of the Earth, so:
    dist = dist - Rearth

    Other way is to use some libraries to develop this and take into account the ellipsoid. 
    One of this libraries is pymap3D which allow us to obtain longitude, latitude and altitude from the ellipsoid
    by simply apply a defined method 

    lat, lon, height = pymap3D.ecef2geodetic() 
    Inputs should be in meters. Possibility to return the outputs in degrees or in radians

    """

    lat, lon, height = ecef2geodetic(r_ITRF[0] * 10 ** 3, r_ITRF[1] * 10 ** 3, r_ITRF[2] * 10 ** 3, deg=True)

    # Write in CSV info about position, velocity, lat, lon and altitude from the ellipsoid
    writer.writerow({'Epoch [UTC Time]': date,
                     'X [km]': r_ITRF[0],
                     'Y [km]': r_ITRF[1],
                     'Z[km]': r_ITRF[2],
                     'Vx [km/s]': v_ITRF[0] / 86400,  # TEME_to_ITRF gives velocity in unit/day -> Generate unit/sec
                     'Vy [km/s]': v_ITRF[1] / 86400,
                     'Vz [km/s]': v_ITRF[2] / 86400,
                     'Latitude [deg]': lat,
                     'Longitude [deg]': lon,
                     'Altitude [km]': height / 10 ** 3})  # Altitude to km

    # Temporal resolution
    date = date + timedelta(seconds=1)
    print(date)

csvfile.close()

print(date_init_utc)
print(date_end_utc)