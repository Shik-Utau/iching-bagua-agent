"""六十四卦卦爻辞数据加载与索引。"""

from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"
BAGUA_MAPPINGS_PATH = PROJECT_ROOT / "data" / "bagua_mappings" / "bagua_mappings.json"

BAGUA_NAMES = {"乾", "坤", "震", "巽", "坎", "离", "艮", "兑"}
REQUIRED_YAO_FIELDS = {"爻位", "爻位序", "阴阳", "当位", "原文", "白话"}  # 当位可为 null（用九/用六）


def load(卦序: int | None = None, 卦名: str | None = None, path: Path | str | None = None) -> dict | None:
    """加载单卦数据。

    Args:
        卦序: 卦序 1-64，与 path 二选一
        卦名: 卦名，与 卦序 配合用于定位文件（若文件名含卦名）
        path: 直接指定 JSON 文件路径

    Returns:
        卦数据字典，未找到则返回 None
    """
    if path:
        p = Path(path)
    elif 卦序 is not None:
        # 匹配 01_乾.json 或 01_*.json
        pattern = f"{卦序:02d}_*.json" if 卦名 is None else f"{卦序:02d}_{卦名}.json"
        matches = list(HEXAGRAMS_DIR.glob(pattern))
        if not matches:
            return None
        p = matches[0]
    else:
        return None

    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_all(dir_path: Path | str | None = None) -> dict[int, dict]:
    """加载所有卦数据，按卦序索引。

    Args:
        dir_path: 卦数据目录，默认 data/hexagrams/

    Returns:
        {卦序: 卦数据} 字典
    """
    d = Path(dir_path) if dir_path else HEXAGRAMS_DIR
    if not d.exists():
        return {}

    result: dict[int, dict] = {}
    for p in sorted(d.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            order = data.get("元信息", {}).get("卦序")
            if order is not None:
                result[order] = data
        except Exception:
            continue
    return result


def list_hexagrams(dir_path: Path | str | None = None) -> list[tuple[int, str, Path]]:
    """列出所有卦文件。

    Returns:
        [(卦序, 卦名, 路径), ...]
    """
    d = Path(dir_path) if dir_path else HEXAGRAMS_DIR
    if not d.exists():
        return []

    out: list[tuple[int, str, Path]] = []
    for p in sorted(d.glob("*.json")):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("元信息", {})
            order = meta.get("卦序")
            name = meta.get("卦名", "")
            if order is not None:
                out.append((order, name, p))
        except Exception:
            continue
    return sorted(out, key=lambda x: x[0])


def _load_bagua_set() -> set[str]:
    try:
        with open(BAGUA_MAPPINGS_PATH, encoding="utf-8") as f:
            return set(json.load(f).keys())
    except Exception:
        return BAGUA_NAMES


def validate_hexagrams(dir_path: Path | str | None = None) -> list[str]:
    """校验卦爻辞数据。返回错误列表。"""
    errors: list[str] = []
    bagua = _load_bagua_set()
    d = Path(dir_path) if dir_path else HEXAGRAMS_DIR

    if not d.exists():
        return [f"目录不存在: {d}"]

    files = sorted(d.glob("*.json"))
    if not files:
        return ["未找到任何卦文件"]

    seen_orders: set[int] = set()

    for path in files:
        prefix = f"[{path.name}]"
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{prefix} JSON 解析失败: {e}")
            continue
        except Exception as e:
            errors.append(f"{prefix} 读取失败: {e}")
            continue

        if "元信息" not in data:
            errors.append(f"{prefix} 缺少 元信息")
        else:
            meta = data["元信息"]
            for field in ("卦名", "卦序", "卦画", "上下卦"):
                if field not in meta:
                    errors.append(f"{prefix} 元信息缺少: {field}")

            if "卦序" in meta:
                order = meta["卦序"]
                if not isinstance(order, int) or not (1 <= order <= 64):
                    errors.append(f"{prefix} 卦序应为 1-64 的整数，当前: {order}")
                elif order in seen_orders:
                    errors.append(f"{prefix} 卦序 {order} 重复")
                else:
                    seen_orders.add(order)

            if "上下卦" in meta:
                sq = meta["上下卦"]
                if isinstance(sq, dict):
                    for k in ("上卦", "下卦"):
                        if k in sq and sq[k] not in bagua:
                            errors.append(f"{prefix} 上下卦.{k} 不在八卦中: {sq[k]}")

        if "卦辞" not in data:
            errors.append(f"{prefix} 缺少 卦辞")
        else:
            for field in ("原文", "白话"):
                if field not in data["卦辞"]:
                    errors.append(f"{prefix} 卦辞缺少: {field}")

        if "爻辞" not in data:
            errors.append(f"{prefix} 缺少 爻辞")
        else:
            yaos = data["爻辞"]
            if not isinstance(yaos, list):
                errors.append(f"{prefix} 爻辞 应为数组")
            elif len(yaos) not in (6, 7):
                errors.append(f"{prefix} 爻辞 应有 6 条或 7 条（含用九/用六），当前 {len(yaos)} 条")
            else:
                for i, yao in enumerate(yaos):
                    if isinstance(yao, dict):
                        missing = REQUIRED_YAO_FIELDS - set(yao.keys())
                        if missing:
                            errors.append(f"{prefix} 爻辞[{i}] 缺少: {missing}")
                        # 用九/用六 爻位序可为 0，当位可为 null
                        爻位 = yao.get("爻位", "")
                        if 爻位 in ("用九", "用六"):
                            if "爻位序" in yao and yao.get("爻位序") != 0:
                                errors.append(f"{prefix} 爻辞[{i}] 用九/用六 爻位序应为 0")
                        elif "爻位序" in yao and yao.get("爻位序") != i + 1:
                            errors.append(f"{prefix} 爻辞[{i}] 爻位序应为 {i+1}")

    return errors
