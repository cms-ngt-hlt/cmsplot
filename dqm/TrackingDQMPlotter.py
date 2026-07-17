from cmsplot import Hist, getSumHist, getDiffHist
from .DQMPlotter import DQMPlotter


class TrackingDQMPlotter(DQMPlotter):
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
    # Cut strings for efficiency plot labels. Keys are histogram name substrings: a cut is
    # excluded when its key appears in the histogram name (the variable is on the x-axis).
    # "ZVertex" is never an x-axis variable in the current set, so it is always shown.
    EFFCUTS = {
        "ZVertex": r"$|z_\text{vertex}| < 30\,\text{cm}$",
        "Pt":      r"$p_\text{T}>0.9\,\text{GeV}$",
        "Vertex":  r"$r_\text{vertex} < 2.5\,\text{cm}$",
    }

    def loadData(self):
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

