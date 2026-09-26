"""Data classes for a fully-derived Saju chart.

The engine returns a `Chart` object that the PDF generator, the
/saju command, and any future API all consume uniformly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .sewoon import SeWoonHit



@dataclass
class Pillar:
    """One of the four pillars: year / month / day / hour."""
    position: str          # "year" | "month" | "day" | "hour"
    stem: str              # e.g. "丙"
    branch: str            # e.g. "午"
    hidden_stems: List[Tuple[str, str]] = field(default_factory=list)
    # hidden_stems is a list of (role, stem) tuples:
    #   role ∈ {"main","middle","residual"}
    # e.g. [("main","丁"), ("middle","己")] for 午

    @property
    def combined(self) -> str:
        return f"{self.stem}{self.branch}"


@dataclass
class TenGodHit:
    """A single 십신 occurrence in the chart."""
    position: str          # "year_stem" | "year_branch_main" | "year_branch_middle" | "year_branch_residual" | ...
    stem: str              # the stem this represents
    tengod: str            # Korean name, e.g. "편인"
    tengod_en: str         # English name, e.g. "Indirect Resource"


@dataclass
class DaeunPeriod:
    """One 10-year major-luck period."""
    start_age: int
    end_age: int
    stem: str
    branch: str
    combined: str = ""

    # Activation overlay (populated by daeun_overlay.build_daeun_overlays)
    stem_tengod: str = ""
    stem_tengod_en: str = ""
    activated_branches: List[Tuple[str, str, str]] = field(default_factory=list)
    relationship_types: List[str] = field(default_factory=list)
    harmony_completions: List[Any] = field(default_factory=list)
    # List[HarmonyCompletion] (sewoon.py) — 삼합/방합 triads this period's
    # branch completes/half-completes with the natal chart.
    stem_combinations: List[Dict] = field(default_factory=list)
    stem_clashes: List[Dict] = field(default_factory=list)
    # 천간충 {stem_a, stem_b} of this period's stem vs. natal stems (E-6).
    stem_element: str = ""
    branch_element: str = ""
    favorable_status: Optional[str] = None

    def __post_init__(self):
        self.end_age = self.start_age + 9
        self.combined = f"{self.stem}{self.branch}"


# ── Logical chart clusters (read-only views over the flat Chart fields) ───────

@dataclass
class BirthData:
    """Birth input and solar-time/correction metadata."""
    name: Optional[str] = None
    gender: Optional[str] = None
    birth_date: str = ""
    effective_date: str = ""
    birth_time: str = ""
    city: Optional[str] = None
    longitude: Optional[float] = None
    utc_offset: float = 9.0
    solar_correction: Optional[dict] = None
    zi_time_type: Optional[str] = None
    convention: str = "korean"


@dataclass
class NatalData:
    """Natal four-pillar data and derived natal overlays."""
    year: Pillar = None  # type: ignore
    month: Pillar = None  # type: ignore
    day: Pillar = None  # type: ignore
    hour: Pillar = None  # type: ignore

    day_master: str = ""
    day_master_info: dict = field(default_factory=dict)
    ten_gods: List[TenGodHit] = field(default_factory=list)
    twelve_stages: List[Tuple[str, str, str]] = field(default_factory=list)

    combinations_6: List[Tuple[str, str, str, str, str]] = field(default_factory=list)
    clashes: List[Tuple[str, str]] = field(default_factory=list)
    self_punishments: List[Tuple[str, str]] = field(default_factory=list)
    three_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    half_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    directional_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    six_harms: List[Tuple[str, str]] = field(default_factory=list)
    six_breaks: List[Tuple[str, str]] = field(default_factory=list)
    three_punishments: List[Tuple[str, str, str, str]] = field(default_factory=list)

    stars: Dict[str, List[str]] = field(default_factory=dict)
    strength_assessment: Optional[Dict] = None
    patterns: Dict = field(default_factory=dict)

    @property
    def pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.hour]

    @property
    def branches(self) -> List[str]:
        return [p.branch for p in self.pillars]

    @property
    def stems(self) -> List[str]:
        return [p.stem for p in self.pillars]


@dataclass
class LuckData:
    """Timed luck overlays relative to the chart's reference date."""
    daeun: List[DaeunPeriod] = field(default_factory=list)
    sewoon: List[Any] = field(default_factory=list)
    woon: List[Any] = field(default_factory=list)
    ilwoon: List[Any] = field(default_factory=list)
    current_age: Optional[int] = None
    current_daeun: Optional[DaeunPeriod] = None


