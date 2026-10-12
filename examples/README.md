# Examples

| File | Runs out of the box? | Demonstrates |
|---|---|---|
| [`quickstart_histograms.ipynb`](quickstart_histograms.ipynb) | Yes — uses toy data, no CMS files needed | `Hist`, `getRatioHist`, `getSumHist`/`getDiffHist`, `cmslabel`, `setStyle`, axis label helpers |
| [`TimingPlotter_example.ipynb`](TimingPlotter_example.ipynb) | No — needs real tracking timing JSON files | `cmsplot.timing.TimingPlotter` end-to-end, reproducing the FSP26 timing-breakdown plot: loading/aggregating, `listGroups`/`unmatchedModules`, the bundled `"tracking"` grouping, and the automatic broken y-axis |
| [`TrackingDQMPlotter_example.ipynb`](TrackingDQMPlotter_example.ipynb) | No — needs real tracking DQM ROOT files | `TrackingDQMPlotter` end-to-end workflow: single-collection comparison, overlaying different collections with label/color overrides, and derived histograms |
| [`SecondaryVertexingDQMPlotter_example.py`](SecondaryVertexingDQMPlotter_example.py) | No — needs real secondary-vertexing DQM ROOT files | `SecondaryVertexingDQMPlotter` end-to-end workflow |

Start with `quickstart_histograms.ipynb` to get a feel for the plotting API
without needing any data. The other three are fully narrated,
already-executed walkthroughs against real CMS data — their outputs are
visible directly (e.g. on GitHub) without running anything, and each doubles
as a copy-paste source once you point it at your own files:
`TimingPlotter_example.ipynb` at `data/Timing/<tag>_....json`,
`TrackingDQMPlotter_example.ipynb` at `data/Tracking/` ROOT files (paths and
layout documented in the notebooks and in each class's docstring).
`SecondaryVertexingDQMPlotter_example.py` is a bare-bones template for the
same idea, kept as a plain script — copy it, adapt
`CONFIGURATIONS`/`DATAPATH` and the histogram keys, and adjust
`PLOTTINGCONFIGURATION` to what you want to compare.

Install `cmsplot` first (from the repo root):

```bash
pip install -e .
```
