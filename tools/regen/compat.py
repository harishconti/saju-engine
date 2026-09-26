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
jobs = [
    ("harish_manvitha", harish, manvitha, "Harish", "Manvitha", {}),
    ("pawan_sruthi", pawan, sruthi, "Pawan", "Sruthi",
     dict(favorable_element_a="Water", favorable_element_b="Earth")),
]
for slug, a, b, na, nb, ov in jobs:
    for tier, suffix in (("basic", ""), ("deep", "_deep")):
        md = generate_compat_report(a, b, na, nb, generation_date="2026-09-26", tier=tier, **ov)
        path = f"{B}/{slug}/{slug}_compatibility{suffix}.md"
        open(path, "w").write(md)
        print("wrote", path)
    r = compat_score(a, b, **ov)
    print(slug, r.score, r.band)
