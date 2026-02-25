"""相似卦发现：整合结构相似与关键词相似。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"

from .relations import (
    get_adjacent_orders,
    get_cuogua,
    get_same_trigram_hexagrams,
    get_zonggua,
)


def _extend_keywords_with_bigrams(words: set[str]) -> set[str]:
    """将关键词扩展为包含所有二字子串，便于模糊匹配。如「刚健而动」-> 含「刚健」。"""
    out = set(words)
    for w in words:
        if len(w) >= 2:
            for i in range(len(w) - 1):
                out.add(w[i : i + 2])
    return out


def _load_keywords_index() -> dict[int, set[str]]:
    """加载卦序 -> 关键词集合（含二字子串扩展）。"""
    import json

    result: dict[int, set[str]] = {}
    for p in sorted(HEXAGRAMS_DIR.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        卦序 = data.get("元信息", {}).get("卦序")
        if 卦序 is None:
            continue
        kw = data.get("卦辞", {}).get("关键词", [])
        if isinstance(kw, list):
            raw = {str(x).strip() for x in kw if str(x).strip()}
            result[卦序] = _extend_keywords_with_bigrams(raw)
        else:
            result[卦序] = set()
    return result


_keywords_index: dict[int, set[str]] | None = None


def _ensure_keywords() -> None:
    global _keywords_index
    if _keywords_index is None:
        _keywords_index = _load_keywords_index()


def get_keyword_similar(
    卦序: int,
    *,
    top_k: int = 10,
    min_overlap: int = 1,
    exclude_self: bool = True,
) -> list[tuple[int, float]]:
    """按卦辞关键词交集相似度返回相似卦。

    Args:
        卦序: 参考卦序
        top_k: 返回前 k 个
        min_overlap: 最少交集词数
        exclude_self: 是否排除自身

    Returns:
        [(卦序, 相似度), ...]，相似度用 Jaccard 系数 |A∩B|/|A∪B|
    """
    _ensure_keywords()
    A = _keywords_index.get(卦序, set())
    if not A:
        return []

    scores: list[tuple[int, float]] = []
    for o, B in _keywords_index.items():
        if exclude_self and o == 卦序:
            continue
        overlap = len(A & B)
        if overlap < min_overlap:
            continue
        union = len(A | B)
        jaccard = overlap / union if union else 0.0
        scores.append((o, jaccard))

    scores.sort(key=lambda x: (-x[1], x[0]))
    return scores[:top_k]


def find_similar_hexagrams(
    卦序: int,
    *,
    include_keyword: bool = True,
    keyword_top_k: int = 10,
    same_trigram: bool = True,
) -> dict:
    """整合相似卦检索结果。

    Returns:
        {
            "错卦": 卦序 | None,
            "综卦": 卦序 | None,
            "卦序相邻": {"前": 卦序|None, "后": 卦序|None},
            "同上下卦": [卦序, ...],
            "关键词相似": [(卦序, 相似度), ...],
        }
    """
    prev, next_ = get_adjacent_orders(卦序)
    result = {
        "错卦": get_cuogua(卦序),
        "综卦": get_zonggua(卦序),
        "卦序相邻": {"前": prev, "后": next_},
        "同上下卦": get_same_trigram_hexagrams(卦序) if same_trigram else [],
        "关键词相似": [],
    }
    if include_keyword:
        result["关键词相似"] = get_keyword_similar(卦序, top_k=keyword_top_k)
    return result
