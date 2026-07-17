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
        plotter.plotHistogram("efficiencyVsEta", yLim=(0.5, 1.0), limitYTicks=True)
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

    def loadData(self):
        """Load all tracking-validation histograms from the DQM ROOT files.

        Populates ``self.DATA[config][coll]`` for every loaded configuration and
        collection.  Skips (config, collection) combinations whose ROOT subdirectory
        is not present in the file.

        The following histogram keys are available after loading:

        **Efficiency / fake / duplicate rates** (vs η, pT, φ, vertex radius):

        - ``"efficiencyVsEta"``, ``"efficiencyVsPt"``, ``"efficiencyVsPhi"``,
          ``"efficiencyVsVertex"``
        - ``"fakeVsEta"``, ``"fakeVsPt"``, ``"fakeVsPhi"``
        - ``"dupVsEta"``, ``"dupVsPt"``, ``"dupVsPhi"``
        - ``"fake+dupVsEta"``, ``"fake+dupVsPt"``, ``"fake+dupVsPhi"``
          (sum of fake and duplicate rates)

        **Track counts** (vs η, pT):

        - ``"nTracksVsEta"``, ``"nTracksVsPt"``
        - ``"nSimVsEta"``, ``"nSimVsPt"``, ``"nSimVsPhi"``, ``"nSimVsVertex"``
        - ``"nDupsVsEta"``, ``"nDupsVsPt"``
        - ``"nFakesVsEta"``, ``"nFakesVsPt"``
          (derived as ``nTracks - assoc(RecoToSim)``)
        - ``"assoc(RecoToSim)VsEta"``, ``"assoc(RecoToSim)VsPt"``

        **Resolution** (σ of pull distributions vs η or pT):

        - ``"ptresVsEta"``, ``"ptresVsPt"``
        - ``"phiresVsEta"``, ``"dxyresVsEta"``, ``"dzresVsEta"``

        **Hit counts**:

        - ``"hitsVsEta"``
        """
        for config in self.CONFIGS:
            for coll in self.COLLS:
                colldir = self.COLLECTIONS[coll]
                if (colldir + ";1") not in self.FILES[config].keys():
                    continue
                self.DATA[config][coll] = {
                    "efficiencyVsEta":         Hist(self.FILES[config][colldir], "efficiency", "eta"),
                    "fakeVsEta":               Hist(self.FILES[config][colldir], "fake", "eta"),
                    "dupVsEta":                Hist(self.FILES[config][colldir], "duplicate", "eta"),
                    "efficiencyVsPt":          Hist(self.FILES[config][colldir], "efficiency", "pt"),
                    "fakeVsPt":                Hist(self.FILES[config][colldir], "fake", "pt"),
                    "dupVsPt":                 Hist(self.FILES[config][colldir], "duplicate", "pt"),
                    "efficiencyVsPhi":         Hist(self.FILES[config][colldir], "efficiency", "phi"),
                    "fakeVsPhi":               Hist(self.FILES[config][colldir], "fake", "phi"),
                    "dupVsPhi":                Hist(self.FILES[config][colldir], "duplicate", "phi"),
                    "efficiencyVsVertex":      Hist(self.FILES[config][colldir], "effic_vs_vertpos"),
                    "ptresVsEta":              Hist(self.FILES[config][colldir], "ptres_vs_eta_Sigma"),
                    "ptresVsPt":               Hist(self.FILES[config][colldir], "ptres_vs_pt_Sigma"),
                    "phiresVsEta":             Hist(self.FILES[config][colldir], "phires_vs_eta_Sigma"),
                    "dxyresVsEta":             Hist(self.FILES[config][colldir], "dxyres_vs_eta_Sigma"),
                    "dzresVsEta":              Hist(self.FILES[config][colldir], "dzres_vs_eta_Sigma"),
                    "assoc(RecoToSim)VsEta":   Hist(self.FILES[config][colldir], "num_assoc(recoToSim)_eta"),
                    "assoc(RecoToSim)VsPt":    Hist(self.FILES[config][colldir], "num_assoc(recoToSim)_pT"),
                    "nTracksVsEta":            Hist(self.FILES[config][colldir], "num_reco_eta"),
                    "nTracksVsPt":             Hist(self.FILES[config][colldir], "num_reco_pT"),
                    "nDupsVsEta":              Hist(self.FILES[config][colldir], "num_duplicate_eta"),
                    "nDupsVsPt":               Hist(self.FILES[config][colldir], "num_duplicate_pT"),
                    "hitsVsEta":               Hist(self.FILES[config][colldir], "hits_eta"),
                    "nSimVsEta":               Hist(self.FILES[config][colldir], "num_simul_eta"),
                    "nSimVsPt":                Hist(self.FILES[config][colldir], "num_simul_pT"),
                    "nSimVsPhi":               Hist(self.FILES[config][colldir], "num_simul_phi"),
                    "nSimVsVertex":            Hist(self.FILES[config][colldir], "num_simul_vertpos"),
                }
                d = self.DATA[config][coll]
                d["fake+dupVsEta"]  = getSumHist(d["fakeVsEta"],  d["dupVsEta"])
                d["fake+dupVsPt"]   = getSumHist(d["fakeVsPt"],   d["dupVsPt"])
                d["fake+dupVsPhi"]  = getSumHist(d["fakeVsPhi"],  d["dupVsPhi"])
                d["nFakesVsEta"]    = getDiffHist(d["nTracksVsEta"], d["assoc(RecoToSim)VsEta"])
                d["nFakesVsPt"]     = getDiffHist(d["nTracksVsPt"],  d["assoc(RecoToSim)VsPt"])

