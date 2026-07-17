import matplotlib.pyplot as plt
import numpy as np
from ..dictionaries.hist_dictionary import HIST_NAME
from ..tools.plotting_helpers import xlabel, ylabel

class Hist:
    # bin edges of the histogram
    edges = 0
    bin_quantity = None
    bin_labels = None
    # values of the histogram
    values = 0
    count_quantity = None
    # uncertainties of the counts
    errors = 0
    errorsUp = None
    errorsLow = None
    
    def __init__(self, ROOTbranch=None, count_quantity=None, bin_quantity=None, scale_for_values=None):
        if ROOTbranch is not None:
            # check if count and bin quantities are given seperately
            #  - if not: take count_quantity as name of the histogram
            #  - if yes: construct the name of the histogram from both
            if bin_quantity is None:
                hist_name = count_quantity
            else:
                hist_name = HIST_NAME(count_quantity, bin_quantity)

            # load the histogram
            TH1 = ROOTbranch[hist_name]

            # fill the histogram information
            self.edges = TH1.axis().edges()
            self.values = TH1.values()
            self.errors = TH1.errors()

            # remember the bin and count quantities
            self.bin_quantity = bin_quantity
            self.count_quantity = count_quantity
            
            # bin_label is a list of strings if the xticks are labeled
            # else, it is None
            self.bin_labels = TH1.axis("x").labels()
            
            # if a scale factor for the values are given (e.g. 1/N_events) apply it to values and errors
            if scale_for_values is not None:
                self.values *= scale_for_values
                self.errors *= scale_for_values

            self.updateErrors()

    def updateErrors(self):
        # set upper and lower error bars if not done so yet
        if self.errorsUp is None:
            self.errorsUp = self.errors
        if self.errorsLow is None:
            self.errorsLow = self.errors

    def plot(self, ax=None, **kwargs):
        self.updateErrors()
        # if bin_labels is not None, assume the prefered plot type is an x-labeled hist
        if self.bin_labels is not None:
            return self.plot_xlabeled_hist(ax, **kwargs)
            
        # else plot an errorbar hist
        else:
            return self.plot_errorbar_hist(ax, **kwargs)

    def plot_errorbar_hist(self, ax=None, **kwargs):
        if ax is None:
            ax = plt.gca()
        handle = ax.errorbar((self.edges[1:] + self.edges[:-1])/2, self.values, yerr=[self.errorsLow, self.errorsUp], xerr=(self.edges[1:] - self.edges[:-1])/2, linestyle="", **kwargs)
        ylabel(self.count_quantity, ax)
        xlabel(self.bin_quantity, ax)
        return handle

    def plot_xlabeled_hist(self, ax=None, **kwargs):
        if ax is None:
            ax = plt.gca()
        xtick_positions = np.arange(len(self.bin_labels))
        handle = ax.bar(xtick_positions, self.values, yerr=self.errors, **kwargs)
        ax.set_xticks(xtick_positions, labels=self.bin_labels, rotation=30, ha='right')
        ylabel(self.count_quantity, ax)
        return handle
    
    def plot_bar_hist(self, ax=None, **kwargs):
        if ax is None:
            ax = plt.gca()
        handle = ax.bar((self.edges[1:] + self.edges[:-1])/2, self.values, **kwargs)
        ylabel(self.count_quantity, ax)
        xlabel(self.bin_quantity, ax)
        return handle

    def get_value_from_label(self, label):
        if self.bin_labels is None:
            return None
        # return the count value given the label that bin
        index = self.bin_labels.index(label)
        return self.values[index]

    def get_error_from_label(self, label):
        if self.bin_labels is None:
            return None
        # return the count value given the label that bin
        index = self.bin_labels.index(label)
        return self.errors[index]