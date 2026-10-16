"""Shared helpers for the HTML/Playwright PDF generator.

Contains the Korean/Hanja → English translation maps and the CJK-stripping
logic originally created for the reportlab-based `md_to_saju_pdf.py`.
Both PDF generators import these maps so translations stay identical.
"""
from __future__ import annotations

import re
from typing import List, Optional

from saju_engine.report_data import ELEMENT_COLORS as ELEMENT_COLORS
from saju_engine.report_data import ELEMENT_EMOJI as ELEMENT_EMOJI


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
    "비견": "Companion", "겁재": "Rob Wealth (Companion)",
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
    "청명": "Qingming", "입하": "Lixia (Start of Summer)", "망종": "Mangzhong", "소서": "Xiaoshu",
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
    "삼합": "three-harmony",
    "일지": "Day Branch",
    # ── Marriage compatibility (궁합) terms ──────────────────────────────────
    "궁합": "Compatibility",
    "合婚": "Marriage Compatibility",
    "종합 점수": "Composite Score",
    "종합": "Composite",
    "점수": "Score",
    "평가": "Verdict",
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
    "도화": "Peach Blossom",
    "역마": "Post Horse",
    "화개": "Canopy",
    "천을": "Heavenly Noble",
    "홍양교차": "Hongyeom-Yangin cross",
    "결합에서 충분": "sufficient in the union",
    "지지": "Earthly Branches",
    "관계": "relationship",
    # Added 2026-09-26 (report regeneration after the 2026-09-25 engine audit):
    # terms that fell through to the CJK-stripping pass in client PDFs.
    "본": "main", "중": "middle", "여": "residual",
    "본기": "main qi", "중기": "middle qi", "여기": "residual qi",
    "방합": "Directional Harmony", "천간충": "Stem Clash", "천간": "Heavenly Stem",
    "합이불화": "binding without transforming", "이불화": "without transforming",
    "합거": "combined away", "파격": "broken structure", "관살혼잡": "mixed officers",
    "정편관혼잡": "mixed officers",
    "비견격": "Companion Structure", "겁재격": "Robber Structure",
    "식신격": "Eating God Structure", "상관격": "Hurting Officer Structure",
    "편재격": "Indirect Wealth Structure", "정재격": "Direct Wealth Structure",
    "편관격": "Seven Killings Structure", "정관격": "Direct Officer Structure",
    "편인격": "Indirect Resource Structure", "정인격": "Direct Resource Structure",
    "만세력": "manseryeok (Korean perpetual calendar)", "방위": "direction",
    "야자시": "late Rat hour", "억부": "strength-balance", "운성": "-Stage Cycle",
    "천을귀인": "Heavenly Noble", "천덕귀인": "Heavenly Virtue", "월덕귀인": "Monthly Virtue",
    "원진": "Deep Grudge", "귀문관": "Ghost Gate", "처성": "wife star", "부성": "husband star",
    "지살": "Movement Star", "연살": "Annual Star", "월살": "Withering Star",
    "고초살": "Withering Star", "천살": "Heaven Star", "재살": "Calamity Star",
    "겁살": "Robbery Star", "망신": "Loss-of-Face", "장성": "General Star", "반안": "Saddle Star",
    "자영업": "self-employment",
    "홍염": "Red Flame", "백호": "White Tiger", "양인": "Blade Star",
    # Ten-stem combination names — without these, 병 in "병신합수" matched the
    # 12-stage term 병 (病, "Illness").
    "갑기합토": "Gap-Gi Earth combination", "을경합금": "Eul-Gyeong Metal combination",
    "병신합수": "Byeong-Sin Water combination", "정임합목": "Jeong-Im Wood combination",
    "무계합화": "Mu-Gye Fire combination",
    # Added 2026-10-04 (P5 task 1): terms the golden reports use that previously
    # fell through to silent CJK deletion. Glosses follow knowledge/00-glossary.md
    # (신살 -> Star, 득령 -> in-season support) and knowledge/11-gunghap.md (납음 -> Nayin).
    # (The generic words 결합/교차/균형/배우자/원소/일부/일치/혼잡 are bounded
    # phrase rules below, not bare terms: as terms they fired inside unrelated
    # Korean words, e.g. 일부러 -> "partial러", 불일치 -> "불match".)
    "괴강": "Kuigang Star", "납음": "Nayin", "득령": "in-season support",
    "문창귀인": "Literary Star", "복덕": "blessing and virtue",
    "쌍화개": "double Canopy",
}

