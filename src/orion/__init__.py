"""Orion — the framework's canonical import name.

Orion is the name of the framework (see the papers under ``publication/papers`` and
the root ``README``). The on-disk implementation package is ``rakl`` (``src/rakl``),
whose name is deliberately retained: 899 frozen receipts, the paper-3 experiments,
and job/schema identities SHA-pin the exact ``rakl`` bytes and paths, so renaming the
source itself would break the "unchanged since freeze" provenance the papers rely on.

This module makes ``import orion`` (and ``import orion.<submodule>``) resolve to that
implementation. **New code should import ``orion``.**
"""
from __future__ import annotations

import importlib
import sys

_impl = importlib.import_module("rakl")
sys.modules[__name__] = _impl  # orion IS rakl: shares __path__, submodules resolve
