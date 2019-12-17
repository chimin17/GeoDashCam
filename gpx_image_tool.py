import gpxpy
import gpxpy.gpx
import cv2
import os, time, sys, datetime
from GPSPhoto import gpsphoto

IMAGE_DIR = "D:\\_tmp\\mapillary_test\\image\\"

def read_gpx(gpx_filename):
    gpx_file = open(gpx_filename, 'r')
    gpx = gpxpy.parse(gpx_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append(point)

    points
    return points


def video2image(video_filename):
    image_dir_for_video = IMAGE_DIR + os.path.basename(video_filename).split('.')[0]+"\\"
    image_name_prefix = os.path.basename(video_filename).split('.')[0]+"_"
    if not os.path.exists(image_dir_for_video):
        os.makedirs(image_dir_for_video)

    images = []
    vidcap = cv2.VideoCapture(video_filename)
    hasFrames = True
    sec = 0
    frameRate = 1
    count = 1
    while hasFrames:
        vidcap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        hasFrames, image = vidcap.read()
        if hasFrames:
            cv2.imwrite(image_dir_for_video + image_name_prefix + "image" +
                        str(count) + ".jpg", image)  # save frame as JPG file
            images.append(image_dir_for_video + image_name_prefix + "image" +
                          str(count) + ".jpg")
            count = count + 1
            sec = sec + frameRate
            sec = round(sec, 2)
    return images


def checklastframetime(video_filename):
    return datetime.datetime.fromtimestamp(
        os.path.getmtime(video_filename)).strftime('%Y:%m:%d %H:%M:%S')


def remove_image(filename):
    os.remove(filename)

def overwite_exif(image_filename, point):
    photo = gpsphoto.GPSPhoto(image_filename)

    # Create GPSInfo Data Object
    print('Point at ({0},{1}) -> {2}'.format(point.latitude, point.longitude,
                                             point.elevation))
    elevation = 0
    if point.elevation != None:
        elevation = point.elevation
    info = gpsphoto.GPSInfo((point.latitude, point.longitude),
                            alt=int(elevation),
                            timeStamp=point.time + datetime.timedelta(hours=8))

    # Modify GPS Data
    photo.modGPSData(info, image_filename)

if __name__ == "__main__":

  gpx_filename = sys.argv[1]
  mp4_filename = sys.argv[2]
    
  _gpx = read_gpx(gpx_filename)
  _images = video2image(mp4_filename)

  print("number of gpx: %s" % len(_gpx))
  print("number of images: %s" % len(_images))

  _lastframe_time = checklastframetime(mp4_filename)
  print("last modified of mp4: %s" % _lastframe_time)
  print("last gpx time: %s" % _gpx[len(_gpx) - 1].time)



  for idx in list(range(len(_gpx))):
      if idx!=0 and abs(_gpx[idx].latitude-_gpx[idx-1].latitude)< 0.00001 and abs(_gpx[idx].longitude-_gpx[idx-1].longitude)< 0.00001:
          remove_image(_images[idx])
      else:
          overwite_exif(_images[idx], _gpx[idx])