# Phrase-level rules applied BEFORE per-term CJK tokenization. CJK runs split on
# ASCII spaces, so multi-word Korean phrases and particle constructions can
# only be handled here. Bare particles (는 에 의 고 분) are deliberately NOT in
# the term maps: global substitution garbles ordinary words (의미, 분석, 사고가).

# Korean-boundary helpers: a Korean term only counts as a word when no Hangul
# touches it (so 두 분 matches "두 분" but not "두 분석", and 사고 matches the
# standalone term but not 사고방식). _KP additionally allows one trailing
# case particle (은/는/이/가/을/를/의/와/과/도/로/에/에서/으로).
_K0 = r"(?<![가-힣])"
_K1 = r"(?![가-힣])"
# Particle-tolerant end boundary. `_KP_RE` is used to build `_KW_RE` patterns
# (see translate_inline) that CONSUME the optional particle, so a term like
# 혼잡은 becomes "mixed" with no leftover 을/은/는 for the CJK tokenizer to
# garble (P5-hangul-tokens).
_KP_RE = r"(?:에서|으로|은|는|이|가|을|를|의|와|과|도|로|에)?(?![가-힣])"
_KP = r"(?=" + _KP_RE + r")"  # lookahead form, kept for direct uses


def _kw(term: str) -> "re.Pattern":
    """Compile a bounded Korean-word pattern that consumes a trailing particle.

    The particle is consumed (not just looked ahead) so ``혼잡은`` -> ``mixed``
    with no leftover ``은`` (P5-hangul-tokens)."""
    return re.compile(_K0 + re.escape(term) + _KP_RE)


def _pair_union_gloss(m: "re.Match") -> str:
    gloss = m.group(1)
    return gloss if re.search(r"combination|pair|couple", gloss) else gloss + " union"


# Rules applied BEFORE the "Hangul (English gloss)" collapse, for strings whose
# English parenthetical would otherwise swallow/misplace the Korean phrase.
_PRE_RULES: List[tuple] = [
    # Ten-god pair verdicts (compat.py _TENGOD_*_PAIRS)
    (re.compile(r"서로 신뢰·안정 — 가장 좋은 궁합 \(best\)"),
     "mutual trust and stability — the best match"),
    # Day-pillar pair names (compat.py _GOOD_PAIRS): "따뜻한 결합 (warm combination)"
    (re.compile(r"천생 부부 \(heaven-made couple\) — 1순위"),
     "heaven-made couple (top-ranked pair)"),
    (re.compile(r"(?:따뜻한|정열적|성장|안정적|균형 잡힌|정밀한|잠재력|용과 봉황) 결합 \(([A-Za-z][^()]*)\)"),
     _pair_union_gloss),
    (re.compile(r"동등한 관계, 때로 경쟁 \(an equal bond, sometimes competitive\)"),
     "an equal bond, sometimes competitive"),
    # Classical-text titles glossed with their Hanja: keep the Korean-term gloss only.
    (re.compile(r"(적천수|연해자평|궁통보감|명리정종|자평진전) \((?:滴天髓|淵海子平|窮通寶鑑|命理正宗|子平眞詮)\)"),
     r"\1"),
    # Ten-god terms glossed with their Hanja where the two map to DIFFERENT
    # English (정관 -> "Direct Officer (Authority)" but 正官 -> "Direct Officer"),
    # so the later placeholder dedup misses it and doubles the gloss
    # (P5-hangul-tokens): drop the Hanja parenthetical, keep the term.
    (re.compile(r"(정관|편관|정재|편재|정인|편인|비견|겁재|식신|상관)"
                r" \((?:正官|偏官|正財|偏財|正印|偏印|比肩|劫財|食神|傷官)\)"),
     r"\1"),
    # Organ pairs after an English organ gloss: "liver/gallbladder (간/담)"
    (re.compile(r" \((?:간/담|심/소장|비/위|폐/대장|신/방광)\)"), ""),
]

