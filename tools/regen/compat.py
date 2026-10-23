from saju_engine.engine import compute_chart
from saju_engine.compat_report import generate_compat_report
from saju_engine.compat import compat_score
REF = dict(reference_year=2026, reference_month=9, reference_day=26)
B = "candidates_horoscope/marriage_compatibility"
harish = compute_chart(name="Harish", gender="M", year=1992, month=6, day=4, hour=3, minute=10,
                       longitude=79.4408, utc_offset=5.5, **REF)
manvitha = compute_chart(name="Manvitha", gender="F", year=1996, month=12, day=3, hour=21, minute=15,
                         longitude=78.8242, utc_offset=5.5, **REF)
pawan = compute_chart(name="Pawan", gender="M", year=1991, month=10, day=3, hour=23, minute=45,
                      longitude=79.19, utc_offset=5.5, **REF)
sruthi = compute_chart(name="Sruthi", gender="F", year=1993, month=12, day=11, hour=2, minute=45,
                       longitude=79.45, utc_offset=5.5, **REF)
bindu = compute_chart(name="Bindu", gender="F", year=1995, month=3, day=24, hour=10, minute=10,
                      longitude=78.2669, utc_offset=5.5, **REF)
srinidhi = compute_chart(name="Srinidhi", gender="F", year=1994, month=4, day=9, hour=20, minute=47,
                         longitude=78.70, utc_offset=5.5, **REF)
priyanka = compute_chart(name="Priyanka", gender="F", year=1996, month=6, day=3, hour=10, minute=20,
                         longitude=80.2707, utc_offset=5.5, **REF)
# `harish_priyanka_1998` is a *different* woman who shares the first name
# (12 Jul 1998, Pallipattu) — kept distinct from `harish_priyanka` (3 Jun 1996).
priyanka_1998 = compute_chart(name="Priyanka", gender="F", year=1998, month=7, day=12, hour=21, minute=43,
                              longitude=79.4408, utc_offset=5.5, **REF)
# Keerthana — 3 Oct 1996, 09:35 IST, Coimbatore (DD/MM/1996 per the client form).
keerthana = compute_chart(name="Keerthana", gender="F", year=1996, month=10, day=3, hour=9, minute=35,
                          longitude=76.9558, utc_offset=5.5, **REF)
# Prethivika — 19 Mar 1993, 03:17 IST, Pondicherry (DD/MM/1993 per the bio-data).
prethivika = compute_chart(name="Prethivika", gender="F", year=1993, month=3, day=19, hour=3, minute=17,
                           longitude=79.8083, utc_offset=5.5, **REF)
# NOTE: harish_vinothini is intentionally absent — Vinothini's birth date, time
# and place are not on record (only her four pillars), so the engine cannot
# rebuild her chart. Her existing .md is left as-is (see docs/issues_bugs.md).
# generation_date preserves each pair's provenance date (matches the README).
jobs = [
    ("harish_manvitha", harish, manvitha, "Harish", "Manvitha", {}, "2026-09-26"),
    ("pawan_sruthi", pawan, sruthi, "Pawan", "Sruthi",
     dict(favorable_element_a="Water", favorable_element_b="Earth"), "2026-09-26"),
    ("harish_bindu", harish, bindu, "Harish", "Bindu", {}, "2026-09-26"),
    ("harish_srinidhi", harish, srinidhi, "Harish", "Srinidhi", {}, "2026-09-30"),
    ("harish_priyanka", harish, priyanka, "Harish", "Priyanka", {}, "2026-10-03"),
    ("harish_priyanka_1998", harish, priyanka_1998, "Harish", "Priyanka", {}, "2026-10-07"),
    ("harish_keerthana", harish, keerthana, "Harish", "Keerthana", {}, "2026-10-17"),
    ("harish_prethivika", harish, prethivika, "Harish", "Prethivika", {}, "2026-10-22"),
]
for slug, a, b, na, nb, ov, gd in jobs:
    for tier, suffix in (("basic", ""), ("deep", "_deep")):
        md = generate_compat_report(a, b, na, nb, generation_date=gd, tier=tier, **ov)
        path = f"{B}/{slug}/{slug}_compatibility{suffix}.md"
        open(path, "w").write(md)
        print("wrote", path)
    r = compat_score(a, b, **ov)
    print(slug, r.score, r.band)
