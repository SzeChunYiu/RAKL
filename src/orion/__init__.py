"""Orion — the framework's canonical import name.

Orion is the name of the framework; the on-disk implementation package is ``rakl``
(kept for frozen provenance: receipts, job identities and paper-3 experiments SHA-pin
the exact ``rakl`` bytes/paths). This module makes ``import orion`` and every
``import orion.<submodule>`` resolve to the *same module objects* as ``rakl.<submodule>``.

The meta-path finder below is required for correctness, not convenience: without it,
``orion.x`` would re-execute ``rakl/x.py`` under a second module name, producing
duplicate enum/class objects whose ``is``-comparisons silently disarm validation
invariants (found in hostile engineering audit). New code should import ``orion``.
"""
from __future__ import annotations

import importlib
import importlib.abc
import importlib.machinery
import sys

_impl = importlib.import_module("rakl")


class _OrionAliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Route ``orion.X`` to the already-loaded ``rakl.X`` module object (no re-exec)."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "orion" or fullname.startswith("orion."):
            return importlib.machinery.ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        target = "rakl" + spec.name[len("orion"):]
        module = importlib.import_module(target)
        sys.modules[spec.name] = module  # orion.X IS rakl.X (identity preserved)
        return module

    def exec_module(self, module):  # already executed as rakl.X
        return None


if not any(isinstance(f, _OrionAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _OrionAliasFinder())

sys.modules[__name__] = _impl
