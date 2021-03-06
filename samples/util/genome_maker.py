# -*- coding: utf-8 -*-

import pyvotune
import collections
import pyvotune.sklearn
import random
import copy
import sys

log = pyvotune.log.logger()


def reproduce(offspring_cs, variator, rng, args):
    if isinstance(variator, collections.Iterable):
        for op in variator:
            offspring_cs = op(random=rng, candidates=offspring_cs, args=args)

        return offspring_cs
    else:
        return [variator(random=rng, candidates=offspring_cs, args=args)]


if __name__ == '__main__':
    pyvotune.set_debug(True)

    # Dummy data
    n_features = 28 * 28

    rng = random.Random()
    gene_pool = pyvotune.sklearn.get_classifiers(n_features, rng) +\
        pyvotune.sklearn.get_preprocessors(n_features, rng) + \
        pyvotune.sklearn.get_decomposers(n_features, rng) +\
        pyvotune.sklearn.get_image_features(n_features, rng) +\
        pyvotune.sklearn.get_pyrbm(n_features, rng)

    #################################
    # Initialize PyvoTune Generator #
    #################################
    gen = pyvotune.Generate(
        initial_state={
            'sparse': False
        },
        gene_pool=gene_pool,
        max_length=4,
        noop_frequency=0.2,
        rng=rng)

    args = {
        'crossover_rate': 0.5,
        'mutation_rate': 0.3,
        'pyvotune_generator': gen
    }

    # Use PyvoTun variators
    variators = [
        pyvotune.variators.random_reset_mutation,
        pyvotune.variators.param_reset_mutation,
        pyvotune.variators.scramble_mutation,
        pyvotune.variators.uniform_crossover,
        pyvotune.variators.n_point_crossover
    ]

    parents = []
    for i in range(2):
        parent = gen.generate(max_retries=150)
        parents.append(parent)

    first_gen_paernts = copy.copy(parents)

    stats = collections.defaultdict(int)

    for j in range(10):
        log.info("GENERATION %s" % j)

        orig_parents = copy.copy(parents)

        #log.debug("Done generating parents")

        rep = pyvotune.util.side_by_side(parents, 50)
        #log.debug("\nParents:\n%s\n" % rep)

        reproduction_parents = random.sample(parents, 2)

        for i in range(100):
            children = reproduce(reproduction_parents, variators, rng, args)
            child_rep = pyvotune.util.side_by_side(children, 50)
            #log.debug("\nChildren:\n%s\n" % child_rep)

            stats = pyvotune.util.child_stats(parents, children, stats)

        if orig_parents != parents:
            log.error("PARENTS CHANGED")

        parents += children

    for key, value in stats.iteritems():
        log.debug("%s: %s" % (key, value))


    #rep = pyvotune.util.side_by_side(parents, 50)
    #log.debug("\nParents:\n%s\n" % rep)
