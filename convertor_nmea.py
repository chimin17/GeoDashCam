import piexif
import cv2
import os, time, sys, datetime
import pynmea2
from fractions import Fraction
import math
import numpy as np
from datetime import datetime

IMAGE_DIR = ""
def video2image(video_filename):
    image_dir_for_video = IMAGE_DIR + os.path.basename(video_filename).split('.')[0]+"/"
    image_name_prefix = os.path.basename(video_filename).split('.')[0]+"_"
    if not os.path.exists(image_dir_for_video):
        os.makedirs(image_dir_for_video)

    images = []
    vidcap = cv2.VideoCapture(video_filename)
    hasFrames = True
    sec = 1
    frameRate = 1
    count = 1
    while hasFrames:
        vidcap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        hasFrames, image = vidcap.read()
        if hasFrames:
            # kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            # brightness = 10 
            # contrast = 2.3  
            # image = cv2.addWeighted(image, contrast, np.zeros(image.shape, image.dtype), 0, brightness) 
              
            cv2.imwrite(image_dir_for_video + image_name_prefix + "image" +
                        str(count).zfill(6) + ".jpg", image)  # save frame as JPG file
            images.append(image_dir_for_video + image_name_prefix + "image" +
                          str(count).zfill(6) + ".jpg")
            count = count + 1
            sec = sec + frameRate
            sec = round(sec, 2)
    return images

