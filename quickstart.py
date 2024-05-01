"""
Use the Google Photos API to download your photos

You can filter on different conditions. Use Python exif libraries to make sure
the exported photos contain dates that are more or less consistent with Google.
"""
from __future__ import print_function
import os 
import pickle
import json
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import google_auth_httplib2
import requests
from PIL import Image, ExifTags
from datetime import datetime
from datetime import timedelta
from dateutil import parser
import piexif

# Change these parameters if you wish
PORT = 8888
PAGE_SIZE = 100
INFO_DIR = "/home/daveagp/pyphotos/info/"
IMAGE_DIR = "/home/daveagp/pyphotos/images/"
MAX_DOWNLOADS = 50000
MAX_INFOS = 100000
TZ_HOURS = 7  # default conversion time zone you want from Google Photos API. 7 = LAX
USE_MAX_SIZE = True
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
IGNORE_PHOTOS_AFTER = "2015-05-14"  # Optionally, ignore recent photos

# Setup the Photo v1 API
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.readonly']
creds = None
if(os.path.exists("token.pickle")):
    with open("token.pickle", "rb") as tokenFile:
        creds = pickle.load(tokenFile)
if not creds or not creds.valid:
    if (creds and creds.expired and creds.refresh_token):
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        creds = flow.run_local_server(port = PORT)
    with open("token.pickle", "wb") as tokenFile:
        pickle.dump(creds, tokenFile)
service = build('photoslibrary', 'v1', credentials = creds, static_discovery = False)

# Call the Photo v1 API
results = service.mediaItems().list(
    pageSize=PAGE_SIZE, fields="nextPageToken,mediaItems").execute()
items = results.get('mediaItems', [])
token = results.get('nextPageToken', None)

downloads = 0
infos = 0

while token is not None and infos < MAX_INFOS:
    for item in items:
        info_filename = INFO_DIR + item['id']
        googleTimestamp = None
        if os.path.isfile(info_filename):
            print("Already done", item['id'], "skipping")
            continue
        else:
            print()
            print('id:', item['id'])
            if 'mediaMetadata' in item and 'creationTime' in item['mediaMetadata']:
                googleTimestamp = item['mediaMetadata']['creationTime']
                print(googleTimestamp)
            infos += 1
            json.dump(item, open(info_filename, "w"))
        if item['mimeType'] != 'image/jpeg':
            print('Skipping mimeType', item['mimeType'])
            continue
        if googleTimestamp[:10] >= IGNORE_PHOTOS_AFTER:
            print('Skipping recent', googleTimestamp[:10])
            continue
        if downloads >= MAX_DOWNLOADS:
            continue
        image_filename = IMAGE_DIR + item['id'] + '.jpg'
        if not os.path.isfile(image_filename):
            suffix = 'w'+str(MAX_WIDTH)+'-h'+str(MAX_HEIGHT) if USE_MAX_SIZE else 'd'
            r = requests.get(item['baseUrl']+"="+suffix)
            if r.status_code == 200:
                open(image_filename, "wb").write(r.content)
                downloads += 1
                PILobj = Image.open(image_filename)
                exif = {
                    ExifTags.TAGS[k]: v
                    for k, v in PILobj._getexif().items()
                    if k in ExifTags.TAGS
                }
                exifDate = None
                for k, v in exif.items():
                    if 'DateTimeOriginal' in k:
                        print(k, v)
                        # ignore invalid dates we sometimes see
                        if v[:4] != '0000':
                            exifDate = v
                needsNewExifDate = exifDate is None
                googleDate = parser.isoparse(googleTimestamp)
                print(googleDate)
                if exifDate is not None:
                    exif_dt = datetime.strptime(exifDate, "%Y:%m:%d %H:%M:%S")
                    days_diff = (exif_dt - googleDate.replace(tzinfo=None)).days
                    # If delta is larger than what time zones could explain, override
                    if abs(days_diff) > 2:
                        print('needs new exif date')
                        print(exifDate)
                        print(googleTimestamp)
                        needsNewExifDate = True
                if needsNewExifDate:
                    exif_dict = piexif.load(image_filename)
                    # this seems to be hard-coded due to my account? or else there is not enough info exposed by google photos api to do better
                    new_date = (googleDate - timedelta(hours=TZ_HOURS)).strftime("%Y:%m:%d %H:%M:%S")
                    print(new_date)
                    exif_dict['0th'][piexif.ImageIFD.DateTime] = new_date
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = new_date
                    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = new_date
                    exif_bytes = piexif.dump(exif_dict)
                    piexif.remove(image_filename)
                    piexif.insert(exif_bytes, image_filename)
            else:
                print('Status', r.status_code)

    results = service.mediaItems().list(
        pageSize=PAGE_SIZE,
        pageToken=token,
        fields="nextPageToken,mediaItems").execute()
    items = results.get('mediaItems', [])
    token = results.get('nextPageToken', None)

"""
- creationTime is meant to reference the camera's zone when the photo was taken
- the time zone is not explicitly part of the Google Photos API, but it is there implicitly
-- e.g. Toronto photos have UTC in creationTime but Toronto time in Photos UI, and these can be different dates
- EXIF generally has the right time/date/zone

therefore

- use EXIF when it's available. Seemingly it will match Photos UI
- otherwise inject Google Photos API creationTime into EXIF DateTimeOriginal. We can't know the time zone, so leave out the time zone
"""
