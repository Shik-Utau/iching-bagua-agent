"""卦象关系：错卦、综卦、同上下卦。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"

# 八卦名 -> 三爻数组（从下到上，阳=1 阴=0）
# 先天序：乾1兑2离3震4巽5坎6艮7坤8
BAGUA_YAO: dict[str, tuple[int, int, int]] = {
    "乾": (1, 1, 1),
    "兑": (1, 1, 0),
    "离": (1, 0, 1),
    "震": (1, 0, 0),
    "巽": (0, 1, 1),
    "坎": (0, 1, 0),
    "艮": (0, 0, 1),
    "坤": (0, 0, 0),
}


def _load_hexagram_index():
    """加载卦序 -> (上卦, 下卦, 卦名) 及 六爻 -> 卦序 的索引。"""
    import json

    order_to_info: dict[int, tuple[str, str, str]] = {}
    yao_to_order: dict[tuple[int, ...], int] = {}

    for p in sorted(HEXAGRAMS_DIR.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        meta = data.get("元信息", {})
        卦序 = meta.get("卦序")
        上下卦 = meta.get("上下卦", {})
        卦名 = meta.get("卦名", "")
        上卦 = 上下卦.get("上卦")
        下卦 = 上下卦.get("下卦")
        if 卦序 is None or not 上卦 or not 下卦:
            continue

        上三爻 = BAGUA_YAO.get(上卦, (0, 0, 0))
        下三爻 = BAGUA_YAO.get(下卦, (0, 0, 0))
        六爻 = 下三爻 + 上三爻  # 初二三 + 四五六

        order_to_info[卦序] = (上卦, 下卦, 卦名)
        yao_to_order[六爻] = 卦序

    return order_to_info, yao_to_order


# 懒加载
_order_to_info: dict[int, tuple[str, str, str]] | None = None
_yao_to_order: dict[tuple[int, ...], int] | None = None


def _ensure_index():
    global _order_to_info, _yao_to_order
    if _order_to_info is None:
        _order_to_info, _yao_to_order = _load_hexagram_index()


def order_to_yao_array(卦序: int) -> tuple[int, int, int, int, int, int] | None:
    """卦序 -> 六爻数组（从下到上，阳=1 阴=0）。"""
    _ensure_index()
    info = _order_to_info.get(卦序)
    if not info:
        return None
    上卦, 下卦, _ = info
    上三爻 = BAGUA_YAO.get(上卦, (0, 0, 0))
    下三爻 = BAGUA_YAO.get(下卦, (0, 0, 0))
    return 下三爻 + 上三爻


def yao_array_to_order(六爻: tuple[int, ...]) -> int | None:
    """六爻数组 -> 卦序。若不存在则返回 None。"""
    _ensure_index()
    if len(六爻) != 6:
        return None
    return _yao_to_order.get(tuple(六爻))


def order_to_symbol(卦序: int) -> str:
    """卦序 -> Unicode 卦画符号。"""
    if not 1 <= 卦序 <= 64:
        return ""
    return chr(0x4DC0 + 卦序 - 1)


def get_cuogua(卦序: int) -> int | None:
    """错卦：六爻阴阳全反。乾(111111) -> 坤(000000)。"""
    六爻 = order_to_yao_array(卦序)
    if not 六爻:
        return None
    反 = tuple(1 - y for y in 六爻)
    return yao_array_to_order(反)


def get_zonggua(卦序: int) -> int | None:
    """综卦：上下颠倒。屯(坎上震下) -> 蒙(艮上坎下)。"""
    六爻 = order_to_yao_array(卦序)
    if not 六爻:
        return None
    颠倒 = tuple(reversed(六爻))
    return yao_array_to_order(颠倒)


def get_same_trigram_hexagrams(
    卦序: int,
    *,
    same_上卦: bool = True,
    same_下卦: bool = True,
    exclude_self: bool = True,
) -> list[int]:
    """与指定卦共享上卦和/或下卦的卦序列表。

    Args:
        卦序: 参考卦序
        same_上卦: 筛选上卦相同的卦
        same_下卦: 筛选下卦相同的卦
        exclude_self: 是否排除自身

    Returns:
        满足条件的卦序列表。若 same_上卦 与 same_下卦 均为 True，则筛选同上卦或同下卦（满足其一即可）。
    """
    _ensure_index()
    info = _order_to_info.get(卦序)
    if not info:
        return []
    上卦, 下卦, _ = info

    result: list[int] = []
    for o, (u, d, _) in _order_to_info.items():
        if exclude_self and o == 卦序:
            continue
        match = False
        if same_上卦 and u == 上卦:
            match = True
        if same_下卦 and d == 下卦:
            match = True
        if match:
            result.append(o)
    return sorted(result)


def get_hexagrams_with_trigram(卦名: str, *, 上卦: bool = True, 下卦: bool = True) -> list[int]:
    """含指定八卦的卦序列表（在上卦或下卦中出现即可）。

    Args:
        卦名: 八卦名（乾、坤、震、巽、坎、离、艮、兑）
        上卦: 是否匹配上卦
        下卦: 是否匹配下卦

    Returns:
        卦序列表
    """
    _ensure_index()
    result: list[int] = []
    for o, (u, d, _) in _order_to_info.items():
        if (上卦 and u == 卦名) or (下卦 and d == 卦名):
            result.append(o)
    return sorted(set(result))


def get_adjacent_orders(卦序: int) -> tuple[int | None, int | None]:
    """卦序相邻：前一卦、后一卦。"""
    if 卦序 <= 1:
        prev = None
    else:
        prev = 卦序 - 1
    if 卦序 >= 64:
        next_ = None
    else:
        next_ = 卦序 + 1
    return (prev, next_)
