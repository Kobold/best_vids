#!/usr/bin/python

import dataset
import httplib2
import os
import sys

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the Google Cloud Console at
# https://cloud.google.com/console.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Cloud Console
https://cloud.google.com/console

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# This OAuth 2.0 access scope allows for read-only access to the authenticated
# user's account, but not other types of account access.
YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
  message=MISSING_CLIENT_SECRETS_MESSAGE,
  scope=YOUTUBE_READONLY_SCOPE)

storage = Storage("%s-oauth2.json" % sys.argv[0])
credentials = storage.get()

if credentials is None or credentials.invalid:
  flags = argparser.parse_args()
  credentials = run_flow(flow, storage, flags)

youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
  http=credentials.authorize(httplib2.Http()))

# Retrieve the contentDetails part of the channel resource for the
# authenticated user's channel.
channels_response = youtube.channels().list(
  forUsername="majesticcasual",
  part="contentDetails"
).execute()

assert len(channels_response["items"]) == 1
channel = channels_response["items"][0]

# From the API response, extract the playlist ID that identifies the list
# of videos uploaded to the authenticated user's channel.
uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]

print "Videos in list %s" % uploads_list_id

# Retrieve the list of videos uploaded to the authenticated user's channel.
playlistitems_list_request = youtube.playlistItems().list(
  playlistId=uploads_list_id,
  part="snippet",
  maxResults=50
)

db = dataset.connect('sqlite:///mydatabase.db')
table = db['videos']

while playlistitems_list_request:
  playlistitems_list_response = playlistitems_list_request.execute()

  # Print information about each video.
  for playlist_item in playlistitems_list_response["items"]:
    title = playlist_item["snippet"]["title"]
    video_id = playlist_item["snippet"]["resourceId"]["videoId"]

    videos_response = youtube.videos().list(
      id=video_id,
      part='snippet,statistics').execute()
    assert len(videos_response["items"]) == 1
    video = videos_response["items"][0]

    likeCount = int(video['statistics']['likeCount'])
    dislikeCount = int(video['statistics']['dislikeCount'])
    print "%s (%s) %d, %d" % (title, video_id, likeCount, dislikeCount)
    table.insert(dict(
      title=title, video_id=video_id, likeCount=likeCount, dislikeCount=dislikeCount))

  playlistitems_list_request = youtube.playlistItems().list_next(
    playlistitems_list_request, playlistitems_list_response)

print

"""
playlist_item
{
    "snippet": {
        "playlistId": "UUXIyz409s7bNWVcM-vjfdVA", 
        "thumbnails": {
            "default": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/default.jpg"
            }, 
            "high": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/hqdefault.jpg"
            }, 
            "medium": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/mqdefault.jpg"
            }, 
            "maxres": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/maxresdefault.jpg"
            }, 
            "standard": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/sddefault.jpg"
            }
        }, 
        "title": "Samuel Truth - Rua", 
        "resourceId": {
            "kind": "youtube#video", 
            "videoId": "v5yHI3KsaM4"
        }, 
        "channelId": "UCXIyz409s7bNWVcM-vjfdVA", 
        "publishedAt": "2014-01-05T20:16:43.000Z", 
        "channelTitle": "Majestic Casual", 
        "position": 0, 
        "description": "Majestic Casual - Experience music in a new way.\n\u00bb Facebook: http://on.fb.me/majesticfb\n\u00bb Twitter: http://bit.ly/majestictwitter\n\nSamuel Truth, inspiring music! \n\n\u2716 Download Samuel Truth - Rua\nhttps://www.mediafire.com/?icopm7qsivd67o2\n\n\u2716 Follow Samuel Truth\nhttp://soundcloud.com/samueltruth\nhttp://www.facebook.com/samueltruthbeats\nhttp://twitter.com/Samuel_Truth\n\n\u2716 Picture \u00a9 Ren Rox\nhttp://www.renrox.com/"
    }, 
    "kind": "youtube#playlistItem", 
    "etag": "\"KJzxKWJo5Mkivb-iOczuzoxz-Rk/GtZoxvWRhGA3KERRvBApEGbVTcU\"", 
    "id": "UUIqk53Tt6m54k_VWtdn34vYFcvNbIg9E1"
}

video
{
    "snippet": {
        "thumbnails": {
            "default": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/default.jpg"
            }, 
            "high": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/hqdefault.jpg"
            }, 
            "medium": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/mqdefault.jpg"
            }, 
            "maxres": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/maxresdefault.jpg"
            }, 
            "standard": {
                "url": "https://i1.ytimg.com/vi/v5yHI3KsaM4/sddefault.jpg"
            }
        }, 
        "title": "Samuel Truth - Rua", 
        "channelId": "UCXIyz409s7bNWVcM-vjfdVA", 
        "publishedAt": "2014-01-05T20:29:55.000Z", 
        "liveBroadcastContent": "none", 
        "channelTitle": "Majestic Casual", 
        "categoryId": "10", 
        "description": "Majestic Casual - Experience music in a new way.\n\u00bb Facebook: http://on.fb.me/majesticfb\n\u00bb Twitter: http://bit.ly/majestictwitter\n\nSamuel Truth, inspiring music! \n\n\u2716 Download Samuel Truth - Rua\nhttps://www.mediafire.com/?icopm7qsivd67o2\n\n\u2716 Follow Samuel Truth\nhttp://soundcloud.com/samueltruth\nhttp://www.facebook.com/samueltruthbeats\nhttp://twitter.com/Samuel_Truth\n\n\u2716 Picture \u00a9 Ren Rox\nhttp://www.renrox.com/"
    }, 
    "statistics": {
        "commentCount": "148", 
        "viewCount": "44300", 
        "favoriteCount": "0", 
        "dislikeCount": "23", 
        "likeCount": "1712"
    }, 
    "kind": "youtube#video", 
    "etag": "\"UwFsu5nBFZheQ0Mj5CMLrV9G9b8/kFnCpoD-ALhMEg__s8KsGguUx9A\"", 
    "id": "v5yHI3KsaM4"
}
"""
