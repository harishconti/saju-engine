"""Shared helpers for the HTML/Playwright PDF generator.

Contains the Korean/Hanja → English translation maps and the CJK-stripping
logic originally created for the reportlab-based `md_to_saju_pdf.py`.
Both PDF generators import these maps so translations stay identical.
"""
from __future__ import annotations

import re

from saju_engine.report_data import ELEMENT_COLORS, ELEMENT_EMOJI


# ---------- Translation tables: Korean/Hanja -> English ----------

# Heavenly Stems
STEM_MAP = {
    "甲": "Gap (Yang Wood)", "乙": "Eul (Yin Wood)",
    "丙": "Bing (Yang Fire)", "丁": "Jeong (Yin Fire)",
    "戊": "Mu (Yang Earth)", "己": "Gi (Yin Earth)",
    "庚": "Gyeong (Yang Metal)", "辛": "Sin (Yin Metal)",
    "壬": "Im (Yang Water)", "癸": "Gye (Yin Water)",
}

# Earthly Branches
BRANCH_MAP = {
    "子": "Ja (Rat)", "丑": "Chuk (Ox)",
    "寅": "In (Tiger)", "卯": "Myo (Rabbit)",
    "辰": "Jin (Dragon)", "巳": "Sa (Snake)",
    "午": "O (Horse)", "未": "Mi (Goat)",
    "申": "Shin (Monkey)", "酉": "Yu (Rooster)",
    "戌": "Sul (Dog)", "亥": "Hae (Pig)",
}

# Ten Gods
TENGOD_MAP = {
    "비견": "Pillar (Companion)", "겁재": "Rob Wealth (Companion)",
    "식신": "Eating God (Output)", "상관": "Hurting Officer (Output)",
    "편재": "Indirect Wealth", "정재": "Direct Wealth",
    "편관": "Seven Killings (Authority)", "정관": "Direct Officer (Authority)",
    "편인": "Indirect Resource", "정인": "Direct Resource",
    "식상": "Output", "재성": "Wealth", "관성": "Authority", "인성": "Resource",
    "비겁": "Companion",
}

