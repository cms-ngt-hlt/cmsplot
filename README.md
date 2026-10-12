# cmsplot

Shared plotting package for CMS Phase-2 HLT validation, developed within the NGT CMS group at CERN.
Provides DQM validation plotters, histogram wrappers, and general-purpose CMS-style plotting utilities.

---

## Installation

`cmsplot` is a self-contained Python package.
Install it once in editable mode from the repo root so that it is importable from any notebook or script:

```bash
# from the repo root
pip install -e .
```

After installation, import it in any notebook or script:

```python
from cmsplot import *          # Hist, Hist2D, getRatioHist, xlabel, ylabel, …
from cmsplot.dqm import TrackingDQMPlotter, SecondaryVertexingDQMPlotter
```

**Requirements:** Python ≥ 3.9, `uproot`, `numpy`, `matplotlib`, `scipy`, `mplhep`.

---

## DQM validation plotters

`cmsplot.dqm` provides two ready-to-use plotters that read CMS DQM ROOT files and
produce publication-quality overlay plots with an optional ratio panel.

### Workflow

Every plotter follows the same three-step pattern:

```
1. Instantiate  →  opens ROOT files, loads histograms
2. Configure    →  choose which overlays to draw, set labels / colours / output dir
3. Plot         →  call plotHistogram() for each quantity of interest
```

---

### `TrackingDQMPlotter`

Reads tracking-validation ROOT files and provides efficiency, fake-rate,
duplicate-rate, resolution, and hit-count histograms for HLT pixel and general tracks.

**Expected file layout**

```
data/Tracking/DQM_Tracking_<tag>.root
```

ROOT internal path: `DQMData/Run 1/HLT/Run summary/Tracking/ValidationWRTtp`

**Quick start**

```python
from cmsplot.dqm import TrackingDQMPlotter

plotter = TrackingDQMPlotter(
    CONFIGURATIONS={
        #  tag          color       legend label
        "baseline": ["#e41a1c", "CA baseline"],
        "new":      ["#377eb8", "CA + new extensions"],
    },
)

plotter.setPlottingConfiguration(
    PLOTTINGCONFIGURATION="PixelTracks",   # draw one collection per config
    CMSLABEL="Simulation (Private Work)",
    DIR="plots/tracking",
    SAVEAS=["png", "pdf"],
)

# efficiency vs η — cut labels are added automatically
plotter.plotHistogram("effVsEta", yLim=(0.5, 1.0), limitYTicks=True,
                      ratioYLim=(0.97, 1.03))

# fake rate vs pT (log x-axis applied automatically)
plotter.plotHistogram("fakeVsPt", yLim=(0.0, 0.3))

# track-pT resolution vs η
plotter.plotHistogram("ptResVsEta", yLabel=r"$\sigma(p_\mathrm{T})/p_\mathrm{T}$")
```

**Available collections**

| Key | ROOT subdirectory |
|---|---|
| `"GeneralTracks"` | `hltGeneral_hltAssociatorByHits` |
| `"PixelTracks"` | `hltPhase2Pixel_hltAssociatorByHits` |

**Key histogram names** (see `TrackingDQMPlotter.loadData` docstring for the full list)

| Category | Keys |
|---|---|
| Efficiency | `"effVsEta"`, `"effVsPt"`, `"effVsPhi"`, `"effVsVertex"` |
| Fake rate | `"fakeVsEta"`, `"fakeVsPt"`, `"fakeVsPhi"` |
| Duplicate rate | `"dupVsEta"`, `"dupVsPt"`, `"dupVsPhi"` |
| Fake + duplicate (derived) | `"fakePlusDupVsEta"`, `"fakePlusDupVsPt"`, `"fakePlusDupVsPhi"` |
| Track counts | `"nTracksVsEta"`, `"nTracksVsPt"`, `"nSimVsEta"`, `"nFakesVsEta"`, `"recoAssocVsEta"` |
| Resolution (σ) | `"ptResVsEta"`, `"ptResVsPt"`, `"phiResVsEta"`, `"dxyResVsEta"`, `"dzResVsEta"` |
| Hits | `"hitsVsEta"` |

---

### `SecondaryVertexingDQMPlotter`

Reads secondary-vertexing validation ROOT files and provides efficiency,
fake/duplicate/pileup/merge rates, resolution histograms, and track-quality metrics
for the IVF (Inclusive Vertex Finder) collection.

**Expected file layout**

```
data/DQM_General_<tag>.root
```

ROOT internal path: `DQMData/Run 1/HLT/Run summary/SecondaryVertices/Validation`

**Quick start**

```python
from cmsplot.dqm import SecondaryVertexingDQMPlotter

plotter = SecondaryVertexingDQMPlotter(
    CONFIGURATIONS={
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

# efficiency vs 3D decay length — cut labels added automatically
plotter.plotHistogram("effVsDecayLength", yLim=(0.0, 1.0), limitYTicks=True,
                      ratioYLim=(0.95, 1.05))

# fake rate vs η
plotter.plotHistogram("fakeVsEta", yLim=(0.0, 0.5))

# stacked decay-type composition plot
plotter.plotStackedHistogramOfDecayTypes(
    xName="decayLength",
    xLabel=r"Simulated vertex 3D decay length $L_{3D}$ [cm]",
    xLim=(1e-3, 20),
)
```

