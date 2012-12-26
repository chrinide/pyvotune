# -*- coding: utf-8 -*-

"""
    pyvotune.genome
    --------------------------

    This module defines the Genome class which represents one genetic
    identity and can be translated (assembled) into an individual
"""

from pyvotune.log import logger
from pyvotune.assembly_state import AssemblyState

from pyvotune.pyvotune_globals import NOOP_GENE


class Genome:
    def __init__(self, genome_id):
        self.log = logger()
        self.genome_id = genome_id
        self.param_vals = []
        self.genes = []
        self.state = AssemblyState()

        self.assembled = None

        self.log.debug(
            u"G{0}: Instantiated new genome".format(self.genome_id))

    def add_gene(self, param_vals, gene):
        """
        Adds a gene and it's parameters to the current genome
        """
        self.param_vals += param_vals
        self.genes.append(gene)

        self.state.gene_update(gene)

        self.log.debug(
            u"G{0}: Added new gene {1}".format(self.genome_id, gene))

    def does_gene_fit(self, gene):
        """
        Checks if a gene would fit into the current genome given the
        existing assembly state
        """
        return self.state.is_gene_avail(gene)

    def validate(self):
        """
        Validates the current genome, swallows all exceptions and
        simply fails assembly if there are problems
        """
        try:
            return self._assemble(assemble=False)
        except:
            self.log.exception(
                u"G{0}: Assembly hard excepted, failing".format(
                    self.genome_id))
            return False

    def assemble(self):
        """
        Assembles the current genome, swallows all exceptions and
        simply fails assembly if there are problems
        """
        try:
            return self._assemble()
        except:
            self.log.exception(
                u"G{0}: Assembly hard excepted, failing".format(
                    self.genome_id))
            return False

    def _assemble(self, assemble=True):
        """
        Actual work function that validates with optional assembly step
        """
        to_assemble = []
        remaining_param_vals = list(self.param_vals)

        active_genes = [g for g in self.genes if g != NOOP_GENE]
        num_active = len(active_genes)

        self.state.clear()

        for i, gene in enumerate(active_genes):
            if not self.does_gene_fit(gene):
                self.log.warning(
                    u"G{0}: Invalid - Gene does not fit in current state {1} {2}".format(
                        self.genome_id, gene, self.state))
                return False

            gene_params = self.get_gene_params(gene)
            num_gene_params = len(gene_params)

            if num_gene_params > len(remaining_param_vals):
                self.log.debug(
                    u"G{0}: Invalid - Not enough remaining parameters ({1} < {2})".format(
                        self.genome_id, num_gene_params, len(remaining_param_vals)))

                return False

            gene_param_vals = remaining_param_vals[:num_gene_params]
            remaining_param_vals = remaining_param_vals[num_gene_params:]

            for i, (param, val) in enumerate(zip(gene_params, gene_param_vals)):
                if not param.check(val):
                    self.log.debug(
                        u"G{0}: Invalid - Parameter {1} failed assembly".format(
                            self.genome_id, i))

                    return False

            to_assemble.append((gene, gene_param_vals))
            self.state.gene_update(gene)

        if assemble:
            self.assembled = [
                self.construct_gene(g, p) for g, p in to_assemble]

            self.log.debug(
                u"G{0}: Assembled successfully".format(self.genome_id))
        return True

    def construct_gene(self, gene, param_vals):
        """
        Returns an instantiated gene given the values to pass to it's constructor/factory meth
        """
        cons = gene
        if hasattr(gene, '_pyvotune_assembly_params') and\
                'factory_fn' in gene._pyvotune_assembly_params:
            cons = gene._pyvotune_assembly_params['factory_fn']

        self.log.debug(u"G{0}: Instantiating gene {1} with {2}".format(
            self.genome_id, gene, param_vals))
        return cons(*param_vals)

    def get_gene_params(self, gene):
        if not hasattr(gene, '_pyvotune_params'):
            return []
        return gene._pyvotune_params