_ELEMENT = r"(Wood|Fire|Earth|Metal|Water)"
_HAN = "[\u4e00-\u9fff]"
_PHRASE_RULES: List[tuple] = [
    # "A에 B의 기신 Metal 과다" -> excess of B's Unfavorable Element Metal in A
    (re.compile(r"\b([AB])에 ([AB])의 기신 " + _ELEMENT + r" 과다"),
     "excess of \\2\u2019s Unfavorable Element \\3 in \\1"),
    (re.compile(r"\b([AB])에 ([AB])의 기신"),
     "\\2\u2019s Unfavorable Element in \\1"),
    (re.compile(r"\b([AB])의 일간 원소"), "\\1\u2019s Day Master element"),
    (re.compile(r"\b([AB])의 기신"), "\\1\u2019s Unfavorable Element"),
    (re.compile(r"\b([AB])의 용신"), "\\1\u2019s Favorable Element"),
    # "A (辛)는 B (壬)의 정인" tag -> "A (辛) is B (壬)'s 정인"
    (re.compile(r"\b([AB]) \((" + _HAN + r")\)는 ([AB]) \((" + _HAN + r")\)의 "),
     "\\1 (\\2) is \\3 (\\4)\u2019s "),
    # "(38% 양)" is the Yang share of the combined chart, not the 12-stage 양.
    (re.compile(r"\((\d+(?:\.\d+)?)% 양\)"), r"(\1% Yang)"),
    (re.compile(r"\((\d+(?:\.\d+)?)% 음\)"), r"(\1% Yin)"),
    # ── Compat (궁합) engine strings — see src/saju_engine/compat.py ─────────
    # §A day-stem combination flags
    (re.compile(r"합화 원소 " + _ELEMENT + r" 월령 양호"),
     "transformed element \\1 is in season (favorable)"),
    (re.compile(r"합화 원소 " + _ELEMENT + r" 월령 불분명 \(학파마다 판단이 갈립니다\)"),
     "transformed element \\1 — seasonal support unclear (schools judge it differently)"),
    (re.compile(r"간섭 월지: "), "interference in the month branch: "),
    (re.compile(r"간섭 존재: "), "interference present: "),
    (_kw("간섭"), "interference"),
    # §B/§D yongshin cross-supply narrative
    (re.compile(r"서로 용신이 되는"), "each serves as the other\u2019s Favorable Element"),
    (re.compile(r"일지 궁"), "Day-Branch palace"),
    # §F combined elements
    (re.compile(r"결합에서 결핍"), "missing in the union"),
    (re.compile(r"결합 결핍"), "combined deficiency"),
    (re.compile(r"결합 오행 불균형 심함"), "combined Five Elements severely unbalanced"),
    (_kw("심함"), "severe"),
    (_kw("결핍"), "deficiency"),
    # §G ten-god cross: verdict phrases and spouse-star tags
    (re.compile(r"따뜻한 부부 — 재물·안정·질서"), "warm couple — wealth, stability, order"),
    (re.compile(r"부드러운 부부 — 표현·보호"), "gentle couple — expression and protection"),
    (re.compile(r"사회적 부부 — 권위·안정"), "social couple — authority and stability"),
    (re.compile(r"강렬한 부부 — 둘 다 압박적"), "intense couple — both pressuring"),
    (re.compile(r"갈등 부부 — 둘 다 날카로움"), "conflict-prone couple — both sharp-edged"),
    (re.compile(r"갈등 부부 — 둘 다 갈등"), "conflict-prone couple — both prone to conflict"),
    (re.compile(r"\b([AB])\(남\)의 배우자 지표 "), "\\1 (male)\u2019s spouse star "),
    (re.compile(r"\b([AB])\(여\)의 배우자 지표 "), "\\1 (female)\u2019s spouse star "),
    (re.compile(r"(?<![A-Za-z가-힣])([AB])는 ([AB])의 "), "\\1 is \\2\u2019s "),
    (re.compile(r"비견배우"), "companion-spouse"),
    # §I compatibility star overlays
    (re.compile(r"쌍도화"), "double Peach Blossom"),
    (re.compile(r"쌍역마"), "double Post Horse"),
    (re.compile(r"쌍양인"), "double Blade Star"),
    (re.compile(r"쌍홍염"), "double Red Flame"),
    (re.compile(r"도화스쳐"), "Peach Blossom strike"),
    (re.compile(r"귀인배우"), "noble partner"),
    # Branch/star names the premium deep report glosses with Hanja
    (re.compile(r"백호 \(白虎\)"), "White Tiger Star"),
    (re.compile(r"홍염 \((?:紅艶|紅艷)\)"), "Red Flame Star"),
    (re.compile(r"양인 \(羊刃\)"), "Blade Star"),
    # 사고 (四庫) storehouse branches — only in the 辰戌丑未 sense, never ordinary 사고
    (re.compile(r"\(사고\)"), "(storehouse)"),
    (re.compile(_K0 + r"사고 지지"), "storehouse branch"),
    # Month-command / pattern vocabulary (patterns.py, strength.py)
    (_kw("월령"), "month command"),
    (_kw("투출"), "emergence"),
    (_kw("통근"), "rooting"),
    (_kw("종격"), "Following Structure"),
    (re.compile(_K0 + r"두 분 궁합" + _K1), "Couple Compatibility"),
    (re.compile(_K0 + r"두 분" + _KP), "the couple"),
    (re.compile(_K0 + r"한눈에 보기" + _K1), "At a Glance"),
    (re.compile(_K0 + r"재성 혼잡" + _K1), "Mixed Wealth"),
    (re.compile(_K0 + r"결합에서" + _K1), "in the union"),
    (_kw("결합"), "combined"),
    (_kw("교차"), "cross"),
    (_kw("균형"), "balance"),
    (_kw("배우자"), "spouse"),
    (_kw("원소"), "element"),
    (_kw("일부"), "partial"),
    (_kw("일치"), "match"),
    (_kw("혼잡"), "mixed"),
]


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
    "比肩": "Companion", "劫財": "Rob Wealth",
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
    "調和": "Harmony",
    "天河水": "Heavenly River Water",
    "爐中火": "Furnace Fire",
    "寒": "cold", "熱": "hot",
    # Added 2026-09-26 (report regeneration after the 2026-09-25 engine audit):
    # Hanja that previously fell through to the CJK-stripping pass, leaving
    # dangling "()" in client PDFs.
    "合": "combination", "沖": "clash", "刑": "punishment", "破": "break",
    "天干": "Heavenly Stem", "天干沖": "Stem Clash", "半合": "Half Harmony",
    "三合": "Three Harmony", "六合": "Six Harmony", "合而不化": "binding without transforming",
    "空亡": "Void", "桃花": "Peach Blossom", "驛馬": "Post Horse", "華蓋": "Canopy",
    "藏干": "hidden stems", "節氣": "solar term", "日干": "Day Master",
    "喜神": "Supporting Element", "忌神": "Unfavorable Element", "閒神": "Draining Element",
    "天乙貴人": "Heavenly Noble", "天德貴人": "Heavenly Virtue", "月德貴人": "Monthly Virtue",
    "怨嗔": "Deep Grudge", "鬼門關": "Ghost Gate", "地煞": "Movement Star", "年煞": "Annual Star",
    "月煞": "Withering Star", "天煞": "Heaven Star", "災煞": "Calamity Star", "亡神": "Loss-of-Face",
    "絶": "Extinction", "財庫": "wealth storehouse", "夜子時": "late Rat hour",
    # Added 2026-10-04 (P5 task 1): Hanja glosses for the golden reports.
    "六害": "Six Harm", "將星": "General Star", "將": "General",
    "文昌貴人": "Literary Star", "本氣": "main qi", "魁罡": "Kuigang Star",
    # Nayin (納音) tone names — see knowledge/11-gunghap.md §C.
    "白蠟金": "White Wax Metal", "石榴木": "Pomegranate Wood",
    "釵釧金": "Hairpin Metal", "長流水": "Long-Flowing Water",
    # The 30 Nayin (納音) names — glosses follow knowledge/11-gunghap.md §C and
    # nayin.NAYIN_KOREAN (the engine's own English glosses). The five names
    # above keep their earlier (golden-snapshotted) wording.
    "海中金": "Gold in the Sea", "大林木": "Forest Wood", "路傍土": "Roadside Earth",
    "劍鋒金": "Sword-Edge Metal", "山頭火": "Mountain-Top Fire",
    "澗下水": "Water Under the Stream", "城頭土": "City-Wall Earth",
    "楊柳木": "Willow Wood", "泉中水": "Spring Water", "屋上土": "Rooftop Earth",
    "霹靂火": "Thunder Fire", "松柏木": "Pine-Cypress Wood",
    "沙中金": "Sand Gold", "山下火": "Mountain-Foot Fire", "平地木": "Flatland Wood",
    "壁上土": "Wall Earth", "金箔金": "Gold-Leaf Metal", "覆燈火": "Lamp Fire",
    "大驛土": "Post-Horse Earth", "桑柘木": "Mulberry Wood",
    "大溪水": "Great Stream Water", "沙中土": "Sand Earth",
    "天上火": "Heavenly Fire", "大海水": "Great Sea Water",
    # 24 solar terms (節氣/中氣) as the engine emits them in notes.
    "立春": "Lichun", "雨水": "Yushui", "驚蟄": "Jingzhe", "春分": "Chunfen",
    "淸明": "Qingming", "清明": "Qingming", "穀雨": "Guyu", "立夏": "Lixia",
    "小滿": "Xiaoman", "芒種": "Mangzhong", "夏至": "Xiazhi", "小暑": "Xiaoshu",
    "大暑": "Dashu", "立秋": "Liqiu", "處暑": "Chushu", "白露": "Bailu",
    "秋分": "Qiufen", "寒露": "Hanlu", "霜降": "Shuangjiang", "立冬": "Lidong",
    "小雪": "Xiaoxue", "大雪": "Daxue", "冬至": "Dongzhi", "小寒": "Xiaohan",
    "大寒": "Dahan",
    # Star / branch-relation Hanja (stars.py, skeleton, sewoon notes)
    "三刑": "three-punishment", "六沖": "Six Clash", "六破": "Six Break",
    "自刑": "self-punishment", "攀鞍": "Saddle Star", "白虎": "White Tiger",
    "羊刃": "Blade Star", "紅艶": "Red Flame", "紅艷": "Red Flame",
    "滴天髓": "Jeokcheon-su", "淵海子平": "Yeonhae-japyeong", "窮通寶鑑": "Gungtong-bogam",
    "命理正宗": "Myeongri-jeongjong", "子平眞詮": "Japyeong-jinjeon",
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


