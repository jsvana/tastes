import json
import os


import spotipy
from spotipy import util


from . import config


SCOPES = [
    "user-library-read",
]


class TrackFeatures(object):

    def __init__(self, json):
        for k, v in json.items():
            setattr(self, k, v)


class Track(object):

    def __init__(self, json):
        self.features = None
        for k, v in json.items():
            if k == "features":
                setattr(self, k, TrackFeatures(v))
            elif k == "artists":
                self.artists = []
                for artist in v:
                    self.artists.append(Artist(artist))
            else:
                setattr(self, k, v)

    def distance_from_average(self, stats_map):
        if self.features is None:
            return float("inf")
        distance = 0
        for feature, stats in stats_map.items():
            track_val = getattr(self.features, feature)
            if track_val is None:
                track_val = float("inf")
            distance += abs(track_val - stats.avg) / stats.std_dev
        return distance

    def __str__(self):
        return "{} by {}".format(
            self.name,
            ", ".join([a.name for a in self.artists]),
        )


class Artist(object):

    def __init__(self, json):
        for k, v in json.items():
            setattr(self, k, v)


def get_tracks_from_file(filename):
    tracks = {}
    with open(filename, "r") as f:
        data = json.load(f)
        for track_id, track in data.items():
            tracks[track_id] = Track(track)
    return tracks


def init_spotify(args):
    username = args.spotify_username
    if username is None:
        username = config.SPOTIFY_USERNAME

    for key, value in config.SPOTIPY_ENVIRON.items():
        os.environ[key] = value

    token = util.prompt_for_user_token(username, ",".join(SCOPES))

    if not token:
        print("Unable to get Spotify token")
        return {}

    return spotipy.Spotify(auth=token)


def get_tracks_from_spotify(args):
    sp = init_spotify(args)

    tracks = {}
    last_batch = False
    while not last_batch:
        batch_tracks = sp.current_user_saved_tracks(
            config.TRACK_BATCH_SIZE,
            len(tracks),
        )["items"]
        if len(batch_tracks) != config.TRACK_BATCH_SIZE:
            last_batch = True
        for track in batch_tracks:
            tracks[track["track"]["id"]] = Track(track["track"])

    last_batch = False
    keys_to_fetch = list(tracks.keys())
    while not last_batch:
        count = config.FEATURE_BATCH_SIZE
        if len(keys_to_fetch) < config.FEATURE_BATCH_SIZE:
            count = len(keys_to_fetch)
            last_batch = True
        keys = keys_to_fetch[:count]
        keys_to_fetch = keys_to_fetch[count:]
        batch_features = sp.audio_features(keys)
        for features in batch_features:
            if features is None:
                print("Error getting features for id")
                continue
            tracks[features["id"]].features = TrackFeatures(features)

    return tracks


def write_to_file(tracks, path):
    tracks_json = {}

    for track_id, track in tracks.items():
        tracks_json[track_id] = track.serialize()

    with open(path, "w") as f:
        json.dump(tracks_json, f)
