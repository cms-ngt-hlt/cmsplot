import json
from pathlib import Path

from .classify import classify_by_membership, classify_by_step_prefix

_GROUPINGS_DIR = Path(__file__).parent / "groupings"


class Grouping:
    """A named, reusable module-classification scheme for :class:`~cmsplot.timing.TimingPlotter`.

    Bundles everything that's genuinely shared across timing studies using the
    same CMSSW module-grouping convention - a ``groups.json`` (pattern -> raw
    group string) and ``colors.json`` (group -> color), in the same
    one-file-per-concern layout used by `circles
    <https://github.com/fwyzard/circles/tree/master/web>`_ - plus a small
    ``meta.json`` for the display labels and which classifier to build
    (``categories``, in stack order, and either ``step`` or
    ``stepPrefixes``). Keeping `groups`/`colors` separate from `meta` means
    you can drop in a freshly updated ``groups.json``/``colors.json`` from
    wherever your group maintains its canonical version, without touching the
    display curation in `meta.json`. Construct one via :func:`load_grouping`
    rather than directly.

    .. warning::
        ``groups.json``'s key *order* is significant: a module is assigned to
        the *first* pattern it matches, and some patterns legitimately
        overlap. When replacing it, keep the source file's order as-is -
        don't let a formatter or editor alphabetize the keys, or some modules
        may silently end up in a different group than before.
    """

    def __init__(self, name, groups, colors, meta):
        self.name = name
        self.description = meta.get("description", "")
        self.classifierKind = meta["classifier"]
        self.step = meta.get("step")
        self.stepPrefixes = meta.get("stepPrefixes")
        self.patterns = groups
        self.categories = meta["categories"]
        self.colors = colors

    def classify(self):
        """Build the ``classify(module) -> (step, group)`` callable for this grouping.

        Returns:
            callable: ready to pass as ``TimingPlotter(..., classify=...)``.
        """
        if self.classifierKind == "membership":
            return classify_by_membership(self.patterns, list(self.categories.keys()), step=self.step)
        if self.classifierKind == "step_prefix":
            return classify_by_step_prefix(self.patterns, self.stepPrefixes)
        raise ValueError("Unknown classifier kind %r in grouping %r" % (self.classifierKind, self.name))

    def __repr__(self):
        return "Grouping(%r, classifier=%r, %i patterns, %i categories)" % (
            self.name, self.classifierKind, len(self.patterns), len(self.categories)
        )


def available_groupings():
    """List the names of the groupings bundled with ``cmsplot``.

    Returns:
        list[str]: Sorted grouping names, each loadable via :func:`load_grouping`.
    """
    return sorted(p.name for p in _GROUPINGS_DIR.iterdir() if p.is_dir())


def load_grouping(name):
    """Load a module-classification scheme by name, or from a custom directory.

    Args:
        name (str): Either the name of a grouping bundled with ``cmsplot``
            (see :func:`available_groupings`), or a path to a custom
            directory laid out the same way: ``groups.json`` (pattern -> raw
            group string), ``colors.json`` (group -> color), and ``meta.json``
            (an object with ``"classifier"`` - ``"membership"`` or
            ``"step_prefix"`` - ``"categories"``, and, depending on the
            classifier, ``"step"`` or ``"stepPrefixes"``). See the bundled
            groupings under ``cmsplot/timing/groupings/`` for concrete
            examples. ``groups.json``/``colors.json`` can be swapped for a
            freshly updated copy from your group's own canonical source (see
            the class docstring) without touching ``meta.json``.

    Returns:
        Grouping: use ``.classify()`` for the ``TimingPlotter(..., classify=...)``
        argument, and ``.categories``/``.colors`` for ``plotStackedTiming``.

    Example::

        from cmsplot.timing import TimingPlotter, load_grouping

        grouping = load_grouping("tracking")
        plotter = TimingPlotter(
            CONFIGURATIONS={"Legacy": "Legacy\\n[2 iterations]", "ITACA": "ITACA\\n[2 GPU iterations]"},
            loadModules=lambda tag: load_modules_json(f"timing/{tag}_NGTScouting.json"),
            classify=grouping.classify(),
            Nevents=39744,
        )
        plotter.plotStackedTiming(
            steps=grouping.step,
            categories=grouping.categories,
            colors=grouping.colors,
            yLim=(0, 2.4),
            breakYLim=True,
            filename="bar_total",
        )
    """
    builtin = _GROUPINGS_DIR / name
    directory = builtin if builtin.is_dir() else Path(name)
    if not directory.is_dir():
        raise FileNotFoundError(
            "%r is neither a bundled grouping (%s) nor an existing directory."
            % (name, ", ".join(available_groupings()))
        )

    with open(directory / "groups.json") as f:
        groups = json.load(f)
    with open(directory / "colors.json") as f:
        colors = json.load(f)
    with open(directory / "meta.json") as f:
        meta = json.load(f)
    return Grouping(directory.name, groups, colors, meta)