# A parenthetical written only in CJK — "(偏官)", "(大運)", "(丙午)". When a report
# is glossed these are the author's own Hanja notation for the English just
# written, so they are held aside rather than translated into a duplicate of it.
_PURE_CJK_PAREN_RE = re.compile(r"\(([^A-Za-z()]*)\)")


def _preceding_text(parts: List[str]) -> str:
    """The last non-empty piece already emitted, for duplicate detection."""
    for prev in reversed(parts):
        stripped = prev.strip()
        if stripped:
            return stripped
    return ""


def _ends_with(parts: List[str], phrase: str) -> bool:
    """Does the text already emitted end with ``phrase``?"""
    preceding = _preceding_text(parts).split()
    words = phrase.split()
    return bool(words) and len(words) <= len(preceding) and preceding[-len(words):] == words


def _protect_parenthetical_english(text: str, gloss: bool = False) -> tuple[str, list[str]]:
    """Replace parentheticals with placeholders so translation skips them.

    Pure-ASCII parentheticals are already translated English ("(Direct Officer)",
    "(Annual Luck)"). A parenthetical that also contains CJK (e.g. "(the heart of
    궁합)") keeps going through the normal path so the CJK inside it is
    translated.

    When ``gloss`` is set, a parenthetical that is *only* CJK is held aside too:
    it is the author's Hanja notation for the English just written ("Direct
    Officer (正官)"), and translating it as a run would gloss it a second time.
    ``translate_inline`` decides at restore time whether it repeats the English
    (keep the Hanja) or is itself a gloss to translate.
    """
    placeholders: list[str] = []

    def protect(match: "re.Match") -> str:
        placeholders.append(match.group(0))
        return f"\x00{len(placeholders) - 1}\x00"

    def replace(m: "re.Match") -> str:
        inner = m.group(0)
        # Skip if the parenthetical contains any CJK character.
        if _CJK_RE.search(inner):
            return inner
        return protect(m)

    if gloss:
        text = _PURE_CJK_PAREN_RE.sub(
            lambda m: protect(m) if _CJK_RE.search(m.group(1)) else m.group(0), text)
    # Match parentheses that contain at least one ASCII letter (treat as already
    # translated English). This catches "(Direct Officer)", "(Annual Luck)", etc.
    protected = re.sub(r"\([A-Za-z][^\)]*\)", replace, text)
    return protected, placeholders


