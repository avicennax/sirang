#!/usr/bin/env python
# A futile attempt to estimate the mean of a Cauchy

from __future__ import division

import argparse
import math
import random

import sirang


# Declare experiment storage wrapper
experiment = sirang.Sirang()


def sample_cauchy(x0, gamma):
    y = random.random()
    return gamma*(math.tan(math.pi*(y - 1/2.))) + x0


# Decorate function whose parameters you want to capture
@experiment.dstore(
    db_name='mean-estimates', collection_name='cauchy', store_return=True)
def main(num_of_samples, location, scale):
    samples = [sample_cauchy(location, scale) for _ in range(num_of_samples)]
    mean_estimate = sum(samples)/num_of_samples
    print("Cauchy Parameters --")
    print("Location: {}".format(location))
    print("Scale: {}".format(scale))
    print("Mean estimate: {}".format(mean_estimate))
    # Store the result with key: mean_estimate
    return {'mean_estimate': mean_estimate}, _


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estimate mean of Cauchy")
    parser.add_argument(
        '-n', '--num-of-samples', type=int,
        help="Number of samples to generate", required=True)
    parser.add_argument(
        '-l', '--location', type=float, default=0, help="Location parameter")
    parser.add_argument(
        '-s', '--scale', type=float, default=1, help="Scale parameter")
    args = vars(parser.parse_args())
    main(**args)