# Korean romanization
KOR_REPL = {
    "사주": "Saju", "사주 원국": "Four Pillars", "원국": "natal chart",
    "일간": "Day Master", "일주": "Day Pillar", "년주": "Year Pillar",
    "월주": "Month Pillar", "시주": "Hour Pillar",
    "용신": "Favorable Element", "희신": "Supporting Element",
    "기신": "Unfavorable Element", "한신": "Draining Element",
    "구신": "Restraining Element",
    "격국": "Chart Structure", "신살": "Star",
    "십신": "Ten Gods", "대운": "Major Luck", "세운": "Annual Luck",
    "월운": "Monthly Luck", "일운": "Daily Luck", "배우자궁": "Spouse Palace",
    "도화살": "Peach Blossom", "역마살": "Post Horse", "화개살": "Canopy",
    "공망": "Void", "양인격": "Blade Structure",
    "식상생재": "output-feeds-wealth", "상관견관": "rebellion-against-authority",
    "편인식신": "over-preparation-blocks-output", "겁재奪財": "peer-drains-wealth",
    "겁재탈재": "peer-drains-wealth", "재생관": "wealth-funds-status",
    "재다신약": "much-wealth-weak-self", "인성생신": "resource-strengthens-self",
    "진상관": "true Hurting Officer", "가상관": "provisional Hurting Officer",
    "재고": "wealth storehouse", "택일": "date selection",
    "풍수": "Fengshui", "양택": "dwelling-siting Fengshui", "팔택": "eight mansions",
    "하도낙서": "Hetu-Luoshu", "오행 방위": "element directions",
    "황도길일": "yellow-way auspicious days", "손없는날": "no-ghost days",
    "건제십이신": "twelve day-officers", "이사": "moving house", "개업": "business opening",
    "상생": "generating cycle", "상극": "controlling cycle",
    "입춘": "Lichun (Feb 4)", "소한": "Xiaohan", "대설": "Daxue", "경칩": "Jingzhe",
    "청명": "Qingming", "입하": "Lihai", "망종": "Mangzhong", "소서": "Xiaoshu",
    "입추": "Liqiu", "백로": "Bailu", "한로": "Hanlu", "입동": "Lidong",
    "십이운성": "Twelve Life Stages", "12운성": "Twelve Life Stages",
    "정관": "Direct Officer", "편관": "Seven Killings",
    "비겁": "Companion", "식상": "Output", "재성": "Wealth", "관성": "Authority",
    "인성": "Resource", "장생": "Long Life", "목욕": "Bathing",
    "관대": "Coming of Age", "건록": "Strong / Earning", "제왕": "Peak",
    # 12운성 stage names (병/사/묘/양) collide with single-syllable
    # stem/branch Korean names. Engine emits stage names in every pillar
    # table, so these win; colliding stem/branch syllables are dropped below.
    "쇠": "Decline", "병": "Illness", "사": "Death", "묘": "Tomb",
    "절": "Cutoff", "태": "Embryo", "양": "Nurturing",
    "갑": "Gap (Yang Wood)", "을": "Eul (Yin Wood)",
    "정": "Jeong (Yin Fire)",
    "무": "Mu (Yang Earth)", "기": "Gi (Yin Earth)",
    "경": "Gyeong (Yang Metal)", "신": "Sin (Yin Metal)",
    "임": "Im (Yang Water)", "계": "Gye (Yin Water)",
    "자": "Ja (Rat)", "축": "Chuk (Ox)",
    "인": "In (Tiger)",
    "진": "Jin (Dragon)",
    "오": "O (Horse)", "미": "Mi (Goat)",
    "유": "Yu (Rooster)",
    "술": "Sul (Dog)", "해": "Hae (Pig)",
    "오행": "Five Elements",
    "목": "Wood", "화": "Fire", "토": "Earth", "금": "Metal", "수": "Water",
    "음": "Yin",
    "양목": "Yang Wood", "음목": "Yin Wood",
    "양화": "Yang Fire", "음화": "Yin Fire",
    "양토": "Yang Earth", "음토": "Yin Earth",
    "양금": "Yang Metal", "음금": "Yin Metal",
    "양수": "Yang Water", "음수": "Yin Water",
    "신강": "strong", "신약": "weak",
    "적천수": "Jeokcheon-su (classical reference)",
    "연해자평": "Yeonhae-japyeong (classical reference)",
    "궁통보감": "Gungtong-bogam (favorable-element method)",
    "명리정종": "Myeongri-jeongjong (Korean school)",
    "명리": "Myeongri (Korean Saju tradition)",
    "인성격": "Resource Structure", "식상격": "Output Structure",
    "재격": "Wealth Structure", "관격": "Officer Structure",
    "충": "clash", "합": "combination", "형": "punishment",
    "파": "break",
    "육합": "six-combination", "삼합": "three-harmony",
    "일지": "Day Branch",
    # ── Marriage compatibility (궁합) terms ──────────────────────────────────
    "궁합": "Compatibility",
    "두 분 궁합": "Compatibility Reading",
    "合婚": "Marriage Compatibility",
    "종합 점수": "Composite Score",
    "종합": "Composite",
    "점수": "Score",
    "평가": "Verdict",
    "한눈에 보기": "At a Glance",
    "한눈에": "at a glance",
    "보기": "overview",
    "심정": "Verdict",
    "주의 사항": "Cautions",
    "주의": "caution",
    "사항": "points",
    "관찰 사항": "Observations",
    "관찰": "observation",
    "긍정적 요소": "Favorable Factors",
    "긍정적": "positive",
    "요소": "factors",
    "두 사람의 관계 성향": "Relationship Character",
    "두": "two",
    "사람의": "people's",
    "성향": "character",
    "실천 지침": "Practical Guidance",
    "실천": "practical",
    "지침": "guidance",
    "맺음말": "Closing Note",
    "다음 단계": "Next Steps",
    "다음": "next",
    "단계": "steps",
    "조화": "Harmony",
    "동기": "Synchrony",
    "음양": "Yin-Yang",
    "팔자": "Eight Characters",
    # Sub-system labels
    "일간합": "Day-Stem Combination",
    "천간합": "Heavenly-Stem Combination",
    "일지 합충형파해": "Day-Branch Interactions",
    "합충형파해": "Combination / Clash / Punishment / Break / Harm",
    "납음오행": "Nayin Five Elements",
    "용신 궁합": "Favorable-Element Compatibility",
    "일주 궁합": "Day-Pillar Compatibility",
    "결합 오행": "Combined Elements",
    "십신 교차": "Ten-God Cross",
    "대운·세운 동기": "Luck Synchrony",
    "신살 궁합": "Star Compatibility",
    "음양 조화": "Yin-Yang Harmony",
    "띠 궁합": "Zodiac Compatibility",
    "띠": "Zodiac",
    # Branch interactions
    "육합": "Six Harmony",
    "육충": "Six Clash",
    "육해": "Six Harm",
    "육파": "Six Break",
    "반합": "Half Harmony",
    "상충": "clashing",
    "상합": "harmonizing",
    "상구": "mutually beneficial",
    "상해": "harmful",
    "상대": "neutral pair",
    "자형": "self-punishment",
    "삼형": "three-punishment",
    # Descriptors
    "배우자궁": "Spouse Palace",
    "배우자 복덕": "spouse virtue",
    "일지 본기": "day-branch main hidden stem",
    "공급": "supply",
    "공급 양호": "good supply",
    "양호": "favorable",
    "과다": "excess",
    "약함": "weak",
    "강함": "strong",
    "충분": "sufficient",
    "균형 양호": "well-balanced",
    "불균형": "unbalanced",
    "동일": "same",
    "상이": "different",
    "방향": "direction",
    "시작": "starting",
    "시작 대운": "starting Major Luck",
    "시작 대운 상생": "starting Major Luck mutual generation",
    "대운 방향 상이": "different Major-Luck direction",
    "대운 방향 동일": "same Major-Luck direction",
    "상생": "mutual generation",
    "조후": "climate",
    "점술": "fortune-telling",
    "편의": "familiar ease",
    "서로 용신이 되는": "mutually supplying favorable elements",
    "비견배우": "companion-spouse",
    "동등한 관계": "an equal bond",
    "때로 경쟁": "sometimes competitive",
    "여부": "whether",
    "권인성": "Kwon In-seong",
    "곽임성": "Kwak Im-seong",
    "정봉재": "Jeong Bong-jae",
    "송기영": "Song Gi-yeong",
    "서전구미록": "Seojeon-gumirok",
    "자평진전": "Japyeong-jinjeon",
    "명리정종": "Myeongri-jeongjong",
    "도화": "Peach Blossom",
    "역마": "Post Horse",
    "화개": "Canopy",
    "천을": "Heavenly Noble",
    "홍양교차": "Hongyeom-Yangin cross",
    "결합에서 충분": "sufficient in the union",
    "지지": "Earthly Branches",
    "관계": "relationship",
    "사람의": "of the people",
    "성향": "character",
}

