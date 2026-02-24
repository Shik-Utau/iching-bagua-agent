"""八卦映射数据加载与验证。"""

from pathlib import Path
import json

# 项目根目录（pyproject.toml 所在）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_MAPPINGS_PATH = PROJECT_ROOT / "data" / "bagua_mappings" / "bagua_mappings.json"

# 八卦名称（用于校验）
BAGUA_NAMES = {"乾", "坤", "震", "巽", "坎", "离", "艮", "兑"}

# 结构化数据必填维度
REQUIRED_STRUCTURED_DIMS = {"自然", "人事", "性格", "身体", "动物", "器物", "数理"}


def load(path: Path | str | None = None) -> dict:
    """加载八卦映射 JSON 数据。

    Args:
        path: JSON 文件路径，默认使用 data/bagua_mappings/bagua_mappings.json

    Returns:
        八卦映射字典，键为卦名（乾、坤等），值为该卦的映射信息

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 格式错误
    """
    p = Path(path) if path else DEFAULT_MAPPINGS_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def validate(data: dict | None = None, path: Path | str | None = None) -> list[str]:
    """验证八卦映射数据的完整性与一致性。

    Args:
        data: 已加载的映射数据，若为 None 则从 path 加载
        path: 数据文件路径，当 data 为 None 时使用

    Returns:
        错误信息列表，空列表表示验证通过
    """
    errors: list[str] = []

    if data is None:
        try:
            data = load(path)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return [f"加载失败: {e}"]

    # 1. 必须包含 8 卦
    if len(data) != 8:
        errors.append(f"卦数量应为 8，当前为 {len(data)}")

    # 2. 卦名必须正确
    missing = BAGUA_NAMES - set(data.keys())
    if missing:
        errors.append(f"缺少卦: {missing}")

    extra = set(data.keys()) - BAGUA_NAMES
    if extra:
        errors.append(f"未知卦名: {extra}")

    # 3. 每卦结构校验
    for name, gua in data.items():
        prefix = f"[{name}]"

        if not isinstance(gua, dict):
            errors.append(f"{prefix} 应为对象")
            continue

        # 必填顶层字段
        for field in ("卦象", "象征", "结构化", "描述"):
            if field not in gua:
                errors.append(f"{prefix} 缺少字段: {field}")

        # 结构化
        if "结构化" in gua:
            struct = gua["结构化"]
            if not isinstance(struct, dict):
                errors.append(f"{prefix} 结构化 应为对象")
            else:
                missing_dims = REQUIRED_STRUCTURED_DIMS - set(struct.keys())
                if missing_dims:
                    errors.append(f"{prefix} 结构化缺少维度: {missing_dims}")

        # 时空（可为空对象）
        if "时空" in gua and not isinstance(gua["时空"], dict):
            errors.append(f"{prefix} 时空 应为对象")

    return errors
