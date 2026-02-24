"""关联发现：基于重卦结构，输出 Markdown 解释文档。"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BAGUA_MAPPINGS_PATH = PROJECT_ROOT / "data" / "bagua_mappings" / "bagua_mappings.json"
HEXAGRAMS_DIR = PROJECT_ROOT / "data" / "hexagrams"
ASSOCIATIONS_DIR = PROJECT_ROOT / "data" / "associations"

# 爻位象：爻位序 -> 该爻位的取象描述
YAO_POSITION_DESC: dict[int, str] = {
    1: "初位为潜、为始、为卑下",
    2: "二位为中、为地面、为家中",
    3: "三位为极、为多凶、为人道之始",
    4: "四位为入上卦、为近君",
    5: "五位为君、为尊、为中正",
    6: "上位为终、为亢、为极",
}


def _load_bagua_mappings() -> dict:
    with open(BAGUA_MAPPINGS_PATH, encoding="utf-8") as f:
        return json.load(f)


def _get_bagua_summary(bagua: dict, 卦名: str, max_len: int = 200) -> str:
    """获取某卦的映射摘要，供 LLM 理解。"""
    data = bagua.get(卦名, {})
    描述 = data.get("描述", "")
    结构化 = data.get("结构化", {})
    parts = [描述]
    for 维度, 值 in list(结构化.items())[:4]:  # 自然、人事、性格、身体等
        if 值:
            # 取前几项
            items = 值.replace("，", "、").split("、")[:5]
            parts.append(f"{维度}：{'、'.join(x.strip() for x in items if x.strip())}")
    s = "；".join(parts)
    return s[:max_len] + "…" if len(s) > max_len else s


def _get_hexagram_files(hexagrams_dir: Path) -> list[Path]:
    """获取卦爻辞 JSON 文件列表，按卦序排序。"""
    files = list(hexagrams_dir.glob("*.json"))
    return sorted(files, key=lambda p: p.name)


def _get_openai_client():
    """获取 OpenAI 兼容客户端（DeepSeek）。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(
        api_key=api_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


def _llm_explain_paragraph(
    prompt: str,
    max_tokens: int = 400,
) -> str:
    """调用 LLM 生成解释段落，返回纯文本。"""
    client = _get_openai_client()
    if not client:
        return ""
    try:
        r = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return (r.choices[0].message.content or "").strip()
    except Exception:
        return ""


def _explain_hexagram_statement(
    上卦: str,
    下卦: str,
    卦辞: dict,
    bagua: dict,
    use_llm: bool,
) -> str:
    """卦辞解释：上卦与下卦映射如何组合以解释卦辞。"""
    text = f"{卦辞.get('原文', '')} {卦辞.get('白话', '')}".strip()
    if not text:
        return ""

    上卦摘要 = _get_bagua_summary(bagua, 上卦)
    下卦摘要 = _get_bagua_summary(bagua, 下卦)

    if not use_llm:
        return "（请使用 LLM 模式生成完整解释）"

    prompt = f"""你是一位易经专家。请根据上卦{上卦}与下卦{下卦}的映射，写一段解释性话语，说明二者如何组合以解释卦辞。

上卦{上卦}的映射：{上卦摘要}
下卦{下卦}的映射：{下卦摘要}

卦辞：{text}

要求：直接输出 2-5 句解释段落，说明上卦与下卦的取象如何结合、共同解释卦辞的含义。不要输出「根据」「综上所述」等套话，直接写解释内容。"""

    return _llm_explain_paragraph(prompt) or "（解释生成失败）"


def _explain_yao_statement(
    爻位序: int,
    爻位: str,
    上卦: str,
    下卦: str,
    爻辞: dict,
    bagua: dict,
    use_llm: bool,
) -> str:
    """爻辞解释：本卦、对卦、爻位象如何组合以解释爻辞。"""
    text = f"{爻辞.get('原文', '')} {爻辞.get('白话', '')}".strip()
    if not text:
        return ""

    if 爻位序 <= 3:
        本卦 = 下卦
        对卦 = 上卦
        所属 = "下卦"
    else:
        本卦 = 上卦
        对卦 = 下卦
        所属 = "上卦"

    本卦摘要 = _get_bagua_summary(bagua, 本卦)
    对卦摘要 = _get_bagua_summary(bagua, 对卦)
    爻位象 = YAO_POSITION_DESC.get(爻位序, "")

    if not use_llm:
        return "（请使用 LLM 模式生成完整解释）"

    prompt = f"""你是一位易经专家。请根据本爻所属{本卦}卦的映射、对卦{对卦}的映射、以及爻位象，写一段解释性话语，说明如何组合以解释爻辞。

本爻属{所属}{本卦}（爻位序{爻位序}）。
本卦{本卦}的映射：{本卦摘要}
对卦{对卦}的映射：{对卦摘要}
爻位象：{爻位象}

爻辞：{text}

要求：直接输出 2-5 句解释段落，说明本卦、对卦、爻位象如何结合以解释爻辞。不要输出「根据」「综上所述」等套话，直接写解释内容。"""

    return _llm_explain_paragraph(prompt) or "（解释生成失败）"


def _build_hexagram_summary(上卦: str, 下卦: str, 卦名: str, 别名: list, bagua: dict) -> str:
    """构建卦象简述。"""
    上描述 = bagua.get(上卦, {}).get("描述", "")
    下描述 = bagua.get(下卦, {}).get("描述", "")
    别名_str = "、".join(别名[:3]) if isinstance(别名, list) else str(别名 or "")
    return f"上卦{上卦}（{上描述}），下卦{下卦}（{下描述}）。{上卦}上{下卦}下，{别名_str}。"


def discover_associations(
    use_llm: bool = True,
    hexagrams_dir: Path | str | None = None,
    output_path: Path | str | None = None,
    hexagram_orders: list[int] | None = None,
) -> list[Path]:
    """执行关联发现，输出 Markdown 解释文档。每卦一 .md 文件。

    若指定 hexagram_orders，仅处理这些卦序。
    返回已保存的文件路径列表。
    """
    h_dir = Path(hexagrams_dir) if hexagrams_dir else HEXAGRAMS_DIR
    out_dir = ASSOCIATIONS_DIR
    if output_path:
        p = Path(output_path)
        if p.suffix:
            out_dir = p.parent
        else:
            out_dir = p

    bagua = _load_bagua_mappings()
    files = _get_hexagram_files(h_dir)

    if hexagram_orders:
        orders_set = set(hexagram_orders)
        files = [p for p in files if _parse_hexagram_order(p) in orders_set]
        if not files:
            return []

    out_dir.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []

    for p in files:
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        meta = data.get("元信息", {})
        卦序 = meta.get("卦序")
        卦名 = meta.get("卦名", "")
        卦画 = meta.get("卦画", "")
        上下卦 = meta.get("上下卦", {})
        上卦 = 上下卦.get("上卦")
        下卦 = 上下卦.get("下卦")
        别名 = meta.get("别名", [])

        if not 卦序 or not 上卦 or not 下卦:
            continue

        # 卦象简述
        卦象简述 = _build_hexagram_summary(上卦, 下卦, 卦名, 别名, bagua)

        # 卦辞
        卦辞 = data.get("卦辞", {})
        卦辞原文 = 卦辞.get("原文", "")
        卦辞白话 = 卦辞.get("白话", "")
        卦辞解释 = ""
        if 卦辞:
            if use_llm:
                print(f"  [{卦序}-gc] 卦辞...")
            卦辞解释 = _explain_hexagram_statement(上卦, 下卦, 卦辞, bagua, use_llm)

        # 爻辞
        爻辞块: list[str] = []
        for yao in data.get("爻辞", []):
            爻位序 = yao.get("爻位序")
            爻位 = yao.get("爻位", "")
            if 爻位序 is None:
                continue
            if use_llm:
                print(f"  [{卦序}-{爻位序}] {爻位}...")
            解释 = _explain_yao_statement(爻位序, 爻位, 上卦, 下卦, yao, bagua, use_llm)
            原文 = yao.get("原文", "")
            白话 = yao.get("白话", "")
            爻辞块.append(f"### {爻位}：{原文}\n\n{白话}\n\n{解释}")

        # 构建 Markdown
        md_lines = [
            f"# {卦名}卦（{上卦}上{下卦}下）",
            "",
            f"**卦画**：{卦画}",
            "",
            "## 卦象简述",
            "",
            卦象简述,
            "",
            "## 卦辞",
            "",
            f"**原文**：{卦辞原文}",
            "",
            f"**白话**：{卦辞白话}",
            "",
            卦辞解释,
            "",
            "## 爻辞",
            "",
        ]
        md_lines.extend("\n\n".join(爻辞块).split("\n"))

        out_file = out_dir / f"{卦序:02d}_{卦名}.md"
        out_file.write_text("\n".join(md_lines), encoding="utf-8")
        saved.append(out_file)
        if use_llm:
            print(f"  已保存: {out_file}")

    return saved


def _parse_hexagram_order(p: Path) -> int | None:
    """从文件名解析卦序，如 01_乾.json -> 1。"""
    try:
        return int(p.stem.split("_")[0])
    except (ValueError, IndexError):
        return None


def run_discovery() -> None:
    """CLI 入口：运行关联发现并保存 Markdown。"""
    print("关联发现（基于重卦结构，输出 Markdown 解释）...")
    saved = discover_associations(use_llm=True)
    print(f"完成，共保存 {len(saved)} 个 Markdown 文件")