_HANGUL_SEG_RE = re.compile(r"[가-힣]+")

# Korean grammatical particles, longest first. Consumed as a suffix after a
# matched multi-character term so they are never tokenized as stems/branches
# (P5-hangul-tokens: 천을귀인을 -> "Heavenly Noble", not "... Eul (Yin Wood)").
_PARTICLES = ("에서", "으로", "은", "는", "이", "가", "을", "를", "의",
              "와", "과", "도", "로", "에")


def _is_hangul_syllable(key: str) -> bool:
    return len(key) == 1 and "가" <= key <= "힣"


def _tokenize(
    run: str, banned: frozenset = frozenset()
) -> tuple[List[str], List[str], set]:
    """Longest-match tokenize ``run``; consecutive unmapped chars form ONE token.

    ``banned`` lists positions where single-syllable Hangul keys must not match.
    Returns (tokens, unmapped_tokens, positions of unmapped characters).
    """
    tokens: List[str] = []
    unmapped_tokens: List[str] = []
    unmapped_pos: set = set()
    pending = ""

    def flush() -> None:
        nonlocal pending
        if pending:
            tokens.append(pending)
            unmapped_tokens.append(pending)
            pending = ""

    i, n = 0, len(run)
    while i < n:
        for k, v in _TRANSLATION_TERMS:
            if run.startswith(k, i) and not (i in banned and _is_hangul_syllable(k)):
                flush()
                tokens.append(v)
                i += len(k)
                # Consume one trailing grammatical particle after a multi-
                # character Korean term so 을/은/는 never tokenize as a stem or
                # branch (Heavenly Noble 을 -> not "Eul"; 혼잡은 -> not "Yin").
                if len(k) > 1 and "가" <= run[i - 1] <= "힣":
                    for p in _PARTICLES:
                        if run.startswith(p, i):
                            i += len(p)
                            break
                break
        else:
            pending += run[i]
            unmapped_pos.add(i)
            i += 1
    flush()
    return tokens, unmapped_tokens, unmapped_pos


