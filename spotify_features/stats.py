from collections import defaultdict
from itertools import combinations


from matplotlib import pyplot
import numpy


from . import config


class FeatureStatistics(object):

    def __init__(self, values):
        self.values = values
        self.avg = sum(values) / len(values)
        self.std_dev = numpy.std(values)


def get_feature_values(tracks):
    feature_values = defaultdict(list)
    for track in tracks.values():
        for feature in config.FEATURES:
            val = getattr(track.features, feature, None)
            if val is None:
                continue
            feature_values[feature].append(val)
    return feature_values


def get_average_feature_values(tracks):
    average_feature_values = {}
    for feature, values in get_feature_values(tracks).items():
        average_feature_values[feature] = FeatureStatistics(values)
    return average_feature_values


def make_histograms(feature_values):
    print("Building histograms...")
    pyplot.figure(1)
    pyplot.gcf().set_size_inches(20, 100)
    for i, feature in enumerate(config.FEATURES):
        pyplot.subplot(len(config.FEATURES), 1, i + 1)
        pyplot.hist(feature_values[feature], bins='auto')
        pyplot.title(feature)

    pyplot.savefig("histogram.png", dpi=100)


def make_comparison_scatterplots(feature_values):
    print("Building comparison scatterplots...")
    pyplot.figure(1)
    pyplot.gcf().set_size_inches(20, 100)

    comb = list(combinations(config.FEATURES, 2))
    for i, (feature_a, feature_b) in enumerate(comb):
        count = min(
            len(feature_values[feature_a]),
            len(feature_values[feature_b]),
        )
        pyplot.subplot(len(comb), 1, i + 1)
        pyplot.xlabel(feature_a)
        pyplot.ylabel(feature_b)
        pyplot.scatter(
            feature_values[feature_a][:count],
            feature_values[feature_b][:count],
        )

    pyplot.savefig("scatterplot.png", dpi=100)
