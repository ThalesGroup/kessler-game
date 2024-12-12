# -*- coding: utf-8 -*-
# Copyright © 2022 Thales. All Rights Reserved.
# NOTICE: This file is subject to the license agreement defined in file 'LICENSE', which is part of
# this source code package.

import numpy as np
import random

from deap import base
from deap import creator
from deap import tools
from deap import algorithms

from example_fitness_function import exampleFitness

# orginal fitness function from DEAP onemax example
# def evalOneMax(individual):
#     # print("test", individual[:2])
#     # print(type(individual))
#     return sum(individual),


def main():
    # createing individual and fitness characteristics/types
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    # Attribute generator
    # creating a float attribute - this will be the encoding of the GA individuals so all of the DNA in a chromosome will be floats
    # The random component is to initialize the population with random values
    toolbox.register("attr_flt1", random.uniform, 0.0, 1.0)
    # Structure initializers
    # this registers an individual as an iterable of 50 values where each value is using the float attribute we just defined above
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     toolbox.attr_flt1, 50)
    # this creates our population by creating a list of the individuals as defined above
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # here we register our custom fitness function that we import above - in the DEAP onemax example this is where "evalOneMax" would be passed instead
    toolbox.register("evaluate", exampleFitness)
    # Defining what type of crossover will be used
    toolbox.register("mate", tools.cxTwoPoint)
    # defining what type of mutation will be used - in this case our encoding is floats so we're using Gaussian - we could use other methods
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.2, indpb=0.05)
    # defining how selection is performed - we use tournament selection like the DEAP onemax example
    toolbox.register("select", tools.selTournament, tournsize=3)

    # creating a population - in this case we only have 20 individuals in our population
    pop = toolbox.population(n=20)

    # Evaluate the entire population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.5, 0.2

    # Extracting all the fitnesses of
    fits = [ind.fitness.values[0] for ind in pop]

    # Variable keeping track of the number of generations
    g = 0

    # Begin the evolution
    while g < 1000:
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring

        # Gather all the fitnesses in one list and print the stats
        fits = [ind.fitness.values[0] for ind in pop]

        length = len(pop)
        mean = sum(fits) / length
        sum2 = sum(x * x for x in fits)
        std = abs(sum2 / length - mean ** 2) ** 0.5

        print("  Min %s" % min(fits))
        print("  Max %s" % max(fits))
        print("  Avg %s" % mean)
        print("  Std %s" % std)

if __name__ == "__main__":
    main()