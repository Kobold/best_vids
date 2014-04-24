#!/usr/bin/env python
import click
import dataset
import httplib2
import os
import sys

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


db = dataset.connect('sqlite:///mydatabase.db')


@click.group()
def cli():
    pass


@click.command()
@click.argument('username')
def scrape(username):
    """Scrape a given user's videos and ratings."""
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
      forUsername=username,
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

    table = db['videos-' + username]

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


def as_ratio(video):
    likes = max(video['likeCount'], 1)
    total = likes + float(video['dislikeCount'])
    return likes / total


@click.command()
@click.argument('username')
def bestof(username):
    """Best rated videos for a given user."""
    table = db['videos-' + username]

    template = """%f\t%d\t%d\t%s
https://www.youtube.com/watch?v=%s
    """

    for v in sorted(table.all(), key=as_ratio):
        print template % (
            as_ratio(v),
            v['likeCount'],
            v['dislikeCount'],
            v['title'],
            v['video_id'])


@click.command('list')
def list_():
    """List the channels already in the database."""
    for t in sorted(db.tables, key=lambda s: s.lower()):
        print t[7:] # strip off the videos- prefix


cli.add_command(scrape)
cli.add_command(bestof)
cli.add_command(list_)


if __name__ == '__main__':
    cli()
