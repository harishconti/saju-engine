"""Tests for src/saju_html/__init__.py's translation maps.

N-16 (2026-09-26 audit): F821 undefined `List` (3 occurrences — harmless
under `from __future__ import annotations` but breaks `typing.get_type_hints`)
and F601 duplicate dict keys in the translation maps, some with conflicting
values that silently pick the later one.
"""
from __future__ import annotations

import inspect
import re
import typing

import saju_html


def _duplicate_keys_in_source(dict_source: str) -> set[str]:
    keys = re.findall(r'"((?:[^"\\]|\\.)*)"\s*:', dict_source)
    seen: set[str] = set()
    dupes: set[str] = set()
    for k in keys:
        if k in seen:
            dupes.add(k)
        seen.add(k)
    return dupes


def _dict_literal_source(varname: str) -> str:
    module_source = inspect.getsource(saju_html)
    start = module_source.index(f"\n{varname} = {{")
    end = module_source.index("\n}", start)
    return module_source[start:end]


def test_kor_repl_has_no_duplicate_keys():
    dupes = _duplicate_keys_in_source(_dict_literal_source("KOR_REPL"))
    assert dupes == set(), f"KOR_REPL has duplicate keys: {dupes}"


def test_hanja_map_has_no_duplicate_keys():
    dupes = _duplicate_keys_in_source(_dict_literal_source("HANJA_MAP"))
    assert dupes == set(), f"HANJA_MAP has duplicate keys: {dupes}"


def test_module_level_type_hints_resolve():
    """F821: `List` must be imported, not just used under deferred annotations."""
    typing.get_type_hints(saju_html._translate_cjk_run)
    typing.get_type_hints(saju_html.translate_inline)