**Available collections**

| Key | ROOT subdirectory |
|---|---|
| `"IVF"` | `hltDeepInclusiveMergedVerticesPF` |

**Key histogram names** (see `SecondaryVertexingDQMPlotter.loadData` docstring for the full list)

| Category | Pattern |
|---|---|
| Vertex-level rates | `"effVs<Var>"`, `"techEffVs<Var>"`, `"mergeVs<Var>"`, `"fakeVs<Var>"`, `"dupVs<Var>"`, `"pileupVs<Var>"` |
| Track quality | `"trackEff"`, `"trackPurity"`, `"trackEffVsDecayLength"`, … |
| Resolution / bias | `"<quantity>ResVsNTracks"`, `"<quantity>BiasVsDecayLength"`, … |
| Vertex counts | `"nSVs"`, `"nAllSimSVs"`, `"nSignalSimSVs"` |

where `<Var>` is one of `DecayLength`, `DecayLengthXY`, `Eta`, `Pt`, `Mass`, `NTracks`,
`DecayLengthSig`, `Chi2ndof`, and `<quantity>` is one of `decayLength`, `decayLengthXY`,
`eta`, `pt`, `mass`, `phi`, `x`, `y`, `z`.

---

### Discovering available histograms

Every plotter keeps a registry of all pre-loaded histograms and their ROOT sources.
Print a full table with:

```python
plotter.listHistograms()           # all collections
plotter.listHistograms("PixelTracks")  # one collection
```

Example output:

```
Collection: PixelTracks

  Key                    ROOT source
  ---------------------  ------------------------------------------
  effVsEta               efficiency | eta
  fakeVsEta              fake | eta
  dupVsEta               duplicate | eta
  ptResVsEta             ptres_vs_eta_Sigma
  fakePlusDupVsEta       sum(fakeVsEta, dupVsEta)
  ...
```

Each call to `plotHistogram` also prints a one-line reminder:

```
'effVsEta'  [PixelTracks]  →  efficiency | eta
```

---

### `setPlottingConfiguration` — common options

| Parameter | Default | Description |
|---|---|---|
| `PLOTTINGCONFIGURATION` | *(required)* | Which overlays to draw — a collection name string, a list of `[tag, coll]` pairs (optionally + label suffix + color override), or a full label→`[tag, coll]` dict (optionally + color override) |
| `RATIO` | `True` | Show ratio / difference sub-panel |
| `DRAFT` | `False` | Print a grey DRAFT watermark |
| `CMSLABEL` | `"Simulation (Private Work)"` | Left-hand CMS label |
| `DATALABEL` | *(subclass default)* | Right-hand dataset description |
| `OBJECTLABEL` | `None` | Short object label appended as `", <OBJECTLABEL>"` |
| `EFFCUTS` | *(subclass default)* | Partial override of per-cut label strings |
| `DIR` | `"plots"` | Output directory |
| `SAVEAS` | `["png"]` | File extensions to save |

### `plotHistogram` — common options

| Parameter | Default | Description |
|---|---|---|
| `yLim` | `(None, None)` | y-axis range for the main panel |
| `xLim` | `(None, None)` | x-axis range |
| `xLabel` | auto | x-axis label (auto for η and pT) |
| `yLabel` | `None` | y-axis label |
| `yScale` | `None` | e.g. `"log"` |
| `ratioType` | `"ratio"` | `"ratio"` or `"diff"` |
| `ratioYLim` | `(None, None)` | y-axis range of the ratio panel |
| `factor` | `None` | Rescaling factor for y-axis tick labels |
| `limitYTicks` | `False` | Restrict y ticks to `[0, 1]` (recommended for efficiency plots) |

---

### Comparing two collections within the same config

Pass a dict to `PLOTTINGCONFIGURATION` for full control over labels. By default
each curve's color comes from its `config_tag` in `CONFIGURATIONS`, so two
collections from the *same* config would otherwise share a color — add an
optional 3rd list element to override it per curve:

```python
plotter.setPlottingConfiguration(
    PLOTTINGCONFIGURATION={
        "Pixel tracks":   ["Run3_v2", "PixelTracks"],
        "General tracks": ["Run3_v2", "GeneralTracks", "#000000"],
    },
    RATIO=True,
)
plotter.plotHistogram("effVsEta")
```

The list form supports the same idea, plus a label *suffix* (3rd element,
appended to the auto-derived label; pass `None` to skip it while still
setting a color) — this is what makes it possible to reuse the same
`config_tag` for more than one collection without duplicating its ROOT file:

```python
plotter.setPlottingConfiguration(
    PLOTTINGCONFIGURATION=[
        ["Run3_v1", "PixelTracks"],
        ["Run3_v2", "PixelTracks"],
        ["Run3_v2", "GeneralTracks", " (general tracks)", "#000000"],
    ],
)
```

