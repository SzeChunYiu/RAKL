"""Confirm the dev/heldout split is real and reaches the rendered text."""
from rakl.prose_transfer_instrument_v1 import generate
from rakl.prose_transfer_extractor_v1 import full_prose_extractor

seed = 20260814907
dev_t, dev_s = generate(seed, n_per_cell=8, bank="dev")
hel_t, hel_s = generate(seed, n_per_cell=8, bank="heldout")

# Same seed => same latent specs; only the surface wording should differ.
same_latent = sum(
    all(
        d.coords[k].value == h.coords[k].value and d.coords[k].mode == h.coords[k].mode
        for k in d.coords
    )
    for d, h in zip(dev_s, hel_s)
)
diff_text = sum(d.target_text != h.target_text for d, h in zip(dev_t, hel_t))
same_gold = sum(d.gold is h.gold for d, h in zip(dev_s, hel_s))
n = len(dev_t)
print(f"n={n}")
print(f"identical latent spec (seed-matched): {same_latent}/{n}")
print(f"identical gold:                        {same_gold}/{n}")
print(f"DIFFERENT rendered target text:        {diff_text}/{n}")

dev_exact = sum(s.gold is full_prose_extractor(t) for t, s in zip(dev_t, dev_s)) / n
hel_exact = sum(s.gold is full_prose_extractor(t) for t, s in zip(hel_t, hel_s)) / n
print(f"extractor on dev surface:     {dev_exact:.4f}")
print(f"extractor on heldout surface: {hel_exact:.4f}")
print(f"held-out lexicon costs:       {dev_exact - hel_exact:.4f}")
