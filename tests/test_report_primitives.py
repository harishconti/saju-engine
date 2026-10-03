from saju_engine import report_primitives as RP


def test_tengod_tables_cover_all_ten():
    assert set(RP.TENGOD_CLASS) == set(RP.TENGOD_SHORT_EN) == {
        "비견", "겁재", "식신", "상관", "편재", "정재", "편관", "정관", "편인", "정인"}
    assert RP.TENGOD_CLASS["상관"] == "Output"
    assert RP.TENGOD_SHORT_EN["상관"] == "Hurting Officer"
    assert set(RP.TENGOD_CLASS.values()) == set(RP.CLASS_ORDER) == set(RP.CLASS_KO)


def test_verdict_label_is_symmetric():
    assert RP.verdict_label("extreme") == "Very Strong"
    assert RP.verdict_label("extreme_weak") == "Very Weak"
    assert RP.verdict_label("strong") == "Strong"
    assert RP.verdict_label("weak") == "Weak"
    assert RP.verdict_label("balanced") == "Balanced"
    assert RP.verdict_label("") == "Balanced"


def test_favorability_rule():
    f = RP.favorability
    assert f("Metal", "Earth", "Water", "Metal", "Fire") == "favorable"   # 희신 hit
    assert f("Fire", "Earth", "Water", "Metal", "Fire") == "unfavorable"
    assert f("Water", "Fire", "Water", "Metal", "Fire") == "neutral"      # F-7 wash
    assert f("Earth", "Earth", "Water", "—", None) == "neutral"
    assert f("Water", "Earth", "Water", None, "—") == "favorable"        # sentinels ignored


def test_plain_and_bar():
    assert RP.plain("x") == "> **In plain words:** x"
    assert RP.bar(50, 10) == "█████░░░░░"
    assert RP.bar(43.4) == "█" * 9 + "░" * 11