def _translate_cjk_run(
    run: str,
    keep_unmapped: bool = False,
    unmapped: Optional[set] = None,
    gloss: bool = False,
) -> str:
    """Translate one contiguous CJK run using longest-match tokenization.

    Unmapped characters are always added to ``unmapped`` (if given); they are
    kept verbatim in the output when ``keep_unmapped`` is true, else dropped.
    Consecutive unmapped characters are emitted as ONE token (a word, not
    spaced syllables). Single-syllable Hangul keys (stem/branch/12-stage names
    such as 사, 인, 해) are only trusted when the whole Hangul word maps: if a
    Hangul word contains any unmapped character they are NOT applied inside it,
    so an unknown word like 사고방식 stays whole instead of "Death 고방식".
    """
    tokens, unmapped_tokens, bad_pos = _tokenize(run)
    if bad_pos:
        # Ban single-syllable Hangul matches inside every Hangul word that
        # contains an unmapped character, then re-tokenize.
        banned = {
            i
            for m in _HANGUL_SEG_RE.finditer(run)
            if any(i in bad_pos for i in range(m.start(), m.end()))
            for i in range(m.start(), m.end())
        }
        if banned:
            tokens, unmapped_tokens, _ = _tokenize(run, frozenset(banned))
    if unmapped is not None:
        for w in unmapped_tokens:
            unmapped.update(w)
    if not keep_unmapped:
        bad = set(unmapped_tokens)
        tokens = [t for t in tokens if t not in bad]
    # Join translated tokens with a single space so adjacent Hanja pairs like
    # 丙午 do not collapse into "BingO".
    translated = " ".join(tokens)
    if gloss and translated and not unmapped_tokens:
        # `gloss` is the owner's convention for *client PDFs*: English with the
        # Hanja the report is about beside it ("Direct Officer (正官)", "Gye Mi
        # (癸未)"). One gloss per run, so a two-character pillar reads as
        # "Gye Mi (癸未)" rather than "Gye (癸) Mi (未)". Off by default, and
        # deliberately off for the audio script, where a narrator would read the
        # parentheses out loud.
        return f"{translated} ({run})"
    return translated


