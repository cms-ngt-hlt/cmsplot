import numpy as np
import matplotlib.pyplot as plt
from cmsplot import Hist
import cmsplot as cplt
from .DQMPlotter import DQMPlotter


class SecondaryVertexingDQMPlotter(DQMPlotter):
    DATAPATH = "data"
    FILENAMEPREFIX = "DQM_General_"
    ROOTPATH = "DQMData/Run 1/HLT/Run summary/SecondaryVertices/Validation"
    DATALABEL = r"$\text{t}\bar{\text{t}}$ + 200 PU ($\sqrt{s} = 14\,\text{TeV}$)"
    OBJECTLABEL = "HLT secondary vertices"
    DIR = "plots/SVValidation"
    COLLECTIONS = {
        "IVF": "hltDeepInclusiveMergedVerticesPF",
    }
    COLLS = COLLECTIONS.keys()
    DECAYCOLORS = {
        "b": "#00272B", "c": "#1098F7", "s": "#C0F5FA", "tau": "#BA274A", "other": "#B79FAD",
    }
    DECAYLABELS = {
        "b": "b-hadrons", "c": "c-hadrons", "s": "s-hadrons", "tau": "τ", "other": "others",
    }
    # Cut strings used to build efficiency plot labels.
    # Keys are substrings of histogram names: a cut is excluded from the label when its
    # key appears in the histogram name (i.e. that variable is on the x-axis).
    # Set a value to None to suppress that cut in all labels.
    # Pass EFFCUTS={...} to setPlottingConfiguration to override individual entries.
    EFFCUTS = {
        "Pdg":         r"B/D/s/τ decays",
        "Pt":          r"$p_T>10\,GeV$",
        "DecayLength": r"$100\,\text{µm} < L_{3D} < 20 \,\text{cm}$",
        "NTracks":     r"$N_{daughters} \geq 2$",
    }
    # Appended only for techEff histograms (additive cut, not x-axis exclusion).
    # Set to None to suppress.
    CUT_TECHEFF = r"$N_{tracks} \geq 2$"

    def makeMetricDict(self, rootdir, variable, include_eff=True):
        """Build {metricKey: Hist} for a given x-axis variable."""
        metrics = {"fake": "fakeRate", "dup": "duplicateRate", "pileup": "pileupRate"}
        if include_eff:
            metrics = {"eff": "effic", "techEff": "techEffic", "merge": "mergeRate", **metrics}
        return {
            f"{key}Vs{variable[0].upper()}{variable[1:]}": Hist(rootdir, f"{histoPrefix}_vs_{variable}")
            for key, histoPrefix in metrics.items()
        }

    def makeResolutionDict(self, rootdir, variable, include_eta=False):
        """Build {metricKey: Hist} for resolution quantities."""
        metrics = {
            "BiasVsNTracks":      "_res_vs_nTracks_Mean",
            "ResVsNTracks":       "_res_vs_nTracks_Sigma",
            "BiasVsDecayLength":  "_res_vs_decayLength_Mean",
            "ResVsDecayLength":   "_res_vs_decayLength_Sigma",
        }
        if include_eta:
            metrics = {"BiasVsEta": "_res_vs_eta_Mean", "ResVsEta": "_res_vs_eta_Sigma", **metrics}
        return {
            f"{variable}{key}": Hist(rootdir, f"{variable}{suffix}")
            for key, suffix in metrics.items()
        }

    def loadData(self):
        variables_with_eff    = ["decayLength", "decayLengthXY", "eta", "pt", "mass", "nTracks"]
        variables_without_eff = ["decayLengthSig", "chi2ndof"]
        variables_with_res    = variables_with_eff[:-1] + ["phi", "x", "y", "z"]

        for config in self.CONFIGS:
            for coll in self.COLLS:
                colldir = self.COLLECTIONS[coll]
                if (colldir + ";1") not in self.FILES[config].keys():
                    continue
                self.DATA[config][coll] = {
                    "nSVs":                       Hist(self.FILES[config][colldir], "numRecoSVs"),
                    "nAllSimSVs":                 Hist(self.FILES[config][colldir], "numSimSVsAll"),
                    "nSignalSimSVs":              Hist(self.FILES[config][colldir], "numSimSVsSignal"),
                    "trackEff":                   Hist(self.FILES[config][colldir], "trackEfficiency"),
                    "trackEffVsDecayLength":      Hist(self.FILES[config][colldir], "trackEfficiencyProfile_vs_decayLength"),
                    "trackEffVsNTracksRecoSV":    Hist(self.FILES[config][colldir], "trackEfficiencyProfile_vs_nTracksRecoSV"),
                    "trackEffVsNTracksSimSV":     Hist(self.FILES[config][colldir], "trackEfficiencyProfile_vs_nTracksSimSV"),
                    "trackPurity":                Hist(self.FILES[config][colldir], "trackPurity"),
                    "trackPurityVsDecayLength":   Hist(self.FILES[config][colldir], "trackPurityProfile_vs_decayLength"),
                    "trackPurityVsNTracksRecoSV": Hist(self.FILES[config][colldir], "trackPurityProfile_vs_nTracksRecoSV"),
                    "trackPurityVsNTracksSimSV":  Hist(self.FILES[config][colldir], "trackPurityProfile_vs_nTracksSimSV"),
                    "trackNSharedTracks":         Hist(self.FILES[config][colldir], "nSharedTracks"),
                }
                for variable in variables_with_eff:
                    self.DATA[config][coll].update(self.makeMetricDict(self.FILES[config][colldir], variable))
                for variable in variables_without_eff:
                    self.DATA[config][coll].update(self.makeMetricDict(self.FILES[config][colldir], variable, include_eff=False))
                for variable in variables_with_res:
                    self.DATA[config][coll].update(self.makeResolutionDict(self.FILES[config][colldir], variable))

    def plotStackedHistogramOfDecayTypes(
        self,
        config=None,
        xName="decayLengthXY",
        yName="sim",
        decayTypes=["b", "c", "s", "tau"],
        coll="IVF",
        xLabel=r"Simulated vertex 3D decay length $L_{3D}$ [cm]",
        yLabel="Number of simulated signal vertices",
        xLim=(None, None),
    ):
        if config is None:
            config = self.CONFIGS[0]
        plotname = "num_%s_vs_%s" % (yName, xName)

        fig, ax = plt.subplots(1, figsize=(10, 10))
        baseline = None
        for decayType in decayTypes:
            h = Hist(self.FILES[config][self.COLLECTIONS[coll]], "num_%s_%s_%s" % (yName, decayType, xName))
            if baseline is None:
                baseline = np.zeros_like(h.values)
            ax.stairs(h.values + baseline, h.edges, fill=True, baseline=baseline,
                      color=self.DECAYCOLORS[decayType], label=self.DECAYLABELS[decayType])
            baseline += h.values

        ax.set_xlabel(xLabel)
        ax.set_ylabel(yLabel)
        if self.isLogScale(h.edges):
            ax.set_xscale("log")
        ax.legend(title="Decay types", title_fontsize=20, loc="upper right",
                  bbox_to_anchor=(0.98, 0.78), handletextpad=0.25)

        ylim = ax.get_ylim()
        ax.set_ylim([ylim[0], ylim[1] + 0.65 * (ylim[1] - ylim[0])])
        ax.set_xlim(xLim)

        exptext, expsuffix, supptext, explumi = cplt.cmslabel(
            llabel=self.CMSLABEL, rlabel=self.DATALABEL, ax=ax, loc=4
        )
        explumi.set_fontsize(explumi.get_fontsize() / 1.25)

        for saveas in self.SAVEAS:
            cplt.savefig(self.DIR + "/%s.%s" % (plotname, saveas))
        plt.show()