def change_to_rational(number):
    """convert a number to rantional
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)

def deg_to_dms(decimal_coordinate, cardinal_directions):
    """
    This function converts decimal coordinates into the DMS (degrees, minutes and seconds) format.
    It also determines the cardinal direction of the coordinates.

    :param decimal_coordinate: the decimal coordinates, such as 34.0522
    :param cardinal_directions: the locations of the decimal coordinate, such as ["S", "N"] or ["W", "E"]
    :return: degrees, minutes, seconds and compass_direction
    :rtype: int, int, float, string
    """
    if decimal_coordinate < 0:
        compass_direction = cardinal_directions[0]
    elif decimal_coordinate > 0:
        compass_direction = cardinal_directions[1]
    else:
        compass_direction = ""
    degrees = int(abs(decimal_coordinate))
    decimal_minutes = (abs(decimal_coordinate) - degrees) * 60
    minutes = int(decimal_minutes)
    seconds = Fraction((decimal_minutes - minutes) * 60).limit_denominator(100)
    return degrees, minutes, seconds, compass_direction

def dms_to_exif_format(dms_degrees, dms_minutes, dms_seconds):
    """
    This function converts DMS (degrees, minutes and seconds) to values that can
    be used with the EXIF (Exchangeable Image File Format).

    :param dms_degrees: int value for degrees
    :param dms_minutes: int value for minutes
    :param dms_seconds: fractions.Fraction value for seconds
    :return: EXIF values for the provided DMS values
    :rtype: nested tuple
    """
    exif_format = (
        (dms_degrees, 1),
        (dms_minutes, 1),
        (int(dms_seconds.limit_denominator(100).numerator), int(dms_seconds.limit_denominator(100).denominator))
    )
    return exif_format


def add_geolocation(image_path, latitude, longitude, altitude=None,direction=None):
    """
    This function adds GPS values to an image using the EXIF format.
    This fumction calls the functions deg_to_dms and dms_to_exif_format.

    :param image_path: image to add the GPS data to
    :param latitude: the north–south position coordinate
    :param longitude: the east–west position coordinate
    """
    # converts the latitude and longitude coordinates to DMS
    latitude_dms = deg_to_dms(latitude, ["S", "N"])
    longitude_dms = deg_to_dms(longitude, ["W", "E"])

    # convert the DMS values to EXIF values
    exif_latitude = dms_to_exif_format(latitude_dms[0], latitude_dms[1], latitude_dms[2])
    exif_longitude = dms_to_exif_format(longitude_dms[0], longitude_dms[1], longitude_dms[2])

    try:
        # Load existing EXIF data
        exif_data = piexif.load(image_path)

        # https://exiftool.org/TagNames/GPS.html
        # Create the GPS EXIF data
        coordinates = {}
        if altitude == None:
            coordinates = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: exif_latitude,
                piexif.GPSIFD.GPSLatitudeRef: latitude_dms[3],
                piexif.GPSIFD.GPSLongitude: exif_longitude,
                piexif.GPSIFD.GPSLongitudeRef: longitude_dms[3],
                #piexif.GPSIFD.GPSDateStamp: u"2024:09:18 12:12:12"
                #piexif.ImageIFD.DateTime: datetime.strptime("2024/09/18 12:32","%Y/%m/%d %H:%M").strftime("%Y:%m:%d %H:%M:%S")
            }
        else:
            coordinates = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSLatitude: exif_latitude,
                piexif.GPSIFD.GPSLatitudeRef: latitude_dms[3],
                piexif.GPSIFD.GPSLongitude: exif_longitude,
                piexif.GPSIFD.GPSLongitudeRef: longitude_dms[3],
                piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude)),
                #piexif.GPSIFD.GPSDateStamp:  u"2024:09:18 12:12:12" # u"1999:99:99 99:99:99"
                # piexif.ImageIFD.DateTime: datetime.strptime("2024/09/18 12:32","%Y/%m/%d %H:%M").strftime("%Y:%m:%d %H:%M:%S")
            }

        # Update the EXIF data with the GPS information
        exif_data['GPS'] = coordinates
        exif_data['0th'][piexif.ImageIFD.DateTime] =  datetime.now().strftime("%Y:%m:%d %H:%M:%S")
        print(exif_data['GPS'])
        
        # Direction
        if direction is not None:
            exif_data['GPS'][17]=(direction,1)
        # Dump the updated EXIF data and insert it into the image
        exif_bytes = piexif.dump(exif_data)
        piexif.insert(exif_bytes, image_path)
        print(f"EXIF data updated successfully for the image {image_path}.")
    except Exception as e:
        print(f"Error: {str(e)}")


def calculate_bearing(lat1, lon1, lat2, lon2):
    # Convert decimal degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
 
    dlon = lon2_rad - lon1_rad
 
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - \
        math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
 
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
 
    # Normalize to [0, 360) degrees
    bearing_deg = (bearing_deg + 180) % 360
 
    return bearing_deg

def read_nmea(nmea_filename):
    tracks = []
    file = open(nmea_filename, encoding='utf-8')
    
    for line in file.readlines():
        try:
            msg = pynmea2.parse(line)
            if msg.sentence_type=="GGA":
                tracks.append({"latitude":msg.latitude,
                               "longitude":msg.longitude,
                               "altitude":msg.altitude,
                               "timestamp":msg.timestamp,
                              "strtime":msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")})
                #print(repr(msg))
                
                
        except pynmea2.ParseError as e:
            print('Parse error: {}'.format(e))
            continue
    return tracks


if __name__ == "__main__":
    for file in os.listdir('./'):
        if 'mp4' not in file.lower():
            continue
        _images = video2image(file.split('.')[0]+'.mp4')
        _tracks = read_nmea(file.split('.')[0]+'.nmea')
        
        _len_ = len(_images)
        if _len_ > len(_tracks):
            _len_ = len(_tracks)
        image_count = 0
        for i in list(range(_len_)):
            if i!=0 and abs(_tracks[i]['latitude']-_tracks[i-1]['latitude'])< 0.00001 and abs(_tracks[i]['longitude']-_tracks[i-1]['longitude'])< 0.00001:
                os.remove(_images[i])
            else:
                direction=0
                if i!=0:
                    direction=calculate_bearing(_tracks[i]['latitude'], _tracks[i]['longitude'], _tracks[i-1]['latitude'], _tracks[i-1]['longitude'])
                    direction = round(direction)
                latitude = _tracks[i]['latitude']
                longitude = _tracks[i]['longitude']
                altitude = _tracks[i]['altitude']
                image_path = _images[i]  # Path to your imaged
                
                add_geolocation(image_path, latitude, longitude,altitude,direction)
                os.rename(image_path,image_path[:-10]+str(image_count).zfill(6)+".jpg")
                image_count+=1