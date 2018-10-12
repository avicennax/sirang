#!/usr/bin/env python
# Find local minima of Rosenbrock function and store
# initial guess with solution together.

import argparse

import numpy as np
import scipy.optimize as sciop

import sirang


# Declare experiment storage wrapper
experiment = sirang.Sirang()


# Decorate function whose parameters you want to capture,
# in our case the initial optimization guess.
@experiment.dstore(
    db_name='opt-results',
    collection_name='rosenbrock',
    store_return=True
)
def opt_func(x0):
    """Find local optima of Rosenbrock function."""
    res = sciop.minimize(sciop.rosen, x0, method='Nelder-Mead')
    # MongoDB doesn't like numpy arrays unfortunately.
    x_min = res.x.tolist()
    # Store the result with key: local-opt. Here the first
    # argument will be stored in our DB, and second actually
    # returned to the calling function.
    return {'local-opt': x_min}, x_min


def main(num_of_inits, init_variance):
    """Initial guesses generated from Normal with user specified variance."""
    for n in range(num_of_inits):
        x0 = np.random.normal(0, init_variance, 2).tolist()
        # Positional arguments are not allowed.
        x_min = opt_func(x0=x0)
        print("n: {}, x0: {}, min: {}".format(n, x0, x_min))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find minima of Rosenbrock function via Nelder-Mead.")
    parser.add_argument(
        '-n', '--num-of-inits', type=int,
        help="Number of random initial guesses.", required=True)
    parser.add_argument(
        '-l', '--init-variance', type=float,
        help="Variance of Normal with mean 0, used to generate initial guesses.",
        default=100.0)

    args = vars(parser.parse_args())
    main(**args)
