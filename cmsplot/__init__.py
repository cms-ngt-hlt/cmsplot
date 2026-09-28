# A small Python module:
# - for my personal plotting preferences
# - some helper function and classes
#
# Author: Jan Schulz
# Date: January 8 2025
#

# import dictionaries
from .dictionaries.label_dictionary import LABEL_DICT
from .dictionaries.hist_dictionary import HIST_NAME

# import plotting tools
from .tools.plotting_helpers import setStyle, xlabel, ylabel, cmslabel, savefig, lumilabel

# import helpers
from .tools.getRatioHist import getRatioHist
from .tools.getSumHist import getSumHist
from .tools.getDiffHist import getDiffHist

# import Histogram classes
from .histograms.Hist import Hist
from .histograms.Hist2D import Hist2D
