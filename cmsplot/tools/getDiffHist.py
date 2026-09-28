from ..histograms.Hist import Hist
import numpy as np

def getDiffHist(Hist1, Hist2):
    """
    Calculates the difference Histogram for two given histograms. The error is calculated via error propagation.
    Note, this does not yield the correct error if an efficiency is wanted!
    """
    sumHist = Hist()
    sumHist.edges = Hist1.edges

    sumHist.values = Hist1.values - Hist2.values
    sumHist.errors = np.sqrt((Hist1.errors)**2 + (Hist2.errors)**2)

    return sumHist