@dataclass
class ReferenceData:
    """Reference date used for all "current" overlays and report language."""
    reference_date: str = ""


def _round_floats(obj: Any, ndigits: int = 2) -> Any:
    """Recursively round floats in a JSON-ready structure (dict/list/scalar)."""
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, ndigits) for v in obj]
    return obj


@dataclass
class Chart:
    """A fully-derived Saju chart ready for interpretation."""
    # Birth data
    name: Optional[str] = None
    gender: Optional[str] = None      # "M" or "F"
    birth_date: str = ""              # ISO "YYYY-MM-DD" (original input)
    effective_date: str = ""          # ISO "YYYY-MM-DD" (actual day-pillar date after solar/zi adjustment)
    birth_time: str = ""              # "HH:MM"
    city: Optional[str] = None
    longitude: Optional[float] = None
    utc_offset: float = 9.0            # birth timezone offset in hours (input, not solar-corrected)
    star_anchor: str = "day"           # 12신살 / 도화·역마·화개 anchor: "day" | "year" (E-7)

    # Four pillars
    year: Pillar = None  # type: ignore
    month: Pillar = None  # type: ignore
    day: Pillar = None  # type: ignore
    hour: Pillar = None  # type: ignore

    # Solar-time correction info (None when use_solar_time=False)
    solar_correction: Optional[dict] = None

    # Set when the independent, timezone-correct year/month pillar
    # recomputation disagreed with sajupy's raw value and overrode it
    # (E-1, 2026-09-25) — None when no correction was needed.
    year_month_correction: Optional[dict] = None

    # Set when the civil birth time is within pillars.TERM_BOUNDARY_MARGIN_MIN
    # of a month-opener 절기 (N-15, 2026-09-26 audit) — carries the pillars on
    # both sides of the term. None otherwise.
    term_boundary: Optional[dict] = None

    # 조자시 / 야자시 handling
    zi_time_type: Optional[str] = None  # "夜子時 (Korean 야자시)" | "早子時 (Chinese 조자시)" | None
    convention: str = "korean"          # convention used to derive the hour pillar

    # Reference date used for all "current" overlays and report language.
    # Defaults to the day the chart was computed, but can be overridden so
    # past/future queries return consistent results.
    reference_date: str = ""            # ISO "YYYY-MM-DD"

    # Derived
    day_master: str = ""               # e.g. "丙"
    day_master_info: dict = field(default_factory=dict)

    ten_gods: List[TenGodHit] = field(default_factory=list)
    twelve_stages: List[Tuple[str, str, str]] = field(default_factory=list)
    # twelve_stages entries: (position, branch, stage) e.g. ("month","卯","절")

    daeun: List[DaeunPeriod] = field(default_factory=list)

    # Natal branch relationships found
    combinations_6: List[Tuple[str, str, str, str, str]] = field(default_factory=list)
    # (branch_a, branch_b, combined_element, pillar_a, pillar_b) — positions captured as
    # which two branches (in branch-name form).
    clashes: List[Tuple[str, str]] = field(default_factory=list)
    self_punishments: List[Tuple[str, str]] = field(default_factory=list)
    three_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    half_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    # (branch_a, branch_b, frame_label, element) — two-of-three 삼합 (반합).
    directional_harmonies: List[Tuple[str, str, str, str]] = field(default_factory=list)
    # (branch_a, branch_b, branch_c, element/direction) — full 방합 triple.
    six_harms: List[Tuple[str, str]] = field(default_factory=list)
    six_breaks: List[Tuple[str, str]] = field(default_factory=list)
    three_punishments: List[Tuple[str, str, str, str]] = field(default_factory=list)

    # Optional derived overlays
    stars: Dict[str, List[str]] = field(default_factory=dict)
    strength_assessment: Optional[Dict] = None

    # Structural / grid pattern candidates (engine aid, not classical ruling)
    patterns: Dict = field(default_factory=dict)

    # Annual-luck (세운) window around the current/reference year
    sewoon: List["SeWoonHit"] = field(default_factory=list)

    # Monthly-luck (월운) window around the current/reference month
    woon: List["SeWoonHit"] = field(default_factory=list)

    # Daily-luck (일운) window around the current/reference day
    ilwoon: List["SeWoonHit"] = field(default_factory=list)

    # Querier-relative "now" values computed from reference_date.
    current_age: Optional[int] = None          # 사주 세수 on the reference date
    current_daeun: Optional[DaeunPeriod] = None  # major-luck period active then

    # ── Convenience properties ──────────────────────────────────────────────
    @property
    def pillars(self) -> List[Pillar]:
        return [self.year, self.month, self.day, self.hour]

    @property
    def branches(self) -> List[str]:
        return [p.branch for p in self.pillars]

    @property
    def stems(self) -> List[str]:
        return [p.stem for p in self.pillars]

    # ── Logical cluster views ────────────────────────────────────────────────
    @property
    def birth(self) -> BirthData:
        """Birth input and correction metadata as a single cluster."""
        return BirthData(
            name=self.name,
            gender=self.gender,
            birth_date=self.birth_date,
            effective_date=self.effective_date,
            birth_time=self.birth_time,
            city=self.city,
            longitude=self.longitude,
            utc_offset=self.utc_offset,
            solar_correction=self.solar_correction,
            zi_time_type=self.zi_time_type,
            convention=self.convention,
        )

    @property
    def natal(self) -> NatalData:
        """Natal four-pillar data and natal overlays as a single cluster."""
        return NatalData(
            year=self.year,
            month=self.month,
            day=self.day,
            hour=self.hour,
            day_master=self.day_master,
            day_master_info=self.day_master_info,
            ten_gods=self.ten_gods,
            twelve_stages=self.twelve_stages,
            combinations_6=self.combinations_6,
            clashes=self.clashes,
            self_punishments=self.self_punishments,
            three_harmonies=self.three_harmonies,
            half_harmonies=self.half_harmonies,
            directional_harmonies=self.directional_harmonies,
            six_harms=self.six_harms,
            six_breaks=self.six_breaks,
            three_punishments=self.three_punishments,
            stars=self.stars,
            strength_assessment=self.strength_assessment,
            patterns=self.patterns,
        )

    @property
    def luck(self) -> LuckData:
        """Timed luck overlays relative to the reference date."""
        return LuckData(
            daeun=self.daeun,
            sewoon=self.sewoon,
            woon=self.woon,
            ilwoon=self.ilwoon,
            current_age=self.current_age,
            current_daeun=self.current_daeun,
        )

    @property
    def reference(self) -> ReferenceData:
        """Reference date used for all current overlays."""
        return ReferenceData(reference_date=self.reference_date)

    def reference_date_obj(self) -> Optional[date]:
        """Parse `reference_date` into a `datetime.date`, or return None."""
        if not self.reference_date:
            return None
        try:
            y, m, d = (int(x) for x in self.reference_date.split("-"))
            return date(y, m, d)
        except (ValueError, TypeError):
            return None

    def pillar_table_rows(self) -> List[Tuple[str, str, str, str]]:
        """Return [(label, stem, branch, combined)] for the four pillars."""
        return [
            (p.position.capitalize(), p.stem, p.branch, p.combined)
            for p in self.pillars
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the chart to a plain dictionary (JSON-ready)."""
        def _pillar_dict(p: Pillar) -> Dict[str, Any]:
            return {
                "position": p.position,
                "stem": p.stem,
                "branch": p.branch,
                "combined": p.combined,
                "hidden_stems": [{"role": r, "stem": s} for r, s in p.hidden_stems],
            }

        return {
            "name": self.name,
            "gender": self.gender,
            "birth_date": self.birth_date,
            "effective_date": self.effective_date,
            "birth_time": self.birth_time,
            "city": self.city,
            "longitude": self.longitude,
            "utc_offset": self.utc_offset,
            "star_anchor": self.star_anchor,
            "convention": self.convention,
            "zi_time_type": self.zi_time_type,
            "solar_correction": self.solar_correction,
            "year_month_correction": self.year_month_correction,
            "term_boundary": self.term_boundary,
            "day_master": self.day_master,
            "day_master_info": self.day_master_info,
            "pillars": [_pillar_dict(p) for p in self.pillars],
            "ten_gods": [
                {
                    "position": h.position,
                    "stem": h.stem,
                    "tengod": h.tengod,
                    "tengod_en": h.tengod_en,
                }
                for h in self.ten_gods
            ],
            "twelve_stages": [
                {"position": pos, "branch": br, "stage": st}
                for pos, br, st in self.twelve_stages
            ],
            "daeun": [self._daeun_period_dict(p) for p in self.daeun],
            "combinations_6": self.combinations_6,
            "clashes": self.clashes,
            "self_punishments": self.self_punishments,
            "three_harmonies": self.three_harmonies,
            "half_harmonies": self.half_harmonies,
            "directional_harmonies": self.directional_harmonies,
            "six_harms": self.six_harms,
            "six_breaks": self.six_breaks,
            "three_punishments": self.three_punishments,
            "stars": self.stars,
            "strength_assessment": self.strength_assessment,
            "patterns": self._patterns_dict(self.patterns),
            "sewoon": [self._sewoon_dict(h) for h in self.sewoon],
            "woon": [self._sewoon_dict(h) for h in self.woon],
            "ilwoon": [self._sewoon_dict(h) for h in self.ilwoon],
            "reference_date": self.reference_date,
            "current_age": self.current_age,
            "current_daeun": self._daeun_period_dict(self.current_daeun) if self.current_daeun else None,
        }

    def _daeun_period_dict(self, p: DaeunPeriod) -> Dict[str, Any]:
        return {
            "start_age": p.start_age,
            "end_age": p.end_age,
            "stem": p.stem,
            "branch": p.branch,
            "combined": p.combined,
            "stem_tengod": p.stem_tengod,
            "stem_tengod_en": p.stem_tengod_en,
            "activated_branches": [
                {"daeun": a, "natal": n, "relationship": r}
                for a, n, r in p.activated_branches
            ],
            "relationship_types": p.relationship_types,
            "harmony_completions": self._harmony_completions_dicts(p.harmony_completions),
            "stem_combinations": p.stem_combinations,
            "stem_clashes": p.stem_clashes,
            "stem_element": p.stem_element,
            "branch_element": p.branch_element,
            "favorable_status": p.favorable_status,
        }

    def _sewoon_dict(self, h):
        return {
            "year": h.year,
            "stem": h.stem,
            "branch": h.branch,
            "combined": h.combined,
            "stem_tengod": h.stem_tengod,
            "stem_tengod_en": h.stem_tengod_en,
            "activated_branches": [
                {"period": a, "natal": n, "relationship": r}
                for a, n, r in h.activated_branches
            ],
            "relationship_types": h.relationship_types,
            "harmony_completions": self._harmony_completions_dicts(getattr(h, "harmony_completions", [])),
            "stem_combinations": [
                {"stem_a": a, "stem_b": b, "combined_element": e, "korean_name": k}
                for a, b, e, k in getattr(h, "stem_combinations", [])
            ],
            "natal_stem_combinations": [
                {"stem_a": a, "stem_b": b, "combined_element": e, "korean_name": k, "natal_stem": n}
                for a, b, e, k, n in getattr(h, "natal_stem_combinations", [])
            ],
            "stem_clashes": [
                {"stem_a": a, "stem_b": b} for a, b in getattr(h, "stem_clashes", [])
            ],
        }

    def _harmony_completions_dicts(self, completions) -> List[Dict[str, Any]]:
        return [
            {
                "kind": c.kind,
                "triad": list(c.triad),
                "element": c.element,
                "status": c.status,
                "matched_natal": list(c.matched_natal),
            }
            for c in (completions or [])
        ]

    def _patterns_dict(self, p):
        """Convert pattern output to JSON-serializable dictionaries."""
        if not p:
            return p
        # Shallow copy so the original dataclass objects remain intact.
        out = dict(p)
        if "regular_grid" in out:
            out["regular_grid"] = [
                {
                    "name_ko": g.name_ko,
                    "name_en": g.name_en,
                    "basis": g.basis,
                    "confidence": g.confidence,
                    "note": g.note,
                }
                for g in out["regular_grid"]
            ]
        return out

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """Serialize the chart to a JSON string.

        Uses strict JSON serialization so accidental non-serializable objects
        surface as errors rather than being silently stringified. Floats are
        rounded to 2 decimal places here (display boundary only — `to_dict()`
        keeps full precision for internal callers) so clients never see
        binary-float artifacts like ``1.9000000000000001``.
        """
        import json
        return json.dumps(_round_floats(self.to_dict()), indent=indent, ensure_ascii=ensure_ascii)