# Hanja single-character (for inline like 甲, 乙 inside non-fully-translated contexts)
HANJA_MAP = {
    **{k: v.split(" (")[0] for k, v in STEM_MAP.items()},
    **{k: v.split(" (")[0] for k, v in BRANCH_MAP.items()},
    # 干支 / 地支 / 五行 / 陰陽 / 命 etc.
    "干": "Stem", "支": "Branch", "干支": "Stem-Branch",
    "五行": "Five Elements", "陰": "Yin", "陽": "Yang",
    "風水": "Fengshui", "陽宅": "dwelling-siting Fengshui", "河圖洛書": "Hetu-Luoshu",
    "移徙": "moving house", "開業": "business opening", "擇日": "date selection",
    "陰陽": "Yin-Yang", "命": "destiny", "理": "principles",
    "運": "luck", "星": "star", "格": "structure",
    "神": "spirit", "殺": "killer", "煞": "evil",
    "傷": "hurt", "食": "food", "財": "wealth",
    "官": "officer", "印": "seal", "印星": "Resource",
    "比": "compare", "劫": "rob", "肩": "shoulder",
    "十": "ten", "十二": "twelve",
    "長": "long", "生": "life", "沐": "bathe", "浴": "bath",
    "冠": "crown", "帶": "belt", "健": "healthy", "祿": "salary",
    "帝": "emperor", "旺": "flourishing", "衰": "decline",
    "病": "illness", "死": "death", "墓": "tomb", "絕": "cutoff",
    "胎": "embryo", "養": "nurture",
    "局": "framework",
    "從": "follow", "化": "transform", "建": "build",
    "建祿格": "Strong Self Structure", "羊刃格": "Blade Structure",
    "從格": "Following Structure", "化格": "Transformation Structure",
    "正": "direct", "偏": "indirect", "七": "seven",
    "正官": "Direct Officer", "偏官": "Seven Killings",
    "正印": "Direct Resource", "偏印": "Indirect Resource",
    "正財": "Direct Wealth", "偏財": "Indirect Wealth",
    "傷官": "Hurting Officer", "食神": "Eating God",
    "比肩": "Pillar", "劫財": "Rob Wealth",
    # Marriage-compatibility Hanja
    "宮合": "Compatibility",
    "合婚": "Marriage Compatibility",
    "四柱八字": "Four Pillars",
    "八字": "Eight Characters",
    "四": "four",
    "天干合": "Heavenly-Stem Combination",
    "納音五行": "Nayin Five Elements",
    "用神": "Favorable Element",
    "日柱": "Day Pillar",
    "結合": "Union",
    "十神": "Ten Gods",
    "交叉": "Cross",
    "大運": "Major Luck",
    "歲運": "Annual Luck",
    "月運": "Monthly Luck",
    "日運": "Daily Luck",
    "同期": "Synchrony",
    "神殺": "Star",
    "陰陽": "Yin-Yang",
    "調和": "Harmony",
    "天河水": "Heavenly River Water",
    "爐中火": "Furnace Fire",
    "寒": "cold", "熱": "hot",
    # Five Element Hanja (often appear after stem names like 辛金)
    "金": "Metal", "木": "Wood", "水": "Water", "火": "Fire", "土": "Earth",
}


