import uproot
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.stats import binomtest
from cmsplot import Hist, getRatioHist
import cmsplot as cplt


class DQMPlotter:
    """Base class for DQM validation plotters. Subclasses must set ROOTPATH, FILENAMEPREFIX,
    DATAPATH, DATALABEL, COLLECTIONS, EFFCUTS, and implement loadData()."""

    # Data configuration — subclasses override these
    CONFIGURATIONS = {}
    CONFIGS = []
    NAMES = {}
    CONFIGCOLORS = {}
    DATAPATH = "data"
    FILENAMEPREFIX = "DQM_"
    ROOTPATH = ""
    FILES = {}
    DATA = {}
    COLLECTIONS = {}
    COLLS = {}.keys()

    # Plotting configuration
    DRAFT = False
    CMSLABEL = "Simulation (Private Work)"
    DATALABEL = ""
    OBJECTLABEL = None   # appended as ", <OBJECTLABEL>" in the CMS label when set
    RATIO = True
    EXTENDPLOTNAME = False
    LEGEND = True
    MARKERS = ["s", "^", "D", "v", "o", "."] + ["."] * 30
    PLOTTINGCONFIGURATION = {}
    COLORS = []
    DIR = "plots"
    SAVEAS = ["png"]

    # Cut strings for efficiency plot labels.
    # Keys are histogram name substrings: a cut is excluded when its key appears in the
    # histogram name (i.e. that variable is on the x-axis). Set a value to None to suppress it.
    EFFCUTS = {}
    # Appended only for techEff histograms (additive cut, not x-axis exclusion). None = suppress.
    CUT_TECHEFF = None

    def __init__(self, CONFIGURATIONS={}, COLLECTIONS={}, DATAPATH=None):
        self.updateConfiguration(
            CONFIGURATIONS=CONFIGURATIONS,
            COLLECTIONS=COLLECTIONS,
            DATAPATH=DATAPATH,
        )
        self.loadData()

    def updateConfiguration(self, CONFIGURATIONS={}, COLLECTIONS={}, DATAPATH=None):
        """Merge new run configurations and/or collections into the current setup."""
        if CONFIGURATIONS:
            self.CONFIGURATIONS = self.CONFIGURATIONS | CONFIGURATIONS
        if COLLECTIONS:
            self.COLLECTIONS = self.COLLECTIONS | COLLECTIONS
            self.COLLS = self.COLLECTIONS.keys()
        if DATAPATH:
            self.DATAPATH = DATAPATH

        self.CONFIGS = list(self.CONFIGURATIONS.keys())
        self.NAMES = {k: v[1] for k, v in self.CONFIGURATIONS.items()}
        self.CONFIGCOLORS = {k: v[0] for k, v in self.CONFIGURATIONS.items()}
        self.FILES = {
            config: uproot.open(
                "%s/%s%s.root" % (self.DATAPATH, self.FILENAMEPREFIX, config)
            )[self.ROOTPATH]
            for config in self.CONFIGS
        }
        self.DATA = {config: {} for config in self.CONFIGS}

    def setPlottingConfiguration(
        self,
        PLOTTINGCONFIGURATION="",
        DRAFT=False,
        CMSLABEL="Simulation (Private Work)",
        DATALABEL=None,
        OBJECTLABEL=None,
        EFFCUTS=None,
        CUT_TECHEFF=...,
        RATIO=True,
        EXTENDPLOTNAME=False,
        LEGEND=True,
        DIR=None,
        SAVEAS=["png"],
        MARKERS=["s", "^", "D", "v", "o", "."] + ["."] * 30,
        CUSTOMIZESTYLE=False,
    ):
        """Set the plotting configuration. PLOTTINGCONFIGURATION can be:
        - a dict: label -> [configtag, collectiontag]
        - a list: of [configtag, collectiontag] pairs (labels filled from NAMES)
        - a string: collectiontag (one line per config in CONFIGURATIONS)
        """
        if isinstance(PLOTTINGCONFIGURATION, dict):
            self.PLOTTINGCONFIGURATION = PLOTTINGCONFIGURATION
        elif isinstance(PLOTTINGCONFIGURATION, list):
            self.PLOTTINGCONFIGURATION = {
                self.NAMES[k[0]]: k for k in PLOTTINGCONFIGURATION
            }
        elif PLOTTINGCONFIGURATION in self.COLLS:
            self.PLOTTINGCONFIGURATION = {
                self.NAMES[k]: [k, PLOTTINGCONFIGURATION] for k in self.CONFIGS
            }
        else:
            raise ValueError("PLOTTINGCONFIGURATION is unset or wrongly set.")

        self.DRAFT = DRAFT
        self.CMSLABEL = CMSLABEL
        if DATALABEL is not None:
            self.DATALABEL = DATALABEL
        if OBJECTLABEL is not None:
            self.OBJECTLABEL = OBJECTLABEL
        if EFFCUTS is not None:
            self.EFFCUTS = {**self.EFFCUTS, **EFFCUTS}
        if CUT_TECHEFF is not ...:
            self.CUT_TECHEFF = CUT_TECHEFF
        self.RATIO = RATIO
        self.EXTENDPLOTNAME = EXTENDPLOTNAME
        self.LEGEND = LEGEND
        if DIR is not None:
            self.DIR = DIR
        self.SAVEAS = SAVEAS
        self.MARKERS = MARKERS
        self.COLORS = [
            self.CONFIGCOLORS[self.PLOTTINGCONFIGURATION[c][0]]
            for c in self.PLOTTINGCONFIGURATION.keys()
        ]

        cplt.setStyle(CUSTOMIZESTYLE)

    def loadData(self):
        raise NotImplementedError

    def _datalabel(self, histoName):
        """Build the right-side CMS label string for the given histogram.

        For non-efficiency histograms returns DATALABEL (+ OBJECTLABEL if set).
        For efficiency histograms, appends a line of cut strings from EFFCUTS,
        excluding the cut whose key matches the x-axis variable in histoName.
        CUT_TECHEFF is additionally appended for techEff histograms.
        """
        ISEFF = ("eff" in histoName) or ("techEff" in histoName)
        ISTECHEFF = "techEff" in histoName

        header = self.DATALABEL
        if self.OBJECTLABEL:
            header += ", " + self.OBJECTLABEL
        if not ISEFF:
            return header

        cuts = [v for k, v in self.EFFCUTS.items() if k not in histoName and v is not None]
        if ISTECHEFF and self.CUT_TECHEFF is not None:
            cuts.append(self.CUT_TECHEFF)
        cuts_str = ", ".join(cuts)
        return header + ("\n" + cuts_str if cuts_str else "")

    def getEfficiency(self, passing, total):
        yEff, yEffErrUp, yEffErrLow = [], [], []
        for yPass, yTot in zip(passing, total):
            if yTot > 0:
                result = binomtest(k=int(yPass), n=int(yTot))
                yEff.append(result.statistic)
                yEffErrLow.append(result.proportion_ci(0.683).low)
                yEffErrUp.append(result.proportion_ci(0.683).high)
            else:
                yEff.append(0)
                yEffErrLow.append(0)
                yEffErrUp.append(0)
        return np.array(yEff), np.array(yEffErrLow), np.array(yEffErrUp)

    def getDiffHist(self, Hist1, Hist2=None):
        """Difference histogram with error propagation. Not correct for efficiencies."""
        sumHist = Hist()
        sumHist.edges = Hist1.edges
        if Hist2 is None:
            sumHist.values = 0 * Hist1.values
            sumHist.errors = Hist1.errors
        else:
            sumHist.values = Hist1.values - Hist2.values
            sumHist.errors = np.sqrt(Hist1.errors**2 + Hist2.errors**2)
        return sumHist

    def isLogScale(self, edges, rtol=1e-5):
        return abs((edges[-1] / edges[-2]) - (edges[1] / edges[0])) < rtol

    def plotHistogram(
        self,
        histoName="",
        yLim=(None, None),
        xLim=(None, None),
        xLabel=None,
        yLabel=None,
        yScale=None,
        xScale=None,
        ratioType="ratio",
        ratioYLim=(None, None),
        factor=None,
        limitYTicks=False,
    ):
        ISEFF = ("eff" in histoName) or ("techEff" in histoName)

        ADDPLACE = (0.8 if ISEFF else 0.6) if self.RATIO else (0.65 if ISEFF else 0.54)

        if self.RATIO:
            fig, (ax1, ax2) = plt.subplots(2, sharex=True, height_ratios=[5, 1], figsize=(10, 11))
        else:
            fig, ax1 = plt.subplots(1, figsize=(10, 10))

        plotname = histoName

        for i, label in enumerate(self.PLOTTINGCONFIGURATION.keys()):
            config = self.PLOTTINGCONFIGURATION[label][0]
            coll = self.PLOTTINGCONFIGURATION[label][1]

            if self.EXTENDPLOTNAME:
                plotname += ("_" + coll + "_" + config) if i == 0 else ("_vs_" + config)

            if histoName not in self.DATA[config][coll]:
                self.DATA[config][coll][histoName] = Hist(
                    self.FILES[config][self.COLLECTIONS[coll]], histoName
                )

            theHist = self.DATA[config][coll][histoName]
            theHist.plot(ax=ax1, marker=self.MARKERS[i], color=self.COLORS[i], label=label)

            if self.RATIO:
                if i == 0:
                    refHist = self.DATA[config][coll][histoName]
                    if ratioType == "ratio":
                        base = getRatioHist(refHist)
                        ax2.axhline(1, linestyle="dashed", color=self.COLORS[0])
                        base = ax2.stairs(
                            1 + base.errors / 2, base.edges,
                            baseline=1 - base.errors / 2, fill=True, alpha=0.25, color=self.COLORS[0],
                        )
                    else:
                        base = self.getDiffHist(refHist)
                        ax2.axhline(0, linestyle="dashed", color=self.COLORS[0])
                        base = ax2.stairs(
                            base.errors / 2, base.edges,
                            baseline=base.errors / 2, fill=True, alpha=0.25, color=self.COLORS[0],
                        )
                else:
                    if ratioType == "ratio":
                        ratioHist = getRatioHist(theHist, refHist)
                    else:
                        ratioHist = self.getDiffHist(theHist, refHist)
                    ratioHist.plot(marker=self.MARKERS[i], color=self.COLORS[i], ax=ax2)

        handles, labels = ax1.get_legend_handles_labels()
        if self.RATIO:
            handles[0] = (handles[0], base)
        order = list(range(len(self.PLOTTINGCONFIGURATION.keys())))
        handles = [handles[idx] for idx in order]
        labels = [labels[idx] for idx in order]

        if self.LEGEND:
            ax1.legend(
                handles, labels, loc="upper left",
                bbox_to_anchor=(
                    0.025,
                    (0.78 if ISEFF else 0.84) if self.RATIO else (0.8 if ISEFF else 0.86),
                ),
                handletextpad=0.25, ncols=2, columnspacing=0.8,
            )

        cplt.xlabel(None, ax=ax1)
        ax = ax2 if self.RATIO else ax1
        if xLabel is None:
            if "Eta" in histoName:
                cplt.xlabel("eta", ax=ax)
            elif "Pt" in histoName:
                cplt.xlabel("pt", ax=ax)
        else:
            cplt.xlabel(xLabel, ax=ax)

        if yLabel is not None:
            cplt.ylabel(yLabel, ax=ax1)
        if self.RATIO:
            cplt.ylabel("Ratio" if ratioType == "ratio" else "Difference", loc="top", ax=ax2)

        if ("Pt" in histoName) or (xScale == "log"):
            plt.xscale("log")

        if yLim[0] is None and yScale is None:
            yLim = (ax1.get_ylim()[0], yLim[1])
        if yLim[1] is None:
            yLim = (yLim[0], ax1.get_ylim()[1])
        if yScale is not None:
            ax1.set_yscale(yScale)
            if yLim[0] is None:
                yLim = (ax1.get_ylim()[0], yLim[1])
            yLimTrue = [yLim[0], yLim[1] * 10 ** (np.log10(yLim[1] / yLim[0]) * ADDPLACE)]
        else:
            yLimTrue = [yLim[0], yLim[1] + ADDPLACE * (yLim[1] - yLim[0])]
        ax1.set_ylim(yLimTrue)
        ax1.set_xlim(xLim)

        if limitYTicks:
            ytickslocs = ax1.get_yticks()
            ax1.set_yticks([y for y in ytickslocs if 0 <= y <= 1])
            ytickslocs = ax1.get_yticks()
            yticklabels = ax1.get_yticklabels()
            ax1.set_yticklabels([
                yl if y != 1 else ("1" if yScale == "log" else "1.0")
                for y, yl in zip(ytickslocs, yticklabels)
            ])
            ax1.set_yticks(
                [y for y in ax1.get_yticks(minor=True) if 0 <= y <= 1], minor=True
            )

        ax1.grid(True)

        if self.RATIO:
            ax2.set_ylim(ratioYLim)
            ax2.grid(True)
            ylim = ax2.get_ylim()
            dy = ylim[1] - ylim[0]
            yup = ylim[1] - dy / 50
            ylo = ylim[0] + dy / 50
            for i, label in enumerate(self.PLOTTINGCONFIGURATION.keys()):
                config = self.PLOTTINGCONFIGURATION[label][0]
                coll = self.PLOTTINGCONFIGURATION[label][1]
                theHist = self.DATA[config][coll][histoName]
                if i == 0:
                    xpos = (theHist.edges[1:] + theHist.edges[:-1]) / 2
                else:
                    ratioHist = (
                        getRatioHist(theHist, refHist)
                        if ratioType == "ratio"
                        else self.getDiffHist(theHist, refHist)
                    )
                    mask = ratioHist.values < ylim[0]
                    ax2.scatter(xpos[mask], ylo * np.ones(np.sum(mask)), marker="v",
                                color=self.COLORS[i], facecolors="none", sizes=30 * np.ones(np.sum(mask)))
                    mask = ratioHist.values > ylim[1]
                    ax2.scatter(xpos[mask], yup * np.ones(np.sum(mask)), marker="^",
                                color=self.COLORS[i], facecolors="none", sizes=30 * np.ones(np.sum(mask)))

        if factor is not None:
            if yScale == "log":
                ticks = mpl.ticker.FuncFormatter(
                    lambda x, pos: r"$10^{" + "%i" % np.log10(x * factor) + r"}$"
                )
            else:
                ticks = mpl.ticker.FuncFormatter(lambda x, pos: "{0:g}".format(x * factor))
            ax1.yaxis.set_major_formatter(ticks)

        if self.DRAFT:
            ax1.text(0.5, 0.5, "DRAFT", transform=ax1.transAxes,
                     fontsize=150, color="gray", alpha=0.25,
                     ha="center", va="center", rotation=30)

        exptext, expsuffix, supptext, explumi = cplt.cmslabel(
            llabel=self.CMSLABEL, rlabel=self._datalabel(histoName), ax=ax1, loc=4
        )
        explumi.set_fontsize(explumi.get_fontsize() / 1.25)

        plt.subplots_adjust(hspace=0.0)
        for saveas in self.SAVEAS:
            cplt.savefig(self.DIR + "/%s.%s" % (plotname, saveas))
        plt.show()
