# Ceiling conservative-bias disclosure (preserved from frozen-file amendment)

Provenance: the analysis below was originally added to the frozen
`INTERPRETATION_NARROWING.json` (bbb6e9ac, carried by PRs #680/#633/#632/#682
from merge-base 0414c40c) and was removed to restore the 8fa768f6 byte pin
(e9730c37). The freeze requires byte identity, so the disclosure lives here,
in a non-frozen side file. Nothing below alters any verdict; it documents that
the reported parent-lossiness ceilings are conservative.

## Text (verbatim)

The grouping key is (family,) + projected_fields, so every parent is
additionally handed the generator's construction label, which is not part of
its declared visible state. Removing it lowers every parent --
COMPOSITE_SIMPLE_PARENT falls 0.714 to 0.656, FAILURE_MEMORY_ONLY 0.607 to
0.500 -- while the typed arm stays at 1.0. The reported lossiness therefore
understates the real gap and the retained claim is conservative, not
inflated. Full measurements and the consequence for the closest-parent
mapping are in NEAREST_WORK_AUDIT.json :: PARENT_STATE_ABSTRACTION.exact_correspondence_qualifier.
