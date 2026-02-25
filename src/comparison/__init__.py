"""卦象对比：错卦、综卦、同上下卦、相似卦发现、两卦对比、系列对比。"""

from .relations import (
    get_adjacent_orders,
    get_cuogua,
    get_hexagrams_with_trigram,
    get_same_trigram_hexagrams,
    get_zonggua,
    order_to_symbol,
    order_to_yao_array,
    yao_array_to_order,
)
from .compare import build_comparison_md, compare_two_hexagrams
from .similar import find_similar_hexagrams, get_keyword_similar
from .series import (
    PRESET_SERIES,
    build_series_comparison_md,
    compare_series,
    get_series_orders,
)

# API 别名（供 Agent 等调用）
find_similar = find_similar_hexagrams
compare_two = compare_two_hexagrams

__all__ = [
    "PRESET_SERIES",
    "build_comparison_md",
    "build_series_comparison_md",
    "compare_series",
    "compare_two",
    "compare_two_hexagrams",
    "find_similar",
    "find_similar_hexagrams",
    "get_series_orders",
    "get_adjacent_orders",
    "get_cuogua",
    "get_hexagrams_with_trigram",
    "get_keyword_similar",
    "get_same_trigram_hexagrams",
    "get_zonggua",
    "order_to_symbol",
    "order_to_yao_array",
    "yao_array_to_order",
]