A `ValueError` is raised if two entries still resolve to the same label
(e.g. the same `config_tag` + collection reused, or a missing suffix), rather
than silently dropping one of the curves.

---

## Timing breakdown plots

`cmsplot.timing` builds stacked-bar timing breakdowns from CMSSW per-module
timing reports — e.g. comparing how computing time splits across "IT Hits",
"Legacy Seeding", "Final Build+Fit", ... between several reconstruction
configurations. It follows the same two-step workflow as the DQM plotters,
but since every timing study groups its modules differently, the
project-specific parts (how to load one config's data, how to classify a
module into a group, and the event count to normalize by) are passed in
rather than implemented per subclass:

The module-grouping patterns and colors are shared CMS-wide reference data,
not something to redefine per study, so they're bundled with `cmsplot`
itself rather than loaded from a file you have to keep in sync — just pick a
grouping by name:

```python
from cmsplot.timing import TimingPlotter, load_grouping, load_modules_json

grouping = load_grouping("tracking")  # see available_groupings() for the full list

plotter = TimingPlotter(
    CONFIGURATIONS={
        "Legacy": "Legacy\n[2 iterations]",
        "ITACA":  "ITACA\n[2 GPU iterations]",
    },
    loadModules=lambda tag: load_modules_json(f"timing/{tag}_NGTScouting.json"),
    classify=grouping.classify(),
    Nevents=39744,
)

plotter.setPlottingConfiguration(
    CMSLABEL="Simulation (Private Work)",
    DATALABEL="HLT tracking, run on 2x AMD EPYC 9534 with 1x NVIDIA L40",
    DIR="plots/timing",
)
plotter.plotStackedTiming(
    steps=grouping.step,
    categories=grouping.categories,
    colors=grouping.colors,
    yLim=(0, 2.4),
    breakYLim=True,   # auto-sizes a broken y-axis for any bar that overshoots yLim
    filename="bar_total",
)
```

Each bundled grouping is a directory (`cmsplot/timing/groupings/<name>/`)
with `groups.json` (pattern → raw group string) and `colors.json`
(group → color) kept as separate files — the same one-file-per-concern
layout used by [circles](https://github.com/fwyzard/circles/tree/master/web)
(`web/groups/*.json` + `web/colours/*.json`), so a freshly updated
`groups.json`/`colors.json` from wherever your group maintains its canonical
version can be dropped in directly. A third file, `meta.json`, holds the
display labels and which classifier to use (`categories`, plus `step` or
`stepPrefixes`) — curation that's ours, not something to overwrite from
upstream. `load_grouping` also accepts a path to your own directory in the
same three-file layout instead of a bundled name — see its docstring for the
exact format, or a bundled grouping as a template. **`groups.json`'s key
order matters**: a module is assigned to the *first* pattern it matches, and
patterns can legitimately overlap, so when replacing it, keep the source
file's order — don't let a formatter alphabetize the keys. Each grouping is
built on one of two classifier primitives, exposed directly in
`cmsplot.timing.classify` for fully custom cases:

- **`classify_by_membership(patterns, mainGroups, step="Tracking")`** — every
  matched module is tagged with a single `step` label; only groups listed in
  `mainGroups` are kept. Use this when all groups of interest belong to one
  logical step. The bundled `"tracking"` grouping uses this.
- **`classify_by_step_prefix(patterns, stepPrefixes)`** — splits modules
  across several named steps by a group-string prefix (e.g.
  `{"InitialStep|": "InitialStep", "HighPtTripletStep|": "HighPtTripletStep"}`).
  The bundled `"tracking_by_step"` grouping uses this.

Write a plain `classify(module) -> (step, group)` function for anything a
bundled grouping doesn't cover — returning `(None, None)` excludes a module,
and `plotter.unmatchedModules(tag)` lists what got excluded so nothing
silently disappears from the total.

There's no special CPU-vs-GPU (or similar) concept — give each variant its
own `CONFIGURATIONS` entry (and point `loadModules` at the right file for
that tag), the same way you'd add any other configuration to compare.

`breakYLim` needs the optional `brokenaxes` package:

```bash
pip install cmsplot[timing]
```

---

## Core utilities

Beyond the DQM plotters, `cmsplot` exposes general-purpose helpers used in all notebooks:

```python
from cmsplot import Hist, Hist2D, getRatioHist, getSumHist, getDiffHist
from cmsplot import xlabel, ylabel, cmslabel, savefig, setStyle
```

- **`Hist`** / **`Hist2D`** — lightweight wrappers around uproot histogram objects, with
  `.values`, `.errors`, `.edges` attributes and a `.plot()` method.
- **`getRatioHist(h, ref)`** — bin-by-bin ratio with propagated errors.
- **`getSumHist(h1, h2)`** / **`getDiffHist(h1, h2)`** — arithmetic combinations.
- **`xlabel` / `ylabel`** — CMS-style axis labels with built-in symbol look-up.
- **`cmslabel`** — standard CMS experiment / luminosity label via `mplhep`.
- **`savefig`** — save the current figure, creating the output directory if needed.
- **`setStyle`** — apply the CMS matplotlib style sheet.
