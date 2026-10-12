import numpy as np
import matplotlib.pyplot as plt
import cmsplot as cplt


class TimingPlotter:
    """Stacked-bar timing breakdown plots from CMSSW per-module timing reports.

    Compares, across a set of reconstruction configurations, how computing
    time breaks down into physics-meaningful groups (e.g. "IT Hits",
    "Legacy Seeding", "Final Build+Fit"). Mirrors the two-step workflow of
    :class:`~cmsplot.dqm.DQMPlotter`:

    1. **Initialisation** — pass ``CONFIGURATIONS`` plus three callables that
       encapsulate everything project-specific: how to load one config's raw
       module list, how to classify a module into ``(step, group)``, and the
       event count(s) to normalize by. ``__init__`` loads and aggregates the
       data immediately.
    2. **Plotting** — call :meth:`plotStackedTiming` once per chart.

    Unlike the DQM plotters, there's no fixed "collections" concept here:
    every CMSSW timing study groups its modules differently, so the loading
    and classification logic is supplied by the caller rather than
    implemented per subclass. For the module-grouping patterns and colors
    specifically - which, unlike the file-loading and event counts, *are*
    shared CMS-wide reference data rather than something to redefine per
    study - :func:`~cmsplot.timing.groupings.load_grouping` bundles named,
    ready-to-use groupings (see :mod:`cmsplot.timing.groupings`) built on top
    of the two classifier primitives in :mod:`cmsplot.timing.classify`
    (:func:`~cmsplot.timing.classify.classify_by_membership` and
    :func:`~cmsplot.timing.classify.classify_by_step_prefix`); use those
    directly, or write a plain ``classify(module) -> (step, group)`` function,
    for anything a bundled grouping doesn't cover.

    A CPU-vs-GPU (or any other) variant is not a special concept here either
    - just give it its own entry in ``CONFIGURATIONS`` (and point
    ``loadModules`` at the right file for that tag), the same way you'd add
    any other configuration to compare.

    The ``CONFIGURATIONS`` dict maps a config tag to its legend/axis label.
    Unlike the DQM plotters, there's no per-config color here - a bar's
    colors come entirely from its stacked groups (the `colors` argument to
    :meth:`plotStackedTiming`), consistent across every config, so there's
    nothing for a per-config color to apply to::

        CONFIGURATIONS = {
            "Legacy": "Legacy baseline",
            "ITACA":  "ITACA",
        }

    Example::

        from cmsplot.timing import TimingPlotter, load_grouping, load_modules_json

        grouping = load_grouping("tracking")  # bundled with cmsplot - see available_groupings()

        plotter = TimingPlotter(
            CONFIGURATIONS={
                "Legacy": "Legacy\\n[2 iterations]",
                "ITACA":  "ITACA\\n[2 GPU iterations]",
            },
            loadModules=lambda tag: load_modules_json(f"timing/{tag}_NGTScouting.json"),
            classify=grouping.classify(),
            Nevents=39744,
        )
        plotter.setPlottingConfiguration(CMSLABEL="Simulation (Private Work)", DIR="plots/timing")
        plotter.plotStackedTiming(
            steps=grouping.step,
            categories=grouping.categories,
            colors=grouping.colors,
            yLim=(0, 2.4),
            breakYLim=True,
            filename="bar_total",
        )
    """

    CONFIGURATIONS = {}
    DRAFT = False
    CMSLABEL = "Simulation (Private Work)"
    DATALABEL = ""
    DIR = "plots"
    SAVEAS = ["png"]
    YLABEL = "Average computing time per event [s]"
    WIDTH = 0.5

    def __init__(self, CONFIGURATIONS, loadModules, classify, Nevents):
        """Initialise the plotter and load + aggregate every configuration's timing data.

        Args:
            CONFIGURATIONS (dict): Mapping from config tag to its legend/axis
                label (a plain string - there's no per-config color here, see
                the class docstring).
            loadModules (callable): ``loadModules(tag) -> list[dict]``, returning
                the raw per-module timing records for that config tag (see
                :func:`~cmsplot.timing.classify.load_modules_json` for the
                common case of one JSON file per tag).
            classify (callable): ``classify(module) -> (step, group)``, or
                ``(None, None)`` to exclude that module. See
                :mod:`cmsplot.timing.classify` for ready-made classifiers.
            Nevents (int | float | dict): Event count to normalize by. Either
                one number shared by every config, or a ``{tag: n}`` dict.
                Pass this explicitly rather than deriving it from the timing
                file - which module's event count is the right one to
                normalize by is a per-study decision, not something this
                class can guess safely.
        """
        self.CONFIGURATIONS = CONFIGURATIONS
        self.CONFIGS = list(CONFIGURATIONS.keys())
        self.NAMES = dict(CONFIGURATIONS)
        self.loadData(loadModules, classify, Nevents)

    def loadData(self, loadModules, classify, Nevents):
        """Load and aggregate every configuration's timing data into ``self.DATA``.

        Populates ``self.DATA[tag][step][group]`` (seconds/event) and
        ``self.UNMATCHED[tag]`` (modules `classify` excluded). Called
        automatically by ``__init__``; call again directly if you need to
        reload (e.g. after editing `classify`).
        """
        self.DATA = {}
        self.UNMATCHED = {}
        for tag in self.CONFIGS:
            modules = loadModules(tag)
            n = Nevents[tag] if isinstance(Nevents, dict) else Nevents

            agg = {}
            unmatched = []
            for module in modules:
                step, group = classify(module)
                if not step:
                    unmatched.append(module)
                    continue
                agg.setdefault(step, {})
                agg[step][group] = agg[step].get(group, 0.0) + module["time_real"]

            for groupTimes in agg.values():
                for g in groupTimes:
                    groupTimes[g] /= n * 1000

            self.DATA[tag] = agg
            self.UNMATCHED[tag] = unmatched

            if unmatched:
                unmatchedTime = sum(m["time_real"] for m in unmatched) / n / 1000
                matchedTime = sum(v for s in agg.values() for v in s.values())
                frac = unmatchedTime / (matchedTime + unmatchedTime) if (matchedTime + unmatchedTime) else 0.0
                print(
                    "%r: %i module(s) did not match any group (%.1f%% of total time) "
                    "- see .unmatchedModules(%r)" % (tag, len(unmatched), 100 * frac, tag)
                )

    def unmatchedModules(self, config):
        """Return the raw module records `classify` excluded for one config.

        Args:
            config (str): Config tag (key of ``CONFIGURATIONS``).

        Returns:
            list[dict]: The excluded per-module timing records.
        """
        return self.UNMATCHED[config]

    def listGroups(self, config=None):
        """Print every ``(step, group)`` loaded, with its seconds/event value.

        Args:
            config (str, optional): Restrict output to one config tag. If
                ``None`` (default), all configs are printed.
        """
        for c in ([config] if config else self.CONFIGS):
            print("\nConfig: %s" % c)
            for step, groups in self.DATA[c].items():
                for group, value in groups.items():
                    print("  [%s] %-20s %.4g s/event" % (step, group, value))

    def setPlottingConfiguration(
        self,
        DRAFT=False,
        CMSLABEL="Simulation (Private Work)",
        DATALABEL=None,
        DIR=None,
        SAVEAS=["png"],
        YLABEL=None,
        WIDTH=0.5,
    ):
        """Configure plot-wide styling, used by every subsequent :meth:`plotStackedTiming` call.

        Args:
            DRAFT (bool): If ``True``, print a grey "DRAFT" watermark on every plot.
            CMSLABEL (str): Left-hand CMS label, e.g. ``"Simulation (Private Work)"``.
            DATALABEL (str, optional): Right-hand label (dataset/machine description).
            DIR (str, optional): Output directory for saved figures.
            SAVEAS (list[str]): File extensions to save, e.g. ``["png", "pdf"]``.
            YLABEL (str, optional): y-axis label. Defaults to a generic
                "Average computing time per event [s]".
            WIDTH (float): Bar width.
        """
        self.DRAFT = DRAFT
        self.CMSLABEL = CMSLABEL
        if DATALABEL is not None:
            self.DATALABEL = DATALABEL
        if DIR is not None:
            self.DIR = DIR
        self.SAVEAS = SAVEAS
        if YLABEL is not None:
            self.YLABEL = YLABEL
        self.WIDTH = WIDTH

    def plotStackedTiming(
        self,
        steps,
        categories,
        colors,
        filename,
        configs=None,
        yLim=(0, None),
        breakYLim=None,
        showTotals=True,
        legend=True,
        legendLoc="upper right",
        legendBboxToAnchor=(0.98, 0.98),
        legendReverse=True,
        figsize=(15, 10),
    ):
        """Draw one stacked-bar timing breakdown, one bar per configuration.

        Args:
            steps (str | list[str]): Step(s) whose groups are stacked into
                each bar (keys of ``self.DATA[tag]``). A list stacks every
                listed step's groups together into the same bar - pass a
                single-element list/string for studies with only one step
                (e.g. a flat ``"Tracking"``).
            categories (dict): ``{group: legend_label}``, in stacking order
                (bottom to top). A config missing a given group contributes 0.
            colors (dict): ``{group: color}``, keyed the same as `categories`.
            filename (str): Output filename (without extension) under
                ``self.DIR``; saved once per extension in ``self.SAVEAS``.
            configs (list[str], optional): Which config tags to plot, and in
                what order. Defaults to every config passed to the plotter.
            yLim (tuple[float | None, float | None]): ``(yMin, yMax)`` for the
                main (or, with a break, lower) panel. No headroom is added
                automatically for the legend - pad ``yMax`` yourself.
            breakYLim: Controls a broken y-axis (via the optional
                ``brokenaxes`` package - install it with
                ``pip install cmsplot[timing]``) for bars that exceed
                ``yLim[1]``:

                - ``None``/``False`` (default): no break: a bar that exceeds
                  ``yLim[1]`` is simply clipped.
                - ``True``: auto-size a second pane above ``yLim[1]`` from
                  whichever bar(s) actually overshoot it (requires a numeric
                  ``yLim[1]``).
                - ``(low, high)``: use this range for the second pane directly.
            showTotals (bool): Annotate each bar with its stacked total.
            legend (bool): Show the legend.
            legendLoc (str): Matplotlib legend ``loc``.
            legendBboxToAnchor (tuple): Matplotlib legend ``bbox_to_anchor``.
            legendReverse (bool): Reverse the legend entry order (so it reads
                top-to-bottom in the same order as the stack).
            figsize (tuple): Figure size in inches.

        Returns:
            tuple: ``(fig, ax)`` - with a break, ``ax`` is the main (lower)
            panel's real Axes, matching the no-break case.

        Example::

            plotter.plotStackedTiming(
                steps="Tracking",
                categories={"IT Hits": "IT hits", "Legacy Seeding": "Legacy seeds"},
                colors=colorDict,
                yLim=(0, 2.4),
                breakYLim=True,
                filename="bar_total",
            )
        """
        if isinstance(steps, str):
            steps = [steps]
        configs = configs if configs is not None else self.CONFIGS
        Nconfigs = len(configs)
        labels = [self.NAMES[c] for c in configs]

        def valuesFor(group):
            return np.array([
                sum(self.DATA[c].get(step, {}).get(group, 0.0) for step in steps)
                for c in configs
            ])

        totals = np.zeros(Nconfigs)
        for group in categories:
            totals += valuesFor(group)

        if breakYLim is True:
            if yLim[1] is None:
                raise ValueError("breakYLim=True needs a numeric yLim[1] to detect overshooting bars.")
            overshoot = totals[totals > yLim[1]]
            breakYLim = (overshoot.min() * 0.9, totals.max() * 1.06) if len(overshoot) else None

        if breakYLim:
            try:
                from brokenaxes import brokenaxes
            except ImportError as e:
                raise ImportError(
                    "breakYLim requires the optional 'brokenaxes' package - install it via "
                    "`pip install cmsplot[timing]` or `pip install brokenaxes`."
                ) from e
            fig = plt.figure(figsize=figsize)
            bax = brokenaxes(ylims=(yLim, breakYLim), hspace=0.08, despine=False)
            ax = bax.axs[-1]  # the main (lower) pane, same range as the no-break case
        else:
            fig, ax = plt.subplots(1, figsize=figsize)
            bax = ax

        bottom = np.zeros(Nconfigs)
        for group, label in categories.items():
            values = valuesFor(group)
            # omit the legend entry for a category that doesn't contribute to
            # any of the plotted configs, rather than clutter the legend with
            # one that never shows up as a visible segment
            bax.bar(labels, values, self.WIDTH, label=label if values.any() else None,
                    bottom=bottom, color=colors[group])
            bottom += values

        ax.set_ylim(yLim)
        if showTotals:
            dy = ax.get_ylim()[1] - ax.get_ylim()[0]
            for i, val in enumerate(bottom):
                text = (("%.2f" % val) if val > 1 else ("%.3f" % val)) + r"$\,\text{s}$"
                bax.text(i, val + 0.01 * dy, text, fontsize=18,
                         horizontalalignment="center", verticalalignment="bottom")

        bax.set_ylabel(self.YLABEL)
        if legend:
            ax.legend(loc=legendLoc, bbox_to_anchor=legendBboxToAnchor, reverse=legendReverse)

        bax.set_xlim(-0.5, Nconfigs - 0.5)
        bax.set_xticks([], minor=True)

        # brokenaxes resets the x major locator to a numeric one on every forwarded
        # call, which clobbers the categorical bar labels - pin them directly on the
        # real axes as the last x-axis touch so nothing overwrites them afterwards
        for a in (bax.axs if breakYLim else [ax]):
            a.set_xticks(range(Nconfigs))
            a.set_xticklabels(labels)

        if self.DRAFT:
            ax.text(0.5, 0.5, "DRAFT", transform=ax.transAxes,
                    fontsize=150, color="gray", alpha=0.25,
                    ha="center", va="center", rotation=30)

        exptext, expsuffix, supptext, explumi = cplt.cmslabel(
            llabel=self.CMSLABEL, rlabel=self.DATALABEL, ax=ax, loc=4
        )
        explumi.set_fontsize(explumi.get_fontsize() / 1.25)

        for ext in self.SAVEAS:
            cplt.savefig("%s/%s.%s" % (self.DIR, filename, ext))
        plt.show()

        return fig, ax
