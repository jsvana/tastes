import argparse
from queue import PriorityQueue
import sys


from tabulate import tabulate


from . import (
    config,
    stats,
    track_api,
)


def parse_args():
    parser = argparse.ArgumentParser()

    g = parser.add_mutually_exclusive_group()
    g.add_argument(
        "--spotify-username",
        help="Spotify username to hit API with",
    )
    g.add_argument(
        "--local-file",
        help="Read data from provided file",
    )
    parser.add_argument(
        "--save-path",
        help="Save fetched data to provided path",
    )

    subparsers = parser.add_subparsers()

    get_favorites_parser = subparsers.add_parser(
        "get-favorites",
        help="Finds your favorite songs out of your library",
    )
    get_favorites_parser.add_argument(
        "--limit",
        default=5,
        help="Number of favorites to show (default: %(default)s)",
    )
    get_favorites_parser.set_defaults(function=cmd_get_favorites)

    get_playlists_parser = subparsers.add_parser(
        "get-playlists",
        help="Finds your playlists",
    )
    get_playlists_parser.set_defaults(function=cmd_get_playlists)

    recommend_additions_parser = subparsers.add_parser(
        "recommend-additions",
        help="Recommends new additions to a playlist from your library",
    )
    recommend_additions_parser.add_argument(
        "playlist_id",
        help="ID of the playlist",
    )
    recommend_additions_parser.add_argument(
        "playlist_owner",
        help="Owner of the playlist",
    )
    recommend_additions_parser.add_argument(
        "--limit",
        default=5,
        help="Number of recommendations to show (default: %(default)s)",
    )
    recommend_additions_parser.set_defaults(function=cmd_recommend_additions)

    find_new_parser = subparsers.add_parser(
        "find-new",
        help="Finds new tunes to listen to",
    )
    find_new_parser.add_argument(
        "--limit",
        default=20,
        help="Number of new tunes to show (default: %(default)s)",
    )
    find_new_parser.set_defaults(function=cmd_find_new)

    graph_interests_parser = subparsers.add_parser(
        "graph-interests",
        help="Plots features from your library as histograms and scatterplots",
    )
    graph_interests_parser.set_defaults(function=cmd_graph_interests)

    return parser.parse_args()


def cmd_graph_interests(args):
    if args.local_file:
        tracks = track_api.get_tracks_from_file(args.local_file)
    else:
        tracks = track_api.get_tracks_from_spotify(args)

    feature_values = stats.get_feature_values(tracks)

    stats.make_histograms(feature_values)
    stats.make_comparison_scatterplots(feature_values)

    return True


def cmd_get_favorites(args):
    if args.local_file:
        tracks = track_api.get_tracks_from_file(args.local_file)
    else:
        tracks = track_api.get_tracks_from_spotify(args)

    average_feature_values = stats.get_average_feature_values(tracks)

    best_tracks = PriorityQueue()
    for track in tracks.values():
        distance = track.distance_from_average(average_feature_values)
        best_tracks.put((distance, track))

    rows = []
    for _ in range(args.limit):
        entry = best_tracks.get()
        rows.append([
            str(entry[1]),
            entry[0],
        ])
    print(tabulate(rows, headers=["track", "score"], numalign="right"))

    return True


def cmd_get_playlists(args):
    sp = track_api.init_spotify(args)
    rows = []
    for playlist in sp.user_playlists(config.SPOTIFY_USERNAME)["items"]:
        playlist = track_api.Playlist(playlist)
        rows.append([
            playlist.name,
            playlist.id,
            playlist.owner.id,
            playlist.tracks["total"],
        ])
    print(
        tabulate(
            rows,
            headers=["name", "id", "owner_id", "tracks"],
            numalign="right",
        )
    )


def tracks_for_playlist(sp, playlist_owner, playlist_id):
    tracks = sp.user_playlist_tracks(playlist_owner, playlist_id)
    playlist_tracks = {}
    for track in tracks["items"]:
        playlist_tracks[track["track"]["id"]] = track_api.Track(track["track"])
    return track_api.fill_feature_information(sp, playlist_tracks)


def cmd_recommend_additions(args):
    sp = track_api.init_spotify(args)
    playlist_tracks = tracks_for_playlist(
        sp,
        args.playlist_owner,
        args.playlist_id,
    )

    average_feature_values = stats.get_average_feature_values(playlist_tracks)

    if args.local_file:
        library_tracks = track_api.get_tracks_from_file(args.local_file)
    else:
        library_tracks = track_api.get_tracks_from_spotify(args)

    best_tracks = PriorityQueue()
    for track in library_tracks.values():
        distance = track.distance_from_average(average_feature_values)
        best_tracks.put((distance, track))

    rows = []
    for _ in range(args.limit):
        entry = best_tracks.get()
        rows.append([
            str(entry[1]),
            entry[0],
        ])
    print(tabulate(rows, headers=["track", "score"], numalign="right"))

    return True


def get_tracks_for_category(sp, category):
    tracks = {}
    try:
        playlists = sp.category_playlists(category["id"])["playlists"]["items"]
    except:
        return tracks
    for playlist in playlists:
        tracks.update(
            tracks_for_playlist(sp, playlist["owner"]["id"], playlist["id"])
        )
    return tracks


def cmd_find_new(args):
    sp = track_api.init_spotify(args)

    if args.local_file:
        library_tracks = track_api.get_tracks_from_file(args.local_file)
    else:
        library_tracks = track_api.get_tracks_from_spotify(args)

    average_feature_values = stats.get_average_feature_values(library_tracks)

    categories = sp.categories(country="us")["categories"]["items"]
    for category in categories:
        print()
        print("Category: {}".format(category["name"]))
        tracks = get_tracks_for_category(sp, category)

        best_tracks = PriorityQueue()
        for track in tracks.values():
            distance = track.distance_from_average(average_feature_values)
            best_tracks.put((distance, track))

        rows = []
        for _ in range(args.limit):
            entry = best_tracks.get()
            rows.append([
                str(entry[1]),
                entry[0],
            ])
        print(tabulate(rows, headers=["track", "score"], numalign="right"))

    return True


def main():
    args = parse_args()

    return args.function(args)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
