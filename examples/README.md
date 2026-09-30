# Examples

| File | Runs out of the box? | Demonstrates |
|---|---|---|
| [`quickstart_histograms.ipynb`](quickstart_histograms.ipynb) | Yes — uses toy data, no CMS files needed | `Hist`, `getRatioHist`, `getSumHist`/`getDiffHist`, `cmslabel`, `setStyle`, axis label helpers |
| [`TrackingDQMPlotter_example.ipynb`](TrackingDQMPlotter_example.ipynb) | No — needs real tracking DQM ROOT files | `TrackingDQMPlotter` end-to-end workflow: single-collection comparison, overlaying different collections with label/color overrides, and derived histograms |
| [`SecondaryVertexingDQMPlotter_example.py`](SecondaryVertexingDQMPlotter_example.py) | No — needs real secondary-vertexing DQM ROOT files | `SecondaryVertexingDQMPlotter` end-to-end workflow |

Start with `quickstart_histograms.ipynb` to get a feel for the plotting API
without needing any data. `TrackingDQMPlotter_example.ipynb` is a fully
narrated, already-executed walkthrough of the DQM plotter workflow — its
outputs are visible directly (e.g. on GitHub) without running anything, and
it doubles as a copy-paste source once you point `CONFIGURATIONS`/`DATAPATH`
at your own ROOT files (paths and layout are documented in the notebook and
in `TrackingDQMPlotter`'s docstring). `SecondaryVertexingDQMPlotter_example.py`
is a bare-bones template for the same idea, kept as a plain script — copy it,
adapt `CONFIGURATIONS`/`DATAPATH` and the histogram keys, and adjust
`PLOTTINGCONFIGURATION` to what you want to compare.

Install `cmsplot` first (from the repo root):

```bash
pip install -e .
```
