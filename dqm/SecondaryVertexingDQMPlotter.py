import numpy as np
import matplotlib.pyplot as plt
from cmsplot import Hist
import cmsplot as cplt
from .DQMPlotter import DQMPlotter


class SecondaryVertexingDQMPlotter(DQMPlotter):
    """DQM validation plotter for CMS HLT secondary vertex reconstruction.

    Reads secondary-vertexing validation ROOT files produced by the CMS DQM
    framework and provides efficiency, fake-rate, duplicate-rate, pileup-rate,
    merge-rate, resolution, and track-quality histograms for the IVF (Inclusive
    Vertex Finder) collection.

    The single collection available by default is:

    - ``"IVF"`` — ``hltDeepInclusiveMergedVerticesPF``

    ROOT files are expected at ``data/DQM_General_<tag>.root``, inside the path
    ``DQMData/Run 1/HLT/Run summary/SecondaryVertices/Validation``.

    Efficiency plots show the active selection cuts automatically.  The cut on the
    x-axis variable is excluded via ``EFFCUTS`` keys:

    - ``"Pdg"``         — always shown: B/D/s/τ signal decays
    - ``"Pt"``          — suppressed on pT plots: ``pT > 10 GeV``
    - ``"DecayLength"`` — suppressed on decay-length plots: ``100 μm < L3D < 20 cm``
    - ``"NTracks"``     — suppressed on track-multiplicity plots: ``Ndaughters ≥ 2``

    For technical-efficiency histograms (``techEff``), an additional cut
    ``Ntracks ≥ 2`` is appended via ``CUT_TECHEFF``.

    Example::

        plotter = SecondaryVertexingDQMPlotter(
            CONFIGURATIONS={
                "baseline": ["#e41a1c", "IVF baseline"],
                "new":      ["#377eb8", "IVF tuned"],
            },
        )
        plotter.setPlottingConfiguration(
            PLOTTINGCONFIGURATION="IVF",
            DIR="plots/SV",
            SAVEAS=["png", "pdf"],
        )
        plotter.plotHistogram("effVsDecayLength", yLim=(0.0, 1.0), limitYTicks=True)
        plotter.plotStackedHistogramOfDecayTypes(xName="decayLength")
    """
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
        """Build a ``{metricKey: Hist}`` dict of rate histograms for one x-axis variable.

        Constructs histogram keys of the form ``"<metric>Vs<Variable>"`` (e.g.
        ``"effVsDecayLength"``) and loads the corresponding ``Hist`` objects from
        the ROOT directory.

        Args:
            rootdir: uproot directory object for the current collection.
            variable (str): x-axis variable name as it appears in the ROOT histogram
                name, e.g. ``"decayLength"``, ``"eta"``, ``"pt"``.
            include_eff (bool): If ``True`` (default), include efficiency
                (``"eff"``), technical efficiency (``"techEff"``), and merge-rate
                (``"merge"``) histograms in addition to the fake, duplicate, and
                pileup rates.  Set to ``False`` for variables where efficiency is
                not defined (e.g. ``"chi2ndof"``).

        Returns:
            dict[str, Hist]: Mapping from histogram key to loaded histogram.
        """
        metrics = {"fake": "fakeRate", "dup": "duplicateRate", "pileup": "pileupRate"}
        if include_eff:
            metrics = {"eff": "effic", "techEff": "techEffic", "merge": "mergeRate", **metrics}
        return {
            f"{key}Vs{variable[0].upper()}{variable[1:]}": Hist(rootdir, f"{histoPrefix}_vs_{variable}")
            for key, histoPrefix in metrics.items()
        }

    def makeResolutionDict(self, rootdir, variable, include_eta=False):
        """Build a ``{metricKey: Hist}`` dict of resolution histograms for one quantity.

        Constructs histogram keys of the form ``"<variable><Metric>"`` (e.g.
        ``"xResVsNTracks"``) using the mean and sigma of pull/residual profiles
        stored in the ROOT file.

        Args:
            rootdir: uproot directory object for the current collection.
            variable (str): Quantity name as it appears in the ROOT histogram
                prefix, e.g. ``"x"``, ``"y"``, ``"z"``, ``"phi"``, ``"decayLength"``.
            include_eta (bool): If ``True``, also include ``"BiasVsEta"`` and
                ``"ResVsEta"`` entries (only available for spatial coordinates).

        Returns:
            dict[str, Hist]: Mapping from histogram key to loaded histogram.
                Keys: ``"<variable>BiasVsNTracks"``, ``"<variable>ResVsNTracks"``,
                ``"<variable>BiasVsDecayLength"``, ``"<variable>ResVsDecayLength"``
                (plus ``"<variable>BiasVsEta"`` and ``"<variable>ResVsEta"`` if
                ``include_eta=True``).
        """
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
        """Load all secondary-vertex validation histograms from the DQM ROOT files.

        Populates ``self.DATA[config][coll]`` for every loaded configuration and
        collection.  Skips (config, collection) combinations whose ROOT subdirectory
        is not present in the file.

        The following histogram keys are available after loading:

        **Vertex counts**:

        - ``"nSVs"`` — number of reconstructed secondary vertices per event
        - ``"nAllSimSVs"`` — all simulated secondary vertices
        - ``"nSignalSimSVs"`` — signal-only simulated secondary vertices

        **Track-level quality** (efficiency and purity of tracks assigned to SVs):

        - ``"trackEff"``, ``"trackPurity"``
        - ``"trackEffVsDecayLength"``, ``"trackEffVsNTracksRecoSV"``,
          ``"trackEffVsNTracksSimSV"``
        - ``"trackPurityVsDecayLength"``, ``"trackPurityVsNTracksRecoSV"``,
          ``"trackPurityVsNTracksSimSV"``
        - ``"trackNSharedTracks"``

        **Vertex-level rates** (vs decayLength, decayLengthXY, eta, pt, mass, nTracks):

        - ``"effVs<Variable>"``, ``"techEffVs<Variable>"``, ``"mergeVs<Variable>"``
        - ``"fakeVs<Variable>"``, ``"dupVs<Variable>"``, ``"pileupVs<Variable>"``

        **Rates without efficiency** (vs decayLengthSig, chi2ndof):

        - ``"fakeVs<Variable>"``, ``"dupVs<Variable>"``, ``"pileupVs<Variable>"``

        **Resolution / bias** (vs nTracks and decayLength; vs eta for spatial coords):

        - ``"<quantity>BiasVsNTracks"``, ``"<quantity>ResVsNTracks"``
        - ``"<quantity>BiasVsDecayLength"``, ``"<quantity>ResVsDecayLength"``

          where ``<quantity>`` is one of ``decayLength``, ``decayLengthXY``,
          ``eta``, ``pt``, ``mass``, ``phi``, ``x``, ``y``, ``z``.
        """
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
        """Plot a stacked histogram of simulated vertices broken down by decay type.

        Reads ``num_<yName>_<decayType>_<xName>`` histograms from the ROOT file and
        draws them as a filled stacked area chart, one band per decay type.  The
        x-axis scale is set to logarithmic automatically when the bin edges are
        log-spaced.

        The figure is saved to ``DIR/num_<yName>_vs_<xName>.<ext>`` for each
        extension in ``SAVEAS``.

        Args:
            config (str, optional): Config tag to use.  Defaults to the first entry
                in ``CONFIGS``.
            xName (str): x-axis variable name as it appears in the ROOT histogram
                name, e.g. ``"decayLength"``, ``"decayLengthXY"``, ``"eta"``.
            yName (str): Quantity prefix in the ROOT histogram name.  Use
                ``"sim"`` for the number of simulated vertices (default).
            decayTypes (list[str]): Decay-type identifiers to stack, drawn in order
                from bottom to top.  Must be keys of ``DECAYCOLORS`` and
                ``DECAYLABELS``.  Default: ``["b", "c", "s", "tau"]``.
            coll (str): Collection key from ``COLLECTIONS``.  Default: ``"IVF"``.
            xLabel (str): x-axis label string (LaTeX supported).
            yLabel (str): y-axis label string.
            xLim (tuple[float | None, float | None]): ``(xMin, xMax)`` for the
                x-axis.  ``None`` uses the automatic limit.

        Example::

            plotter.plotStackedHistogramOfDecayTypes(
                xName="decayLength",
                xLabel=r"Simulated vertex 3D decay length $L_{3D}$ [cm]",
                yLabel="Number of simulated signal vertices",
                xLim=(1e-3, 20),
            )
        """
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
