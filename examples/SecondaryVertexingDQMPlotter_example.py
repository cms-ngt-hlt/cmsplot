"""Example: HLT secondary-vertex DQM validation with SecondaryVertexingDQMPlotter.

Like TrackingDQMPlotter_example.ipynb, this needs real CMS DQM ROOT files and
won't run out of the box. It expects, relative to the current working
directory:

    data/DQM_General_<tag>.root

for every <tag> used in CONFIGURATIONS below, each containing the path
DQMData/Run 1/HLT/Run summary/SecondaryVertices/Validation
(the standard layout produced by the CMS secondary-vertex DQM harvesting
step). Adjust CONFIGURATIONS, DATAPATH, or FILENAMEPREFIX to match your own
files - see SecondaryVertexingDQMPlotter's docstring for details.
"""

from cmsplot.dqm import SecondaryVertexingDQMPlotter

plotter = SecondaryVertexingDQMPlotter(
    CONFIGURATIONS={
        #    tag          color       legend label
        "baseline": ["#e41a1c", "IVF baseline"],
        "new":      ["#377eb8", "IVF tuned"],
    },
)

plotter.setPlottingConfiguration(
    PLOTTINGCONFIGURATION="IVF",
    CMSLABEL="Simulation (Private Work)",
    DIR="plots/SV",
    SAVEAS=["png", "pdf"],
)

# see what's available before plotting
plotter.listHistograms()

# efficiency vs 3D decay length - cut labels are added automatically
plotter.plotHistogram(
    "effVsDecayLength",
    yLim=(0.0, 1.05),
    ratioYLim=(0.95, 1.05),
    limitYTicks=True,
)

# fake rate vs eta
plotter.plotHistogram("fakeVsEta", yLim=(0.0, 0.5))

# stacked simulated-vertex composition by decay type (b/c/s/tau)
plotter.plotStackedHistogramOfDecayTypes(
    xName="decayLength",
    xLabel=r"Simulated vertex 3D decay length $L_{3D}$ [cm]",
    xLim=(1e-3, 20),
)
