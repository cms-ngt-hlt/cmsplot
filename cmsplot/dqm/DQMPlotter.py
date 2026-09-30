import uproot
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.stats import binomtest
from cmsplot import Hist, getRatioHist
import cmsplot as cplt


class DQMPlotter:
    """Base class for CMS DQM validation plotters.

    Provides a two-step workflow for loading ROOT-based DQM histograms and
    producing publication-quality comparison plots:

    1. **Initialisation** — pass one or more run configurations (ROOT files) and
       optionally a set of track/vertex collections to ``__init__``.  The class
       opens the files and calls :meth:`loadData` automatically.
    2. **Plot configuration** — call :meth:`setPlottingConfiguration` to choose
       which configurations and collections to overlay, set colours, labels, etc.
    3. **Plotting** — call :meth:`plotHistogram` (or a subclass-specific method)
       for each histogram of interest.

    Subclasses must override:

    - ``DATAPATH``, ``FILENAMEPREFIX``, ``ROOTPATH`` — filesystem / ROOT-path settings.
    - ``DATALABEL`` — right-hand CMS label string.
    - ``COLLECTIONS`` — mapping from friendly name to ROOT subdirectory name.
    - ``EFFCUTS`` — dict of cut strings shown on efficiency plot labels.
    - :meth:`loadData` — populate ``self.DATA`` from ``self.FILES``.

    The ``CONFIGURATIONS`` dict maps an arbitrary config tag to a 2-element list
    ``[color, label]``, for example::

        CONFIGURATIONS = {
            "Run3_v1": ["#e41a1c", "Run 3 v1"],
            "Run3_v2": ["#377eb8", "Run 3 v2"],
        }

    The ROOT file for config tag ``tag`` is expected at
    ``<DATAPATH>/<FILENAMEPREFIX><tag>.root``.
    """

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
    LEGENDNCOLS = 2
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

    # Registry of pre-loaded histograms: {coll: {key: root_repr}}
    # root_repr is a human-readable string identifying the ROOT histogram source.
    HIST_REGISTRY = {}

    def __init__(self, CONFIGURATIONS={}, COLLECTIONS={}, DATAPATH=None, FILENAMEPREFIX=None):
        """Initialise the plotter, open ROOT files, and load histogram data.

        Args:
            CONFIGURATIONS (dict): Mapping from config tag to ``[color, label]``.
                Each tag must correspond to a ROOT file
                ``<DATAPATH>/<FILENAMEPREFIX><tag>.root``.  Example::

                    {
                        "Run3_v1": ["#e41a1c", "Run 3 baseline"],
                        "Run3_v2": ["#377eb8", "Run 3 new geometry"],
                    }

            COLLECTIONS (dict, optional): Extra track/vertex collections to add on
                top of the subclass defaults, keyed by a friendly name.
            DATAPATH (str, optional): Override the subclass ``DATAPATH``.

        Example::

            plotter = TrackingDQMPlotter(
                CONFIGURATIONS={
                    "baseline": ["#e41a1c", "Baseline"],
                    "new":      ["#377eb8", "New geometry"],
                },
            )
        """
        self.updateConfiguration(
            CONFIGURATIONS=CONFIGURATIONS,
            COLLECTIONS=COLLECTIONS,
            DATAPATH=DATAPATH,
            FILENAMEPREFIX=FILENAMEPREFIX,
        )
        self.loadData()

    def updateConfiguration(self, CONFIGURATIONS={}, COLLECTIONS={}, DATAPATH=None, FILENAMEPREFIX=None):
        """Merge additional run configurations or collections into the current setup.

        Can be called after ``__init__`` to add more ROOT files without discarding
        already-loaded data.  New entries are merged (not replaced) into the
        existing ``CONFIGURATIONS`` and ``COLLECTIONS`` dicts.

        Args:
            CONFIGURATIONS (dict, optional): Additional config-tag → ``[color, label]``
                entries to merge.
            COLLECTIONS (dict, optional): Additional collection name → ROOT subdirectory
                entries to merge.
            DATAPATH (str, optional): Override the current data path.
        """
        if CONFIGURATIONS:
            self.CONFIGURATIONS = self.CONFIGURATIONS | CONFIGURATIONS
        if COLLECTIONS:
            self.COLLECTIONS = self.COLLECTIONS | COLLECTIONS
            self.COLLS = self.COLLECTIONS.keys()
        if DATAPATH:
            self.DATAPATH = DATAPATH
        if FILENAMEPREFIX:
            self.FILENAMEPREFIX = FILENAMEPREFIX

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
        self.HIST_REGISTRY = {}

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
        LEGENDNCOLS=2,
        DIR=None,
        SAVEAS=["png"],
        MARKERS=["s", "^", "D", "v", "o", "."] + ["."] * 30,
        CUSTOMIZESTYLE=False,
    ):
        """Configure which histograms to overlay and how to style the plots.

        Must be called before any plotting method.  ``PLOTTINGCONFIGURATION``
        selects the (config, collection) pairs to draw and accepts three forms:

        - **dict** — maps legend label to ``[config_tag, collection_name]``, with
          an optional 3rd element overriding that curve's color (default: the
          color set for ``config_tag`` in ``CONFIGURATIONS``)::

              {
                  "Baseline pixel tracks": ["Run3_v1", "PixelTracks"],
                  "New pixel tracks":      ["Run3_v2", "PixelTracks"],
                  "New general tracks":    ["Run3_v2", "GeneralTracks", "#000000"],
              }

        - **list** — list of ``[config_tag, collection_name]`` pairs; legend labels
          are taken from the ``NAMES`` dict (i.e. the label set in ``CONFIGURATIONS``).
          Two optional trailing elements refine this: a label *suffix* appended to
          the auto-derived label (needed when the same ``config_tag`` is reused for
          more than one collection, e.g. to overlay ``PixelTracks`` and
          ``GeneralTracks`` for the same run without duplicating its ROOT file —
          pass ``None`` to skip the suffix while still setting a color), and a
          color override::

              [
                  ["Run3_v1", "PixelTracks"],
                  ["Run3_v2", "PixelTracks"],
                  ["Run3_v2", "GeneralTracks", " (general tracks)", "#000000"],
              ]

          A ``ValueError`` is raised if two entries still resolve to the same
          label (add a distinguishing suffix to fix it).

        - **string** — a single collection name; one line per loaded config::

              "PixelTracks"

        Args:
            PLOTTINGCONFIGURATION (dict | list | str): Selection of
                (config, collection) pairs to overlay, with optional per-curve
                color (and, for the list form, label-suffix) overrides (see above).
            DRAFT (bool): If ``True``, print a grey "DRAFT" watermark on every plot.
            CMSLABEL (str): Left-hand CMS label, e.g. ``"Simulation (Private Work)"``.
            DATALABEL (str, optional): Override the right-hand label (dataset description).
            OBJECTLABEL (str, optional): Short object description appended to
                ``DATALABEL`` as ``", <OBJECTLABEL>"``, e.g. ``"HLT pixel tracks"``.
            EFFCUTS (dict, optional): Partial override of the subclass ``EFFCUTS``
                dict.  Only the provided keys are updated; others are kept.
            CUT_TECHEFF (str | None, optional): Cut string appended exclusively to
                technical-efficiency plot labels.  Pass ``None`` to suppress it.
                Defaults to the subclass value (``...`` = do not change).
            RATIO (bool): Show a ratio (or difference) panel below the main plot.
            EXTENDPLOTNAME (bool): Append config/collection tags to the saved filename.
            LEGEND (bool): Show the legend.
            LEGENDNCOLS (int): Number of columns in the legend.
            DIR (str, optional): Output directory for saved figures.
            SAVEAS (list[str]): File extensions to save, e.g. ``["png", "pdf"]``.
            MARKERS (list): Matplotlib marker strings, one per overlay line.
            CUSTOMIZESTYLE (bool): Apply additional CMS style customisations via
                ``cmsplot.setStyle``.

        Example::

            plotter.setPlottingConfiguration(
                PLOTTINGCONFIGURATION="PixelTracks",
                CMSLABEL="Simulation (Private Work)",
                RATIO=True,
                DIR="plots/tracking",
                SAVEAS=["png", "pdf"],
            )

            # overlay pixel and general tracks for the same run, without
            # duplicating its ROOT file under a second config tag
            plotter.setPlottingConfiguration(
                PLOTTINGCONFIGURATION=[
                    ["Run3_v2", "PixelTracks"],
                    ["Run3_v2", "GeneralTracks", " (general tracks)", "#000000"],
                ],
            )
        """
        if isinstance(PLOTTINGCONFIGURATION, dict):
            self.PLOTTINGCONFIGURATION = PLOTTINGCONFIGURATION
        elif isinstance(PLOTTINGCONFIGURATION, list):
            self.PLOTTINGCONFIGURATION = {}
            for entry in PLOTTINGCONFIGURATION:
                config, coll = entry[0], entry[1]
                labelSuffix = entry[2] if len(entry) > 2 and entry[2] else ""
                label = self.NAMES[config] + labelSuffix
                if label in self.PLOTTINGCONFIGURATION:
                    raise ValueError(
                        "PLOTTINGCONFIGURATION label %r is used by more than one "
                        "entry - add a distinguishing label suffix (3rd list "
                        "element)." % label
                    )
                value = [config, coll]
                if len(entry) > 3 and entry[3] is not None:
                    value.append(entry[3])
                self.PLOTTINGCONFIGURATION[label] = value
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
        self.LEGENDNCOLS = LEGENDNCOLS
        if DIR is not None:
            self.DIR = DIR
        self.SAVEAS = SAVEAS
        self.MARKERS = MARKERS
        self.COLORS = [
            v[2] if len(v) > 2 and v[2] is not None else self.CONFIGCOLORS[v[0]]
            for v in self.PLOTTINGCONFIGURATION.values()
        ]

        cplt.setStyle(CUSTOMIZESTYLE)

    def _register(self, coll, key, *hist_args):
        """Record a histogram key and its ROOT source in ``HIST_REGISTRY``.

        Called by :meth:`loadData` implementations once per (collection, key) pair.
        Safe to call multiple times for the same key — only the first call is stored.

        Args:
            coll (str): Collection name (key in ``COLLECTIONS``).
            key (str): User-facing histogram key (as stored in ``self.DATA``).
            *hist_args: Either one string (the raw ROOT histogram name) or two strings
                ``(count_quantity, bin_quantity)`` matching the :class:`~cmsplot.Hist`
                constructor.  For derived histograms pass a single descriptive string
                such as ``"sum(fakeVsEta, dupVsEta)"``.
        """
        if coll not in self.HIST_REGISTRY:
            self.HIST_REGISTRY[coll] = {}
        if key not in self.HIST_REGISTRY[coll]:
            if len(hist_args) == 2:
                root_repr = f"{hist_args[0]} | {hist_args[1]}"
            else:
                root_repr = str(hist_args[0])
            self.HIST_REGISTRY[coll][key] = root_repr

    def listHistograms(self, coll=None):
        """Print a table of available histogram keys and their ROOT histogram sources.

        Covers all histograms pre-loaded by :meth:`loadData` as well as any
        additionally registered via :meth:`_register`.  Histograms loaded lazily
        by :meth:`plotHistogram` are not shown here.

        Args:
            coll (str, optional): Restrict output to one collection.  If ``None``
                (default), all collections are printed.

        Example::

            plotter.listHistograms()
            plotter.listHistograms("PixelTracks")
        """
        colls = [coll] if coll else sorted(self.HIST_REGISTRY.keys())
        for c in colls:
            entries = self.HIST_REGISTRY.get(c, {})
            if not entries:
                print(f"No histograms registered for collection '{c}'.")
                continue
            print(f"\nCollection: {c}")
            w = max(len(k) for k in entries) + 2
            print(f"  {'Key':<{w}}  ROOT source")
            print(f"  {'-'*w}  {'-'*45}")
            for key, root_repr in entries.items():
                print(f"  {key:<{w}}  {root_repr}")

    def loadData(self):
        """Load histogram data from ROOT files into ``self.DATA``.

        Must be implemented by every subclass.  Implementations should iterate
        over ``self.CONFIGS`` and ``self.COLLS``, create :class:`~cmsplot.Hist`
        objects from ``self.FILES[config][colldir]``, and store them in
        ``self.DATA[config][coll]`` as a dict keyed by a histogram name string.
        """
        raise NotImplementedError

    def _datalabel(self, histoName):
        """Build the right-side CMS label string for the given histogram.

        For non-efficiency histograms returns ``DATALABEL`` (with ``OBJECTLABEL``
        appended if set).  For efficiency histograms, a second line of active cut
        strings is appended, automatically excluding the cut whose key matches
        a substring of ``histoName`` (i.e. the variable on the x-axis).
        ``CUT_TECHEFF`` is additionally appended for technical-efficiency histograms.

        Args:
            histoName (str): Internal histogram key used to detect the x-axis
                variable and whether the histogram is an efficiency.

        Returns:
            str: Formatted label string, possibly multi-line.
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
        """Compute per-bin efficiency and 68.3 % Clopper–Pearson confidence intervals.

        Uses :func:`scipy.stats.binomtest` for each bin individually.  Bins with
        zero total entries are assigned efficiency 0 and zero-width intervals.

        Args:
            passing (array-like): Number of passing entries per bin.
            total (array-like): Number of total entries per bin.

        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray]:
                ``(efficiency, ci_low, ci_high)`` — all arrays of the same length
                as the input.
        """
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
        """Return a histogram representing the bin-by-bin difference ``Hist1 - Hist2``.

        Errors are propagated in quadrature.  If ``Hist2`` is omitted, returns a
        zero-valued histogram with the same errors as ``Hist1`` (useful as a
        reference uncertainty band in ratio panels).

        Note:
            This method is not statistically correct for efficiency histograms,
            where errors are asymmetric and correlated.  Use it only for raw counts
            or derived rate histograms.

        Args:
            Hist1 (Hist): Minuend histogram.
            Hist2 (Hist, optional): Subtrahend histogram.  If ``None``, the result
                has zero values but preserves ``Hist1``'s errors.

        Returns:
            Hist: Difference histogram with propagated errors.
        """
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
        """Check whether a set of bin edges is approximately logarithmically spaced.

        Compares the ratio of the last two edges to the ratio of the first two.
        If they agree within ``rtol``, the binning is considered logarithmic.

        Args:
            edges (array-like): Bin edge array (length = n_bins + 1).
            rtol (float): Relative tolerance for the spacing comparison.

        Returns:
            bool: ``True`` if the edges are log-spaced.
        """
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
        """Plot one histogram for all entries in ``PLOTTINGCONFIGURATION``.

        Overlays the selected (config, collection) pairs on a single panel, with
        an optional ratio or difference sub-panel below.  The figure is saved to
        ``DIR/<histoName>.<ext>`` for each extension in ``SAVEAS``.

        If the histogram has not been pre-loaded by :meth:`loadData`, it is loaded
        on the fly from the corresponding ROOT file.

        Args:
            histoName (str): Key of the histogram to plot.  Must match an entry in
                ``self.DATA[config][coll]`` or a histogram name in the ROOT file.
                The key is also used as the output filename.  Histograms whose name
                contains ``"eff"`` or ``"techEff"`` are treated as efficiencies:
                cut labels are added automatically and ``limitYTicks`` is useful.
            yLim (tuple[float | None, float | None]): ``(yMin, yMax)`` for the
                main panel.  ``None`` keeps matplotlib's autoscaled value for that
                side.  No headroom is added automatically — since the legend's
                height depends on ``LEGENDNCOLS`` and the number of overlaid
                entries, include enough headroom in ``yMax`` yourself so the
                legend doesn't cover the data.
            xLim (tuple[float | None, float | None]): ``(xMin, xMax)`` for the
                x-axis.  ``None`` uses the automatic limit.
            xLabel (str, optional): x-axis label.  If ``None``, an automatic label
                is applied for ``"Eta"`` and ``"Pt"`` histogram names.
            yLabel (str, optional): y-axis label for the main panel.
            yScale (str, optional): y-axis scale, e.g. ``"log"``.
            xScale (str, optional): Force x-axis scale, e.g. ``"log"``.
                Histograms with ``"Pt"`` in the name are set to log automatically.
            ratioType (str): ``"ratio"`` (default) draws ``hist_i / hist_0``;
                ``"diff"`` draws ``hist_i - hist_0``.
            ratioYLim (tuple[float | None, float | None]): y-axis limits for the
                ratio/difference sub-panel.  Out-of-range points are indicated by
                arrow markers.
            factor (float, optional): Multiplicative rescaling factor applied to
                the y-axis tick labels (useful for unit conversions).
            limitYTicks (bool): If ``True``, restrict y-axis ticks to ``[0, 1]``,
                which is convenient for efficiency plots to avoid crowded tick labels
                outside the physical range.

        Example::

            plotter.plotHistogram(
                "efficiencyVsEta",
                yLim=(0.5, 1.0),
                xLim=(-4.0, 4.0),
                ratioYLim=(0.95, 1.05),
                limitYTicks=True,
            )

            plotter.plotHistogram(
                "nTracksVsPt",
                yScale="log",
                yLim=(1e2, 1e6),
                ratioType="ratio",
            )
        """
        print("Plot histogram:")
        for c in sorted({v[1] for v in self.PLOTTINGCONFIGURATION.values()}):
            root = self.HIST_REGISTRY.get(c, {}).get(histoName, "(not pre-registered)")
            print(f"{histoName!r}  [{c}]  →  {root}")

        ISEFF = ("eff" in histoName) or ("techEff" in histoName)

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
                handletextpad=0.25, ncols=self.LEGENDNCOLS, columnspacing=0.8,
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

        if yScale is not None:
            ax1.set_yscale(yScale)

        # a None bound keeps matplotlib's autoscaled value for that side
        ax1.set_ylim(yLim)
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
            print("Saved plot to %s/%s.%s" % (self.DIR, plotname, saveas))
        plt.show()