# Capturing group is intentional: re.split returns non-CJK and CJK runs alternately.
_CJK_RE = re.compile(
    "(["
    "　-〿"        # CJK Symbols and Punctuation
    "一-鿿"        # CJK Unified Ideographs (Hanja, Kanji, Hanzi)
    "가-힯"        # Hangul Syllables
    "＀-￯"        # Halfwidth and Fullwidth Forms (incl. fullwidth ASCII)
    "]+)"
)

# Internal audit citations such as *(see knowledge/05-ten-gods.md)* are kept in
# the markdown source for reader traceability, but stripped from client PDFs.
# Also strips bare `knowledge/...` backtick references used in the
# `*Chart-derived first draft — verify against ...*` review notes so that
# internal source paths never reach the client.
_SOURCE_CITATION_RE = re.compile(r"[ \t]*\*\(see\s[^)]+\)\*")
# Parenthetical citations that name a knowledge/ path but omit the leading "see"
# (a form a few hand-written reader docs use): `*(knowledge/12 §Element → …)*`.
_SOURCE_CITATION_NOSEE_RE = re.compile(r"[ \t]*\*\(knowledge/[^)]+\)\*")
# Italic "see" citations WITHOUT parens, e.g. `*see knowledge/11-gunghap.md §A*`
# (the form the compat sub-system blocks use). Strip the whole italic span so the
# client PDF doesn't show a dangling "see §A" after the path is removed.
_SOURCE_SEE_RE = re.compile(r"\*see [^*\n]*(?:§|knowledge)[^*\n]*\*")
# Bare `knowledge/...` references (full form with `.md`, or the short
# `knowledge/13` form used in hand-written reader docs), backtick-wrapped or not,
# optionally followed by a `§Section` citation clause up to the closing backtick.
_SOURCE_PATH_RE = re.compile(
    r"`?knowledge/\d{1,2}(?:[A-Za-z0-9_\-./]*\.md)?"
    r"(?: *§[^`)\n]*)?`?"
)


# Combined translation terms, longest first. We keep Korean phrases ahead of
# Hanja so that Hangul terms win when a run could match either; within a script
# longer keys still win because of the sort by length.
_TRANSLATION_TERMS = sorted(
    {**KOR_REPL, **HANJA_MAP, **TENGOD_MAP}.items(),
    key=lambda kv: (-len(kv[0]), kv[0]),
)


# Placeholder sentinel for parenthesized English text that should not be re-translated.
_PLACEHOLDER_RE = re.compile(r"\x00(\d+)\x00")


def _protect_parenthetical_english(text: str) -> tuple[str, list[str]]:
    """Replace pure-ASCII parentheticals with placeholders so translation skips them.

    Parentheticals that also contain CJK (e.g. "(the heart of 궁합)") are left
    untouched — the Korean/Hanja inside them must be translated by the normal
    path, otherwise the final CJK-stripping pass would erase it.
    """
    placeholders: list[str] = []

    def replace(m: "re.Match") -> str:
        inner = m.group(0)
        # Skip if the parenthetical contains any CJK character.
        if _CJK_RE.search(inner):
            return inner
        placeholders.append(inner)
        return f"\x00{len(placeholders) - 1}\x00"

    # Match parentheses that contain at least one ASCII letter (treat as already
    # translated English). This catches "(Direct Officer)", "(Annual Luck)", etc.
    protected = re.sub(r"\([A-Za-z][^\)]*\)", replace, text)
    return protected, placeholders


