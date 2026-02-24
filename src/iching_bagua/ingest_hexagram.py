"""基于 LLM 将大段文本转化为卦爻辞 JSON。"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from iching_bagua.hexagrams import HEXAGRAMS_DIR

# override=True：项目 .env 优先于系统环境变量，避免使用错误的 key
load_dotenv(override=True)

BAGUA = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}

SCHEMA_PROMPT = """你是一位易经专家。请将用户提供的卦爻辞文本，转化为以下 JSON 格式。只输出 JSON，不要输出任何其他文字。

JSON 结构：
{
  "元信息": {
    "卦名": "卦名（如乾、坤）",
    "卦序": 1-64 的整数,
    "卦画": "Unicode 卦画符号（卦序 n 对应 chr(0x4DC0+n-1)）",
    "上下卦": {
      "上卦": "乾/坤/震/巽/坎/离/艮/兑",
      "上卦数": 1-8,
      "下卦": "同上",
      "下卦数": 1-8
    },
    "别名": ["别名1", "别名2"]
  },
  "卦辞": {
    "原文": "卦辞原文",
    "白话": "白话翻译",
    "彖传": "彖传全文或 null",
    "大象传": "大象传或 null",
    "关键词": ["关键词1", "关键词2"],
    "吉凶标签": "吉凶标签或 null"
  },
  "爻辞": [
    {
      "爻位": "初九/九二/.../上九 或 初六/六二/.../上六",
      "爻位序": 1-6,
      "阴阳": "阳 或 阴",
      "当位": true 或 false,
      "原文": "爻辞原文",
      "白话": "白话翻译",
      "小象传": "小象传或 null",
      "吉凶标签": "吉凶标签或 null",
      "爻象推导": {"本爻象": "...", "取象": "...", "逻辑": "..."} 或 null,
      "关联映射": ["映射1", "映射2"],
      "应爻": "应爻名或 null",
      "承乘": []
    }
  ]
}

规则：
- 八卦：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
- 阳爻（九）当位：初、三、五；阴爻（六）当位：二、四、上
- 乾卦可含第7条爻辞「用九」（爻位序0，当位null）；坤卦可含「用六」
- 文本中缺失的字段用 null 或空数组
- 卦画：卦序1对应䷀(U+4DC0)，卦序n对应 chr(0x4DC0+n-1)
"""


def _get_client():
    """获取 DeepSeek API 客户端。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "请设置环境变量 DEEPSEEK_API_KEY。例如：export DEEPSEEK_API_KEY=sk-xxx"
        )
    from openai import OpenAI

    return OpenAI(
        api_key=api_key,
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    )


def _extract_json(text: str) -> dict:
    """从 LLM 输出中提取 JSON。"""
    # 尝试直接解析
    text = text.strip()
    # 去除可能的 markdown 代码块
    if "```json" in text:
        text = re.search(r"```json\s*([\s\S]*?)```", text)
        text = text.group(1).strip() if text else text
    elif "```" in text:
        text = re.search(r"```\s*([\s\S]*?)```", text)
        text = text.group(1).strip() if text else text
    return json.loads(text)


def _ensure_schema(data: dict) -> dict:
    """确保输出符合 schema，补全卦画等。"""
    meta = data.get("元信息", {})
    卦序 = meta.get("卦序")
    if 卦序 is not None and isinstance(卦序, int):
        if "卦画" not in meta or not meta["卦画"]:
            meta["卦画"] = chr(0x4DC0 + 卦序 - 1)
        if "上下卦" in meta:
            sq = meta["上下卦"]
            for k in ("上卦", "下卦"):
                if k in sq and sq[k] in BAGUA and f"{k}数" not in sq:
                    sq[f"{k}数"] = BAGUA[sq[k]]
    return data


def text_to_hexagram_json(text: str, model: str = "deepseek-chat") -> dict:
    """将大段文本转化为卦爻辞 JSON。

    Args:
        text: 卦爻辞相关文本（可从书籍、网页等复制）
        model: DeepSeek 模型名

    Returns:
        符合 schema 的卦数据字典

    Raises:
        RuntimeError: 未设置 DEEPSEEK_API_KEY
        json.JSONDecodeError: LLM 输出无法解析为 JSON
    """
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCHEMA_PROMPT},
            {"role": "user", "content": f"请将以下文本转化为卦爻辞 JSON：\n\n{text}"},
        ],
        temperature=0.2,
    )
    content = response.choices[0].message.content
    data = _extract_json(content)
    return _ensure_schema(data)


def ingest_and_save(
    text: str,
    output_dir: Path | str | None = None,
    model: str = "deepseek-chat",
) -> Path:
    """将文本转化为 JSON 并保存到 data/hexagrams/。

    Returns:
        保存后的文件路径
    """
    data = text_to_hexagram_json(text, model=model)
    meta = data.get("元信息", {})
    卦序 = meta.get("卦序")
    卦名 = meta.get("卦名", "未知")
    if not 卦序 or not isinstance(卦序, int):
        raise ValueError("无法从文本中识别卦序，请确保文本包含卦名或卦序信息")

    d = Path(output_dir) if output_dir else HEXAGRAMS_DIR
    d.mkdir(parents=True, exist_ok=True)
    out_path = d / f"{卦序:02d}_{卦名}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return out_path
