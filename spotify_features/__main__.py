import argparse
from queue import PriorityQueue
import sys


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

    min_distance = float("inf")
    best_tracks = PriorityQueue()
    for track in tracks.values():
        distance = track.distance_from_average(average_feature_values)
        best_tracks.put((distance, track))

    for _ in range(args.limit):
        print(best_tracks.get()[1])

    return True


def main():
    args = parse_args()

    return args.function(args)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