def _translate_cjk_run(run: str) -> str:
    """Translate one contiguous CJK run using longest-match tokenization."""
    tokens: List[str] = []
    i = 0
    n = len(run)
    while i < n:
        matched = False
        for k, v in _TRANSLATION_TERMS:
            if run.startswith(k, i):
                tokens.append(v)
                i += len(k)
                matched = True
                break
        if not matched:
            # Unmapped CJK character — drop it (the final _CJK_RE pass will catch it).
            i += 1
    # Join translated tokens with a single space so adjacent Hanja pairs like
    # 丙午 do not collapse into "BingO".
    return " ".join(tokens)


def translate_inline(text: str) -> str:
    """Replace Korean/Hanja terms with English.

    Improvements over the old global `.replace` loop:
      - Longest-match tokenization within CJK runs prevents adjacent Hanja pairs
        (e.g. 丙午, 辛未) from collapsing into "BingO" / "SinMetal".
      - A space is inserted between translated tokens.
      - Text already inside English parentheses is protected from re-translation,
        and exact duplicates like "Direct Officer (Direct Officer)" are collapsed.
    """
    protected, placeholders = _protect_parenthetical_english(text)

    # Split into CJK runs, placeholders, and plain text.
    parts: List[str] = []
    cursor = 0
    for m in re.finditer(_PLACEHOLDER_RE.pattern, protected):
        # Plain/CJK text before placeholder
        before = protected[cursor:m.start()]
        if before:
            # CJK runs inside the plain text
            subparts = _CJK_RE.split(before)
            for j, sub in enumerate(subparts):
                if j % 2 == 1 and sub:
                    parts.append(_translate_cjk_run(sub))
                else:
                    parts.append(sub)
        parts.append(m.group(0))  # placeholder
        cursor = m.end()
    # Tail
    before = protected[cursor:]
    if before:
        subparts = _CJK_RE.split(before)
        for j, sub in enumerate(subparts):
            if j % 2 == 1 and sub:
                parts.append(_translate_cjk_run(sub))
            else:
                parts.append(sub)

    # Restore placeholders, dropping exact duplicates that would produce
    # "Direct Officer (Direct Officer)" or "Annual Luck (Annual Luck)".
    out_parts: List[str] = []
    for part in parts:
        m = _PLACEHOLDER_RE.match(part)
        if not m:
            out_parts.append(part)
            continue
        placeholder = placeholders[int(m.group(1))]
        # Strip parentheses and normalize whitespace for comparison.
        inner = placeholder[1:-1].strip()
        # If the immediately preceding non-empty text already ends with the
        # same English phrase (e.g. "正官 (Direct Officer)"), drop the
        # parenthetical to avoid "Direct Officer (Direct Officer)" duplication.
        preceding_text = ""
        for prev in reversed(out_parts):
            stripped = prev.strip()
            if stripped:
                preceding_text = stripped
                break
        preceding_words = preceding_text.split()
        inner_words = inner.split()
        if (
            len(inner_words) <= len(preceding_words)
            and preceding_words[-len(inner_words):] == inner_words
        ):
            continue
        out_parts.append(placeholder)

    out = "".join(out_parts)
    # Final safety net: drop any CJK character the maps missed.
    out = _CJK_RE.sub(" ", out)
    # Collapse runs of spaces from the substitution.
    out = re.sub(r"  +", " ", out)
    out = re.sub(r" \.", ".", out)
    out = re.sub(r" ,", ",", out)
    # Insert a space between adjacent Latin words that got concatenated by
    # CJK-to-English translation (e.g. "ADay Branch" -> "A Day Branch").
    out = re.sub(r'([a-zA-Z])([A-Z][a-z])', r'\1 \2', out)
    return out.strip()


def _strip_sources_section(text: str) -> str:
    """Remove a standalone ## Sources / ## Sources & Limits section.

    Stops at the next Markdown heading of the same or higher rank so that
    content after a Sources heading is preserved. Matches the behavior of
    ``combine_candidate_report.py``.
    """
    match = re.search(r"\n(#+)\s+Sources\b", text, flags=re.IGNORECASE)
    if not match:
        return text
    start = match.start()
    rank = len(match.group(1))
    next_heading = re.search(r"\n#{1," + str(rank) + r"}\s+\S", text[match.end():])
    if next_heading:
        end = match.end() + next_heading.start()
    else:
        end = len(text)
    return text[:start].rstrip() + text[end:]