def translate_inline(
    text: str,
    *,
    keep_unmapped: bool = True,
    unmapped: Optional[set] = None,
    gloss: bool = False,
) -> str:
    """Replace Korean/Hanja terms with English.

    Unmapped CJK characters are never silently lost: with ``keep_unmapped``
    (default) they stay in the output (the HTML path renders them with a CJK
    font); otherwise they are dropped (for fonts that cannot draw CJK). Either
    way they are added to ``unmapped`` when a set is supplied.

    Improvements over the old global `.replace` loop:
      - Longest-match tokenization within CJK runs prevents adjacent Hanja pairs
        (e.g. 丙午, 辛未) from collapsing into "BingO" / "SinMetal".
      - A space is inserted between translated tokens.
      - Text already inside English parentheses is protected from re-translation,
        and exact duplicates like "Direct Officer (Direct Officer)" are collapsed.
    """
    # A Hangul term immediately glossed in English ("해 (harm)", "**천간충**
    # (stem clash)") becomes just the English gloss in the English-primary
    # PDF — translating the Hangul too produced doubles, and single syllables
    # could mis-translate (해 "harm" read as the branch 亥 "Hae (Pig)").
    for _rx, _repl in _PRE_RULES:
        text = _rx.sub(_repl, text)
    text = re.sub(
        r"(\*\*)?([가-힯]+)(\*\*)? \(([A-Za-z][^()]*)\)",
        lambda m: f"{m.group(1) or ''}{m.group(4)}{m.group(3) or ''}",
        text,
    )
    for _rx, _repl in _PHRASE_RULES:
        text = _rx.sub(_repl, text)
    protected, placeholders = _protect_parenthetical_english(text, gloss)

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
                    parts.append(_translate_cjk_run(sub, keep_unmapped, unmapped, gloss))
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
                parts.append(_translate_cjk_run(sub, keep_unmapped, unmapped, gloss))
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
        if gloss and _CJK_RE.search(placeholder):
            # A parenthetical the author wrote only in Hanja/Korean. Translate it
            # *without* glossing, then decide:
            #   "Seven Killings (偏官)" -> the Hanja repeats the English before it,
            #       so keep the Hanja: it is the notation the report is about, and
            #       deleting it here is what stripped the Hanja from every
            #       delivered report even though the source carried it;
            #   "庚 (본)" -> "본" is a gloss of the stem, not the term, so it is
            #       translated as before and reads "Gyeong (庚) (main)".
            # Recurse through the public entry point, not the run translator:
            # a parenthetical can mix CJK with digits and punctuation
            # ("(半合, 三合)", "(0.0, 甲)"), and the run translator would
            # report those spaces and commas as unmapped CJK.
            inner_en = translate_inline(
                inner, keep_unmapped=keep_unmapped, unmapped=unmapped, gloss=False).strip()
            if inner_en and _ends_with(out_parts, inner_en):
                out_parts.append(placeholder)
            elif inner_en:
                out_parts.append(f"({inner_en})")
            continue
        # Otherwise: if the immediately preceding non-empty text already ends
        # with the same English phrase (e.g. "正官 (Direct Officer)"), drop the
        # parenthetical to avoid "Direct Officer (Direct Officer)" duplication.
        if _ends_with(out_parts, inner):
            continue
        out_parts.append(placeholder)

    out = "".join(out_parts)
    # Final safety net: CJK the maps missed is dropped only when the caller
    # asked for it (keep_unmapped=False); either way it was reported above.
    if not keep_unmapped:
        out = _CJK_RE.sub(" ", out)
    # ...and any parenthetical it left empty ("Half Harmony ()").
    out = re.sub(r"\(\s*\)", "", out)
    # Collapse a term followed by its own translation in parens, which the
    # placeholder dedup above cannot see when the parenthetical was Hanja
    # (e.g. "Direct Officer (正官)" -> "Direct Officer (Direct Officer)").
    out = re.sub(r"\b([A-Za-z][\w-]*(?: [\w-]+){0,3}) \((\1)\)", r"\1", out, flags=re.I)
    # Collapse runs of spaces from the substitution.
    out = re.sub(r"  +", " ", out)
    out = re.sub(r" \.", ".", out)
    out = re.sub(r" ,", ",", out)
    out = re.sub(r" \u2019s\b", "\u2019s", out)
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
    # 4. Drop bracketed [UNCERTAIN: ...] markers (and the bare [UNCERTAIN]
    #    form — V3, 2026-09-14 audit §9.7: the old regex required the colon,
    #    so bare tags in compat/patterns prose leaked into client PDFs; the
    #    emitters are now client-voiced, and this catches any residual) so
    #    they do not leak into client PDFs.
    out = re.sub(r"\s*\[UNCERTAIN:?[^\]]*\]", "", out, flags=re.IGNORECASE)
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


# The sentence the engine appends to every report it generates. It is a note to
# the *reviewer* ("Interpretive prose must be reviewed and finalized by a
# qualified reader before client delivery"), and it was printing on the last page
# of the client's own copy — telling a paying buyer that nobody had read their
# reading, next to copy the reviewer had in fact rewritten. The review console
# reads the engine markdown directly, so it still sees this; the client render
# does not. (External audit, 2026-10-16, P0 #1.)
_DRAFT_NOTE_RE = re.compile(
    r"[ \t]*\*?Engine-generated premium report draft\.[^\n]*\*?[ \t]*\n?",
    re.IGNORECASE,
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
    # 3. The trailing "engine-generated draft" note (see _DRAFT_NOTE_RE).
    out = _DRAFT_NOTE_RE.sub("", out)
    out = re.sub(r"  +", " ", out)
    out = re.sub(r"\n\n\n+", "\n\n", out)
    return out
