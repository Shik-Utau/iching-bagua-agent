"""交互式录入六十四卦卦爻辞。"""

import json
from pathlib import Path

from iching_bagua.hexagrams import HEXAGRAMS_DIR

BAGUA = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}
BAGUA_NAMES = list(BAGUA.keys())


def _prompt(prompt: str, default: str = "", required: bool = True) -> str:
    while True:
        s = input(f"  {prompt}: ").strip()
        if s:
            return s
        if default or not required:
            return default
        print("    （必填，请重新输入）")


def _prompt_list(prompt: str) -> list[str]:
    s = input(f"  {prompt}（逗号分隔，空则跳过）: ").strip()
    if not s:
        return []
    return [x.strip() for x in s.split("，") if x.strip()] or [x.strip() for x in s.split(",") if x.strip()]


def _prompt_bool(prompt: str, default: bool = True) -> bool:
    s = input(f"  {prompt} (y/n，默认 y): ").strip().lower()
    if not s:
        return default
    return s in ("y", "yes", "是")


def _卦画(卦序: int) -> str:
    return chr(0x4DC0 + 卦序 - 1)


def add_hexagram() -> None:
    """交互式录入一卦。"""
    print("=== 六十四卦录入 ===\n")

    while True:
        try:
            卦序 = int(_prompt("卦序 (1-64)", required=True))
            if 1 <= 卦序 <= 64:
                break
        except ValueError:
            pass
        print("    请输入 1-64 的整数")

    existing = list(HEXAGRAMS_DIR.glob(f"{卦序:02d}_*.json"))
    if existing:
        overwrite = _prompt_bool(f"已存在 {existing[0].name}，是否覆盖？", False)
        if not overwrite:
            print("已取消。")
            return

    print("\n--- 元信息 ---")
    卦名 = _prompt("卦名", required=True)
    卦画 = _卦画(卦序)

    print("  上卦可选:", " ".join(BAGUA_NAMES))
    上卦 = _prompt("上卦", required=True)
    while 上卦 not in BAGUA:
        上卦 = _prompt("上卦（请从八卦中选）", required=True)

    print("  下卦可选:", " ".join(BAGUA_NAMES))
    下卦 = _prompt("下卦", required=True)
    while 下卦 not in BAGUA:
        下卦 = _prompt("下卦（请从八卦中选）", required=True)

    别名 = _prompt_list("别名")

    print("\n--- 卦辞 ---")
    卦辞原文 = _prompt("卦辞原文", required=True)
    卦辞白话 = _prompt("卦辞白话", required=True)
    彖传 = _prompt("彖传", required=False)
    大象传 = _prompt("大象传", required=False)
    关键词 = _prompt_list("关键词")
    吉凶标签 = _prompt("吉凶标签", required=False)

    print("\n--- 爻辞（共 6 爻，乾卦可加用九、坤卦可加用六）---")
    爻辞列表 = []
    for i in range(6):
        print(f"\n  第 {i+1} 爻:")
        爻位 = _prompt("  爻位（如初九、六二）", required=True)
        阴阳 = "阳" if "九" in 爻位 else "阴"
        当位 = _prompt_bool("当位？", default=(i % 2 == 0 and "九" in 爻位) or (i % 2 == 1 and "六" in 爻位))
        原文 = _prompt("  原文", required=True)
        白话 = _prompt("  白话", required=True)
        小象传 = _prompt("  小象传", required=False)
        吉凶 = _prompt("  吉凶标签", required=False)
        取象 = _prompt("  爻象推导-取象", required=False)
        逻辑 = _prompt("  爻象推导-逻辑", required=False)
        关联映射 = _prompt_list("  关联映射")
        应爻 = _prompt("  应爻", required=False)
        承乘 = _prompt_list("  承乘")

        爻象推导 = None
        if 取象 or 逻辑:
            爻象推导 = {
                "本爻象": _prompt("  爻象推导-本爻象", required=False) or "",
                "取象": 取象 or "",
                "逻辑": 逻辑 or "",
            }

        爻辞列表.append({
            "爻位": 爻位,
            "爻位序": i + 1,
            "阴阳": 阴阳,
            "当位": 当位,
            "原文": 原文,
            "白话": 白话,
            "小象传": 小象传 or None,
            "吉凶标签": 吉凶 or None,
            "爻象推导": 爻象推导,
            "关联映射": 关联映射,
            "应爻": 应爻 or None,
            "承乘": 承乘,
        })

    # 乾卦可加用九，坤卦可加用六
    if 卦名 == "乾":
        if _prompt_bool("是否添加用九？", default=False):
            原文 = _prompt("  用九-原文", required=True)
            白话 = _prompt("  用九-白话", required=True)
            小象传 = _prompt("  用九-小象传", required=False)
            吉凶 = _prompt("  用九-吉凶标签", required=False)
            取象 = _prompt("  用九-爻象推导-取象", required=False)
            逻辑 = _prompt("  用九-爻象推导-逻辑", required=False)
            爻象推导 = None
            if 取象 or 逻辑:
                爻象推导 = {
                    "本爻象": _prompt("  用九-爻象推导-本爻象", required=False) or "",
                    "取象": 取象 or "",
                    "逻辑": 逻辑 or "",
                }
            爻辞列表.append({
                "爻位": "用九",
                "爻位序": 0,
                "阴阳": "阳",
                "当位": None,
                "原文": 原文,
                "白话": 白话,
                "小象传": 小象传 or None,
                "吉凶标签": 吉凶 or None,
                "爻象推导": 爻象推导,
                "关联映射": _prompt_list("  用九-关联映射"),
                "应爻": None,
                "承乘": [],
            })
    elif 卦名 == "坤":
        if _prompt_bool("是否添加用六？", default=False):
            原文 = _prompt("  用六-原文", required=True)
            白话 = _prompt("  用六-白话", required=True)
            小象传 = _prompt("  用六-小象传", required=False)
            吉凶 = _prompt("  用六-吉凶标签", required=False)
            取象 = _prompt("  用六-爻象推导-取象", required=False)
            逻辑 = _prompt("  用六-爻象推导-逻辑", required=False)
            爻象推导 = None
            if 取象 or 逻辑:
                爻象推导 = {
                    "本爻象": _prompt("  用六-爻象推导-本爻象", required=False) or "",
                    "取象": 取象 or "",
                    "逻辑": 逻辑 or "",
                }
            爻辞列表.append({
                "爻位": "用六",
                "爻位序": 0,
                "阴阳": "阴",
                "当位": None,
                "原文": 原文,
                "白话": 白话,
                "小象传": 小象传 or None,
                "吉凶标签": 吉凶 or None,
                "爻象推导": 爻象推导,
                "关联映射": _prompt_list("  用六-关联映射"),
                "应爻": None,
                "承乘": [],
            })

    data = {
        "元信息": {
            "卦名": 卦名,
            "卦序": 卦序,
            "卦画": 卦画,
            "上下卦": {
                "上卦": 上卦,
                "上卦数": BAGUA[上卦],
                "下卦": 下卦,
                "下卦数": BAGUA[下卦],
            },
            "别名": 别名,
        },
        "卦辞": {
            "原文": 卦辞原文,
            "白话": 卦辞白话,
            "彖传": 彖传 or None,
            "大象传": 大象传 or None,
            "关键词": 关键词,
            "吉凶标签": 吉凶标签 or None,
        },
        "爻辞": 爻辞列表,
    }

    HEXAGRAMS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = HEXAGRAMS_DIR / f"{卦序:02d}_{卦名}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n已保存: {out_path}")