def strip_source_citations(text: str) -> str:
    """Remove internal source citations and Sources sections from client-facing output.

    Handles the patterns used in the markdown:
      1. Inline parenthetical citations: *(see knowledge/05-ten-gods.md)*
      2. Non-parenthetical italic "see <path> §X" citations (compat blocks)
      3. Bare knowledge/ path references (backtick-wrapped or bare)
      4. Standalone "## Sources" sections
      5. Bracketed [UNCERTAIN: ...] scholarly disagreement markers.
    """
    # 1. Drop inline parenthetical citations.
    out = _SOURCE_CITATION_RE.sub("", text)
    out = _SOURCE_CITATION_NOSEE_RE.sub("", out)
    # 1b. Drop non-parenthetical italic "see <path> §X" citations (compat blocks).
    out = _SOURCE_SEE_RE.sub("", out)
    # 2. Drop bare knowledge/ path references (with any trailing `§Section` clause).
    out = _SOURCE_PATH_RE.sub("", out)
    # 3. Drop any "## Sources" / "## Sources & Limits" section.
    # Stop at the next Markdown heading of the same or higher rank so content
    # after a Sources heading (e.g. a follow-up "## Focus Requested...") is
    # preserved. Matches the behavior of combine_candidate_report.py.
    out = _strip_sources_section(out)
    # 4. Drop bracketed [UNCERTAIN: ...] markers so they do not leak into client PDFs.
    out = re.sub(r"\s*\[UNCERTAIN:[^\]]*\]", "", out, flags=re.IGNORECASE)
    # 5. Drop engine reviewer notes so they never reach a client PDF even if a
    # hand-written .md still carries them (the engine no longer emits these for
    # client tiers — see premium_report._reviewer_note):
    #   - blockquote form:  >*Chart-derived first draft — verify against ...*
    #   - compat bullet:    - *Engine note:* Heuristic only; final 용신 ...
    out = re.sub(r"^\s*>\s*\*Chart-derived.*?\*\s*$", "", out, flags=re.MULTILINE)
    out = re.sub(r"^\s*[-*]\s*\*Engine note:\*.*$", "", out, flags=re.MULTILINE)

    out = re.sub(r"  +", " ", out)
    out = re.sub(r"\n\n\n+", "\n\n", out)
    return out


# Pattern used to strip `[ENGINE DRAFT — REVIEW REQUIRED]` markers from
# client-facing output. The engine emits this tag to flag prose that needs
# human review; the backends must drop it so clients never see the marker.
# The inline regex consumes only single-space whitespace (never newlines) so
# the surrounding paragraph structure is preserved.
_ENGINE_DRAFT_INLINE_RE = re.compile(r" ?\[ENGINE DRAFT — REVIEW REQUIRED\] ?")
_ENGINE_DRAFT_LINE_RE = re.compile(
    r"^\s*>\s*\[ENGINE DRAFT — REVIEW REQUIRED\]\s*$", re.MULTILINE
)


def strip_engine_drafts(text: str) -> str:
    """Remove all `[ENGINE DRAFT — REVIEW REQUIRED]` markers from client output.

    The engine inserts these tags inline or as standalone blockquote lines so a
    reader can spot which prose still needs human review. Once the report is
    rendered to PDF (or otherwise sent to a client) the markers must not leak.

    Two patterns are stripped:
      1. Inline markers: `[ENGINE DRAFT — REVIEW REQUIRED] <prose>`
         The marker (and its immediately-adjacent single-space whitespace) is
         removed, preserving the prose. Newlines are never consumed so the
         paragraph structure survives.
      2. Standalone blockquote lines containing only the marker
         (e.g. `> [ENGINE DRAFT — REVIEW REQUIRED]`) — the entire line is removed.
    """
    # 1. Standalone marker-only lines — drop the line entirely.
    out = _ENGINE_DRAFT_LINE_RE.sub("", text)
    # 2. Inline markers — keep the surrounding prose and any newlines.
    out = _ENGINE_DRAFT_INLINE_RE.sub("", out)
    out = re.sub(r"  +", " ", out)
    out = re.sub(r"\n\n\n+", "\n\n", out)
    return out
