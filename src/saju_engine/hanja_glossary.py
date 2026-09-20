"""Korean → Hanja glossary for first-use annotation in engine prose.

CLAUDE.md requires technical Saju terms to appear with both Korean (한글) and
Hanja (한자) on first use. This map is shared by report builders; each builder
tracks which terms it has already injected.
"""
import re
from typing import Dict

HANJA_GLOSSARY: Dict[str, str] = {
    "대운": "大運",
    "세운": "歲運",
    "월운": "月運",
    "일운": "日運",
    "용신": "用神",
    "희신": "喜神",
    "기신": "忌神",
    "한신": "閒神",
    "십신": "十神",
    "도화": "桃花",
    "역마": "驛馬",
    "화개": "華蓋",
    "천을귀인": "天乙貴人",
    "문창귀인": "文昌貴人",
    "홍염": "紅艷",
    "양인": "羊刃",
    "공망": "空亡",
    "격국": "格局",
    "일간": "日干",
    "일주": "日柱",
    "월지": "月支",
    "천간": "天干",
    "지지": "地支",
    "오행": "五行",
    "음양": "陰陽",
    "합": "合",
    "충": "沖",
    "형": "刑",
    "파": "破",
    "해": "害",
    "반합": "半合",
    "삼합": "三合",
    "육합": "六合",
    "육충": "六沖",
    "자형": "自刑",
    "삼형": "三刑",
    "육파": "六破",
    "육해": "六害",
    "장생": "長生",
    "목욕": "沐浴",
    "관대": "冠帶",
    "건록": "建祿",
    "제왕": "帝旺",
    "쇠": "衰",
    "병": "病",
    "사": "死",
    "묘": "墓",
    "절": "絶",
    "태": "胎",
    "양": "養",
    # Additional stars documented in knowledge/07-special-formations.md
    "신살": "神殺",
    "겁살": "劫煞",
    "재살": "災煞",
    "천살": "天煞",
    "지살": "地煞",
    "연살": "年煞",
    "월살": "月煞",
    "망신": "亡神",
    "망신살": "亡神殺",
    "장성": "將星",
    "반안": "攀鞍",
    "육해": "六害",
    "원진": "怨嗔",
    "원진살": "怨嗔煞",
    "귀문관": "鬼門關",
    "귀문관살": "鬼門關煞",
    "백호": "白虎",
    "백호대살": "白虎大煞",
    "괴강": "魁罡",
    "괴강살": "魁罡煞",
    "천덕귀인": "天德貴人",
    "월덕귀인": "月德貴人",
    "천덕": "天德",
    "월덕": "月德",
    "일주": "日柱",
    "월지": "月支",
    "본기": "本氣",
    "중기": "中氣",
    "여기": "餘氣",
}


def inject_hanja(text: str, already_used: set, glossary: Dict[str, str] = HANJA_GLOSSARY) -> str:
    """Annotate the first occurrence of each glossary term in `text`.

    Terms are processed longest-first to avoid partial replacements (e.g.
    "천을귀인" before "천간"). Already-used terms are skipped. The set is
    updated in place.
    """
    # Work longest-first to avoid replacing a shorter term inside a longer one.
    for term in sorted(glossary, key=len, reverse=True):
        if term in already_used:
            continue
        hanja = glossary[term]
        # Replace the first occurrence only, preserving surrounding characters.
        idx = text.find(term)
        if idx == -1:
            continue
        # Avoid re-annotating a term that already has Hanja nearby.
        #
        # Bug found 2026-09-20 (external report review): the original check
        # here only looked IMMEDIATELY after `term`'s own end for an opening
        # paren. That misses every case where `term` is a prefix of a longer
        # compound word that already carries its Hanja a few Hangul
        # characters later — e.g. "역마" is a prefix of "역마살"; text already
        # containing "역마살 (驛馬殺, Post Horse Star)" has "살", not "(",
        # immediately after "역마", so the old check inserted a second,
        # word-splitting annotation mid-compound: "역마 (驛馬)살 (驛馬殺, ...)".
        # This happened even for compounds that are NOT themselves a second
        # glossary key (역마살 isn't a HANJA_GLOSSARY key; 천덕귀인 is — both
        # forms of the bug are real and are both fixed by this one check).
        #
        # Fix: after `term`, allow up to 6 more Hangul syllables (a generous
        # bound — covers suffixes like 살/귀인/살성 etc.) before requiring the
        # "(" that marks an existing annotation.
        after = idx + len(term)
        lookahead = text[after:after + 8]
        if re.match(r"^[가-힣]{0,6}\s*\(", lookahead):
            continue
        # Bug found 2026-09-20 (own find, while implementing R12's annual-
        # activation note): the checks above only ever looked AFTER `term`.
        # A single-character glossary entry like "합" (合) can also sit
        # embedded on the LEFT side of an unlisted longer compound —
        # confirmed live: "병신합수" (a 천간합 label built at render time,
        # not itself a glossary key) matched "합" mid-word and rendered as
        # the split "병신합 (合)수". Require a left word-boundary too: skip
        # when the character immediately before `term` is itself Hangul,
        # since that means `term` is only a fragment of a larger compound.
        if idx > 0 and re.match(r"[가-힣]", text[idx - 1]):
            continue
        annotated = f"{term} ({hanja})"
        text = text[:idx] + annotated + text[idx + len(term):]
        already_used.add(term)
    return text
