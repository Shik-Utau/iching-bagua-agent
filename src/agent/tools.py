"""Agent 工具：卦象对比的可调用接口，返回结构化数据。"""

from comparison import (
    find_similar_hexagrams,
    compare_two_hexagrams,
    compare_series,
    get_series_orders,
    order_to_symbol,
)


def _resolve_and_name(卦序_or_卦名):
    """解析卦序或卦名为 (卦序, 卦名)。"""
    from comparison.compare import _resolve_hexagram
    from iching_bagua.hexagrams import list_hexagrams
    o = _resolve_hexagram(卦序_or_卦名)
    if o is None:
        return None, None
    名 = next((n for ord_, n, _ in list_hexagrams() if ord_ == o), str(o))
    return o, 名


def tool_find_similar(卦序_or_卦名: str | int, *, include_keyword: bool = True) -> dict:
    """查找相似卦。供 Agent 调用。

    Args:
        卦序_or_卦名: 卦序(1-64) 或 卦名
        include_keyword: 是否包含关键词相似

    Returns:
        {
            "卦序": int,
            "卦名": str,
            "错卦": {"卦序": int, "卦名": str} | null,
            "综卦": {"卦序": int, "卦名": str} | null,
            "卦序相邻": {"前": {...}|null, "后": {...}|null},
            "同上下卦": [{"卦序": int, "卦名": str}, ...],
            "关键词相似": [{"卦序": int, "卦名": str, "相似度": float}, ...],
        }
    """
    from iching_bagua.hexagrams import list_hexagrams

    o, 名 = _resolve_and_name(卦序_or_卦名)
    if o is None:
        return {"error": f"未找到卦「{卦序_or_卦名}」"}

    sim = find_similar_hexagrams(o, include_keyword=include_keyword)
    order_to_name = {ord_: n for ord_, n, _ in list_hexagrams()}

    def _info(卦序: int | None) -> dict | None:
        if 卦序 is None:
            return None
        return {"卦序": 卦序, "卦名": order_to_name.get(卦序, str(卦序)), "卦画": order_to_symbol(卦序)}

    result = {
        "卦序": o,
        "卦名": 名,
        "卦画": order_to_symbol(o),
        "错卦": _info(sim.get("错卦")),
        "综卦": _info(sim.get("综卦")),
        "卦序相邻": {
            "前": _info(sim.get("卦序相邻", {}).get("前")),
            "后": _info(sim.get("卦序相邻", {}).get("后")),
        },
        "同上下卦": [_info(x) for x in sim.get("同上下卦", []) if x],
        "关键词相似": [
            {"卦序": x[0], "卦名": order_to_name.get(x[0], str(x[0])), "相似度": round(x[1], 3)}
            for x in sim.get("关键词相似", [])
        ],
    }
    return result


def tool_compare_two(卦A: str | int, 卦B: str | int) -> dict:
    """两卦对比。供 Agent 调用。

    Args:
        卦A, 卦B: 卦序或卦名

    Returns:
        {
            "卦A": {"卦序": int, "卦名": str, "上下卦": str, ...},
            "卦B": {...},
            "错卦关系": bool,
            "综卦关系": bool,
            "卦辞": {"卦A": {...}, "卦B": {...}},
            "爻辞": [{"爻位序": int, "卦A": {...}, "卦B": {...}}, ...],
        }
    """
    oA, _ = _resolve_and_name(卦A)
    oB, _ = _resolve_and_name(卦B)
    if oA is None:
        return {"error": f"未找到卦「{卦A}」"}
    if oB is None:
        return {"error": f"未找到卦「{卦B}」"}

    data = compare_two_hexagrams(oA, oB)
    if not data:
        return {"error": "对比数据加载失败"}
    return data


def tool_compare_series(预设或列表: str | list) -> dict:
    """卦系列对比。供 Agent 调用。

    Args:
        预设或列表: 预设名称（上经前六卦、含坎等）或 卦名/卦序列表

    Returns:
        {
            "卦列表": [{"卦序": int, "卦名": str}, ...],
            "卦辞": [...],
            "爻位对比": [...],
        }
    """
    orders = get_series_orders(预设或列表)
    if not orders:
        return {"error": f"未解析到有效卦系列「{预设或列表}」"}
    data = compare_series(orders)
    if not data:
        return {"error": "系列对比数据加载失败"}
    return data


def get_tool_definitions() -> list[dict]:
    """返回 OpenAI 风格的工具定义，用于 function calling。

    Returns:
        [
            {
                "type": "function",
                "function": {
                    "name": "find_similar_hexagrams",
                    "description": "...",
                    "parameters": {...},
                },
            },
            ...
        ]
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "find_similar_hexagrams",
                "description": "查找与指定卦相似的卦，包括错卦、综卦、同上下卦、卦序相邻、关键词相似。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hexagram": {
                            "type": ["string", "integer"],
                            "description": "卦序(1-64) 或 卦名（如乾、坤、屯）",
                        },
                        "include_keyword": {
                            "type": "boolean",
                            "description": "是否包含关键词相似",
                            "default": True,
                        },
                    },
                    "required": ["hexagram"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_two_hexagrams",
                "description": "对比两个卦的结构、卦辞、爻辞。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hexagram_a": {
                            "type": ["string", "integer"],
                            "description": "卦 A：卦序或卦名",
                        },
                        "hexagram_b": {
                            "type": ["string", "integer"],
                            "description": "卦 B：卦序或卦名",
                        },
                    },
                    "required": ["hexagram_a", "hexagram_b"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "compare_series",
                "description": "卦系列对比。支持预设（上经前六卦、含坎等）或卦名/卦序列表。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "series": {
                            "type": ["string", "array"],
                            "description": "预设名称或卦名/卦序列表（如「上经前六卦」「含坎」或 [\"泰\",\"否\",\"既济\",\"未济\"]）",
                        },
                    },
                    "required": ["series"],
                },
            },
        },
    ]
