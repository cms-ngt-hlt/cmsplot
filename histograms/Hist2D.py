import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from ..dictionaries.hist_dictionary import HIST_NAME
from ..tools.plotting_helpers import xlabel, ylabel

class Hist2D:
    # bin edges of the histogram
    edges_x = 0
    bin_quantity_x = None
    bin_labels_x = None
    edges_y = 0
    bin_quantity_y = None
    bin_labels_y = None
    # values of the histogram
    values = 0
    count_quantity = None
    # uncertainties of the counts
    errors = 0
    
    def __init__(self, ROOTbranch, hist_name, count_quantity=None, bin_quantity_x=None, bin_quantity_y=None, scale_for_values=None):
        # load the histogram
        TH2 = ROOTbranch[hist_name]

        # fill the histogram information
        self.edges_x = TH2.axis("x").edges()
        self.edges_y = TH2.axis("y").edges()
        self.values = TH2.values()
        self.errors = TH2.errors()

        # remember the bin and count quantities
        self.bin_quantity_x = bin_quantity_x
        self.bin_quantity_y = bin_quantity_y
        self.count_quantity = count_quantity
        
        # bin_label is a list of strings if the xticks are labeled
        # else, it is None
        self.bin_labels = TH2.axis("x").labels()
        
        # if a scale factor for the values are given (e.g. 1/N_events) apply it to values and errors
        if scale_for_values is not None:
            self.values *= scale_for_values
            self.errors *= scale_for_values

    def plot(self, ax=None, plot_zeros_special=False, **kwargs):
        self.plot_hist2d(ax, plot_zeros_special=plot_zeros_special, **kwargs)

    def plot_hist2d(self, ax=None, plot_zeros_special=False, log=True, **kwargs):
        if ax is None:
            ax = plt.gca()
        # if plot_zeros_special == True, move zeros to negative numbers and fix vmin=0
        if plot_zeros_special:
            if log:
                vmin = np.ma.masked_equal(self.values.T, 0.0, copy=False).min() * 0.999
                vmax = np.max(self.values.T)
                cax = ax.pcolormesh(self.edges_x, self.edges_y, self.values.T, 
                                    norm=LogNorm(vmin=vmin, vmax=vmax), **kwargs)
            else:
                cax = ax.pcolormesh(self.edges_x, self.edges_y, self.values.T - (self.values.T == 0), 
                                        vmin =0, **kwargs)
        else:
            cax = ax.pcolormesh(self.edges_x, self.edges_y, self.values.T, **kwargs)
        xlabel(self.bin_quantity_x, ax)
        ylabel(self.bin_quantity_y, ax)
        ax.xaxis.set_ticks_position('bottom')
        ax.yaxis.set_ticks_position('left')
        return cax

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