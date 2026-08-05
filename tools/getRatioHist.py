from ..histograms.Hist import Hist
import numpy as np

def getRatioHist(numHist, denomHist = None):
    """
    Calculates the ratio Histogram for two given histograms. The error is calculated via error propagation.
    Note, this does not yield the correct error if an efficiency is wanted!

    If only one histogram is given it computes the ratio with itself.
    """
    ratioHist = Hist()
    ratioHist.edges = numHist.edges
    
    with np.errstate(divide="ignore", invalid="ignore"):
        if denomHist is None:
            ratioHist.values = np.ones_like(numHist.values)
            ratioHist.errors = np.where(numHist.values == 0, 0, numHist.errors / numHist.values)
        else:
            denomIsZero = denomHist.values == 0
            ratioHist.values = np.where(denomIsZero, np.nan, numHist.values / denomHist.values)
            ratioHist.errors = np.where(denomIsZero, 0, np.abs(numHist.values / denomHist.values) * np.sqrt((numHist.errors/numHist.values)**2 + (denomHist.errors/denomHist.values)**2))

    return ratioHist