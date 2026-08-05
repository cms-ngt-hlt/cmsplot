from cmsplot import Hist, getSumHist, getDiffHist
from .DQMPlotter import DQMPlotter


class TrackingDQMPlotter(DQMPlotter):
    """DQM validation plotter for CMS HLT pixel and general tracking.

    Reads tracking-validation ROOT files produced by the CMS DQM framework and
    provides efficiency, fake-rate, duplicate-rate, resolution, and hit-count
    histograms for comparison across reconstruction configurations.

    Three track collections are available by default:

    - ``"GeneralTracks"`` — general-purpose HLT tracks (``hltGeneral``).
    - ``"PixelTracks"`` — Phase-2 pixel CA tracks with extensions
      (``hltPhase2PixelCAExtension``).
    - ``"PixelTracksHP"`` — Phase-2 high-purity pixel tracks
      (``hltPhase2Pixel``).

    ROOT files are expected at ``data/Tracking/DQM_Tracking_<tag>.root``,
    inside the path ``DQMData/Run 1/HLT/Run summary/Tracking/ValidationWRTtp``.

    Efficiency plots automatically show the active selection cuts.  The cut on the
    x-axis variable is excluded automatically via the ``EFFCUTS`` keys:

    - ``"ZVertex"`` — always shown (never an x-axis variable): ``|z_vertex| < 30 cm``
    - ``"Pt"``      — suppressed on pT plots: ``pT > 0.9 GeV``
    - ``"Vertex"``  — suppressed on vertex-radius plots: ``r_vertex < 2.5 cm``

    Example::

        plotter = TrackingDQMPlotter(
            CONFIGURATIONS={
                "baseline": ["#e41a1c", "CA baseline"],
                "new":      ["#377eb8", "CA + new extensions"],
            },
        )
        plotter.setPlottingConfiguration(
            PLOTTINGCONFIGURATION="PixelTracks",
            DIR="plots/tracking",
            SAVEAS=["png", "pdf"],
        )
        plotter.plotHistogram("effVsEta", yLim=(0.5, 1.0), limitYTicks=True)
        plotter.plotHistogram("fakeVsEta",       yLim=(0.0, 0.3))
    """

    DATAPATH = "data/Tracking"
    FILENAMEPREFIX = "DQM_Tracking_"
    ROOTPATH = "DQMData/Run 1/HLT/Run summary/Tracking/ValidationWRTtp"
    DATALABEL = r"$\text{t}\bar{\text{t}}$ + 200 PU ($\sqrt{s} = 14\,\text{TeV}$), HLT pixel tracks"
    DIR = "plots/trackingValidation"
    COLLECTIONS = {
        "GeneralTracks": "hltGeneral_hltAssociatorByHits",
        "PixelTracks": "hltPhase2PixelCAExtension_hltAssociatorByHits",
        "PixelTracksHP": "hltPhase2Pixel_hltAssociatorByHits",
    }
    COLLS = COLLECTIONS.keys()
    # "ZVertex" key never appears in histogram names, so this cut is always shown.
    EFFCUTS = {
        "ZVertex": r"$|z_\text{vertex}| < 30\,\text{cm}$",
        "Pt":      r"$p_\text{T}>0.9\,\text{GeV}$",
        "Vertex":  r"$r_\text{vertex} < 2.5\,\text{cm}$",
    }

    # Maps user-facing key → Hist constructor args (count_quantity,) or (count_quantity, bin_quantity).
    # Drives both loadData and HIST_REGISTRY population.
    _HIST_DEFS = {
        # Efficiency
        "effVsEta":         ("efficiency", "eta"),
        "effVsPt":          ("efficiency", "pt"),
        "effVsPhi":         ("efficiency", "phi"),
        "effVsVertex":      ("effic_vs_vertpos",),
        # Fake rate
        "fakeVsEta":        ("fake", "eta"),
        "fakeVsPt":         ("fake", "pt"),
        "fakeVsPhi":        ("fake", "phi"),
        # Duplicate rate
        "dupVsEta":         ("duplicate", "eta"),
        "dupVsPt":          ("duplicate", "pt"),
        "dupVsPhi":         ("duplicate", "phi"),
        # Resolution (σ of pull distributions)
        "ptResVsEta":       ("ptres_vs_eta_Sigma",),
        "ptResVsPt":        ("ptres_vs_pt_Sigma",),
        "phiResVsEta":      ("phires_vs_eta_Sigma",),
        "dxyResVsEta":      ("dxyres_vs_eta_Sigma",),
        "dzResVsEta":       ("dzres_vs_eta_Sigma",),
        # Track counts
        "recoAssocVsEta":   ("num_assoc(recoToSim)_eta",),
        "recoAssocVsPt":    ("num_assoc(recoToSim)_pT",),
        "nTracksVsEta":     ("num_reco_eta",),
        "nTracksVsPt":      ("num_reco_pT",),
        "nDupsVsEta":       ("num_duplicate_eta",),
        "nDupsVsPt":        ("num_duplicate_pT",),
        "hitsVsEta":        ("hits_eta",),
        "nSimVsEta":        ("num_simul_eta",),
        "nSimVsPt":         ("num_simul_pT",),
        "nSimVsPhi":        ("num_simul_phi",),
        "nSimVsVertex":     ("num_simul_vertpos",),
    }

    def loadData(self):
        """Load all tracking-validation histograms from the DQM ROOT files.

        Populates ``self.DATA[config][coll]`` for every loaded configuration and
        collection.  Skips (config, collection) combinations whose ROOT subdirectory
        is not present in the file.

        The following histogram keys are available after loading:

        **Efficiency** (vs η, pT, φ, vertex radius):

        - ``"effVsEta"``, ``"effVsPt"``, ``"effVsPhi"``, ``"effVsVertex"``

        **Fake rate** (vs η, pT, φ):

        - ``"fakeVsEta"``, ``"fakeVsPt"``, ``"fakeVsPhi"``

        **Duplicate rate** (vs η, pT, φ):

        - ``"dupVsEta"``, ``"dupVsPt"``, ``"dupVsPhi"``

        **Fake + duplicate** (derived, vs η, pT, φ):

        - ``"fakePlusDupVsEta"``, ``"fakePlusDupVsPt"``, ``"fakePlusDupVsPhi"``

        **Track counts** (vs η, pT):

        - ``"nTracksVsEta"``, ``"nTracksVsPt"``
        - ``"nSimVsEta"``, ``"nSimVsPt"``, ``"nSimVsPhi"``, ``"nSimVsVertex"``
        - ``"nDupsVsEta"``, ``"nDupsVsPt"``
        - ``"nFakesVsEta"``, ``"nFakesVsPt"``
          (derived as ``nTracks − recoAssoc``)
        - ``"recoAssocVsEta"``, ``"recoAssocVsPt"``
          (number of tracks matched reco→sim)

        **Resolution** (σ of pull distributions vs η or pT):

        - ``"ptResVsEta"``, ``"ptResVsPt"``
        - ``"phiResVsEta"``, ``"dxyResVsEta"``, ``"dzResVsEta"``

        **Hit counts**:

        - ``"hitsVsEta"``

        Use :meth:`~DQMPlotter.listHistograms` to display the full list with ROOT sources.
        """
        for config in self.CONFIGS:
            for coll in self.COLLS:
                colldir = self.COLLECTIONS[coll]
                if (colldir + ";1") not in self.FILES[config].keys():
                    continue
                rootdir = self.FILES[config][colldir]
                self.DATA[config][coll] = {}

                for key, args in self._HIST_DEFS.items():
                    self.DATA[config][coll][key] = Hist(rootdir, *args)
                    self._register(coll, key, *args)

                d = self.DATA[config][coll]
                d["fakePlusDupVsEta"]  = getSumHist(d["fakeVsEta"],  d["dupVsEta"])
                d["fakePlusDupVsPt"]   = getSumHist(d["fakeVsPt"],   d["dupVsPt"])
                d["fakePlusDupVsPhi"]  = getSumHist(d["fakeVsPhi"],  d["dupVsPhi"])
                d["nFakesVsEta"]       = getDiffHist(d["nTracksVsEta"], d["recoAssocVsEta"])
                d["nFakesVsPt"]        = getDiffHist(d["nTracksVsPt"],  d["recoAssocVsPt"])

                self._register(coll, "fakePlusDupVsEta", "sum(fakeVsEta, dupVsEta)")
                self._register(coll, "fakePlusDupVsPt",  "sum(fakeVsPt, dupVsPt)")
                self._register(coll, "fakePlusDupVsPhi", "sum(fakeVsPhi, dupVsPhi)")
                self._register(coll, "nFakesVsEta",      "diff(nTracksVsEta, recoAssocVsEta)")
                self._register(coll, "nFakesVsPt",       "diff(nTracksVsPt, recoAssocVsPt)")
