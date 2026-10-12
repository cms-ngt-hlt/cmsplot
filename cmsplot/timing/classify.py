import json


def _matchedGroup(groupDict, module):
    """Find the first ``groupDict`` pattern matching a module, return its (raw) group string."""
    key = module["type"] + "|" + module["label"]
    for pattern, group in groupDict.items():
        if all(s in key for s in pattern.replace("?", " ").replace("*", " ").split()):
            return group
    return None


def classify_by_membership(groupDict, mainGroups, step="Tracking"):
    """Build a classifier that assigns every matched module to a single step.

    Matches each module against ``groupDict`` (a pattern -> group-string
    mapping, typically loaded from a ``*_Groups.json`` file: each pattern is
    matched by checking that every one of its whitespace-separated tokens
    appears in ``module["type"] + "|" + module["label"]``; a ``"|"`` suffix on
    the resolved group string is stripped). A module is kept - tagged with the
    single `step` label - only if its resolved group name is one of
    `mainGroups`; anything else is reported as unmatched.

    Use this when every group of interest belongs to one logical step (e.g.
    "Tracking" as a whole). For studies that split modules across several
    named steps (e.g. "InitialStep" vs "HighPtTripletStep"), see
    :func:`classify_by_step_prefix` instead.

    Args:
        groupDict (dict): Pattern -> group string mapping.
        mainGroups (list[str]): Group names to keep; any resolved group not
            in this list is treated as unmatched.
        step (str): Step label assigned to every kept module. Defaults to
            ``"Tracking"``.

    Returns:
        callable: ``classify(module) -> (step, group)`` for a kept module, or
        ``(None, None)`` for one that should be excluded.

    Example::

        classify = classify_by_membership(groupDict, mainGroups=["IT Hits", "OT Hits", ...])
        plotter = TimingPlotter(CONFIGURATIONS, loadModules, classify, Nevents)
    """
    def classify(module):
        group = _matchedGroup(groupDict, module)
        if group is None:
            return None, None
        if "|" in group:
            group = group[:group.find("|")]
        if not any(name in group for name in mainGroups):
            return None, None
        return step, group
    return classify


def classify_by_step_prefix(groupDict, stepPrefixes):
    """Build a classifier that splits modules across steps by a group-string prefix.

    Like :func:`classify_by_membership`, modules are first matched against
    `groupDict`. Instead of a single step label, the resolved group string is
    then expected to start with one of `stepPrefixes`' keys (including its
    separator, e.g. ``"HighPtTripletStep|"``); that prefix is stripped to
    recover the group name, and the matching value is used as the step label.
    A resolved group that doesn't start with any known prefix is unmatched.

    Args:
        groupDict (dict): Pattern -> group string mapping.
        stepPrefixes (dict): Maps a group-string prefix (e.g.
            ``"InitialStep|"``) to the step label to report for it.

    Returns:
        callable: ``classify(module) -> (step, group)`` for a kept module, or
        ``(None, None)`` for one that should be excluded.

    Example::

        classify = classify_by_step_prefix(groupDict, stepPrefixes={
            "InitialStep|":      "InitialStep",
            "HighPtTripletStep|": "HighPtTripletStep",
        })
        plotter = TimingPlotter(CONFIGURATIONS, loadModules, classify, Nevents)
    """
    def classify(module):
        group = _matchedGroup(groupDict, module)
        if group is None:
            return None, None
        for prefix, step in stepPrefixes.items():
            if group.startswith(prefix):
                group = group[len(prefix):]
                if "|" in group:
                    group = group[:group.find("|")]
                return step, group
        return None, None
    return classify


def load_modules_json(path):
    """Load a CMSSW timing-report JSON file's per-module records.

    Args:
        path (str): Path to a timing JSON file (must contain a ``"modules"``
            key).

    Returns:
        list[dict]: The raw per-module timing records, each with (at least)
        ``"type"``, ``"label"``, ``"time_real"``, and ``"events"`` keys.
    """
    with open(path) as f:
        return json.load(f)["modules"]
