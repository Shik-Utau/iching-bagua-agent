"""
融合卦爻关联文件：保留原文本的原文与翻译，删除原文本的说明，替换为 new 的说明。
支持任意卦。对 new 的说明进行格式编排：根据重点词分行、用 + 做无编号陈列、适度加粗，不更改原文。
"""

import re
from pathlib import Path

# 重点词行模式：以 "xxx"： 或 "xxx"（ 开头（支持 ASCII " 与 Unicode ""）
_KEY_PHRASE_PATTERN = re.compile(r'^[\u0022\u201c\u201d][^\u0022\u201c\u201d]+[\u0022\u201c\u201d][：:（]')
# 小标题加粗
_LABELS_BOLD = (
    "核心主题", "核心短词", "卦象", "核心卦辞", "总纲", "本质", "相关性", "总结",
    "是现象", "是内在修养", "是外在行动", "破局之道", "关键路径",
    "重要警示", "领导力陷阱", "关键禁忌", "核心精神",
)


def _format_explanation_text(text: str) -> str:
    """
    对说明文本进行格式编排：根据重点词分行、用 + 做无编号陈列、适度加粗。不更改原文。
    """
    if not text.strip():
        return text

    lines = [ln.rstrip() for ln in text.split("\n")]
    out = []
    in_list = False  # 是否处于连续的重点词陈列中

    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            out.append("")
            in_list = False
            continue

        is_key_phrase = bool(_KEY_PHRASE_PATTERN.match(s))
        # 爻传补充"xxx"： 也视为重点词行
        if not is_key_phrase and s.startswith("爻传") and "：" in s:
            is_key_phrase = True

        if is_key_phrase:
            # 重点词行：加 + 做无编号陈列
            out.append("+ " + s)
            in_list = True
        else:
            if in_list:
                in_list = False
            # 加粗小标题
            for label in _LABELS_BOLD:
                if s.startswith(label + "：") or s.startswith(label + ":"):
                    s = f"**{label}**" + s[len(label):]
                    break
            # 初九：、六二： 等爻名
            s = re.sub(
                r"^((?:初[六九]|六[二三四五]|九[二三四五]|上[六九])[：:])",
                r"**\1**",
                s,
            )
            # 句中加粗短语（不打断文字）
            for phrase in ("关键禁忌", "核心精神", "关键路径", "破局之道"):
                if phrase in s and f"**{phrase}**" not in s:
                    s = s.replace(phrase, f"**{phrase}**", 1)
            out.append(s)

    return "\n".join(out)


def _remove_trailing_drop_blocks(lines: list) -> list:
    """从行列表中移除末尾的 定位/解读/核心/说明 块。"""
    DROP = ("**定位**", "**解读**", "**核心**", "**说明**", "**困惑点**", "**解答**")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if any(stripped.startswith(p) for p in DROP):
            i += 1
            while i < len(lines):
                n = lines[i]
                ns = n.strip()
                if not ns:
                    i += 1
                    continue
                if any(ns.startswith(p) for p in DROP):
                    break
                if ns.startswith("###"):
                    break
                if ns.startswith("**原文**") or ns.startswith("**白话**"):
                    break
                i += 1
            continue
        out.append(line)
        i += 1
    return out


def parse_original(path: Path) -> dict:
    """
    解析原文件，按块切分，保留原文+翻译，删除 定位/解读/核心/说明。
    支持 总论、卦象简述 等任意 ## 节（保留 ## 卦辞 之前全部内容）。
    """
    text = path.read_text(encoding="utf-8")
    result = {"header_before": [], "卦象简述_block": [], "卦辞": [], "爻辞": {}}

    # 分离：header_before（卦名、卦画）+ 卦象简述_block（第一个 ## 到 ## 卦辞）
    idx_卦辞 = text.find("## 卦辞")
    before_卦辞 = text[:idx_卦辞].rstrip() if idx_卦辞 >= 0 else text
    first_h2 = before_卦辞.find("## ")
    if first_h2 >= 0:
        result["header_before"] = before_卦辞[:first_h2].rstrip().split("\n")
        result["卦象简述_block"] = before_卦辞[first_h2:].rstrip().split("\n")
    else:
        result["header_before"] = before_卦辞.split("\n")
        result["卦象简述_block"] = []

    parts = re.split(r"^(## .+)$", text, flags=re.MULTILINE)

    for i, p in enumerate(parts):
        if not p.strip():
            continue
        s = p.strip()
        if s == "## 卦辞":
            content = parts[i + 1] if i + 1 < len(parts) else ""
            content = re.sub(
                r"\n### 说明\n[\s\S]*?(?=\n### |\n## |\Z)",
                "\n",
                content,
            )
            result["卦辞"] = [x for x in content.split("\n") if x is not None]
            if result["卦辞"] and result["卦辞"][-1] == "":
                result["卦辞"] = result["卦辞"][:-1]
        elif s == "## 爻辞":
            content = parts[i + 1] if i + 1 < len(parts) else ""
            result["爻辞"]["_raw"] = content
            break

    raw = result["爻辞"].get("_raw", "")
    yao_blocks = re.split(r"\n(### (?:初[六九]|六[二三四五]|九[二三四五]|上[六九])：.+)", raw)

    for j in range(1, len(yao_blocks), 2):
        if j + 1 >= len(yao_blocks):
            break
        title = yao_blocks[j]
        body = yao_blocks[j + 1]
        m = re.match(r"### (初[六九]|六[二三四五]|九[二三四五]|上[六九])：", title)
        if m:
            yao = m.group(1)
            cleaned = _remove_trailing_drop_blocks((title + "\n" + body).split("\n"))
            result["爻辞"][yao] = cleaned

    return result


def parse_new_explanations(path: Path) -> dict:
    """解析 new.md，提取总论、核心主题（含核心卦辞、总纲等）、各爻说明、总结。"""
    text = path.read_text(encoding="utf-8")
    result = {"总论": "", "核心主题": "", "爻": {}, "总结": ""}

    # 总论：从 "总论" 或 "xxx总论" 到 问： 之间的内容，用于替代卦象简述
    m = re.search(r"(?:^|\n).*总论[：:]\s*([\s\S]+?)(?=\n\n问[：:]|\n总结[：:]|\Z)", text)
    if m:
        result["总论"] = m.group(1).strip()

    # 从 核心主题 到 问： 之间的内容（若无总论则用此；若有总论则核心主题用于卦辞说明）
    m = re.search(r"核心主题[：:]\s*([\s\S]+?)(?=\n\n问[：:]|\n总结[：:]|\Z)", text)
    if m:
        result["核心主题"] = m.group(1).strip()
    elif not result["总论"]:
        # 无核心主题时，总论可兼作核心主题
        result["核心主题"] = result["总论"]

    blocks = re.split(r"\n\n问[：:]", text)
    for blk in blocks[1:]:
        blk = "问：" + blk
        qm = re.search(r"问[：:][^答]*答[：:]\s*([\s\S]+?)(?=\n\n问：|\n总结：|\Z)", blk)
        if qm:
            ans = qm.group(1).strip()
            q_yao = re.search(r"([初六九二三四五上]{2})", blk)
            if q_yao:
                yao = q_yao.group(1)
                result["爻"][yao] = ans

    m = re.search(r"总结[：:]\s*([\s\S]+)", text)
    if m:
        result["总结"] = "总结：" + m.group(1).strip()  # 保留 总结： 便于加粗

    return result


# 标准爻序（用于排序，不同卦可能只有其中部分）
_YAO_ORDER = ["初九", "初六", "九二", "六二", "九三", "六三", "九四", "六四", "九五", "六五", "上九", "上六"]


def _sorted_yao_keys(yao_dict: dict) -> list:
    """按标准爻序排序，仅返回实际存在的爻。"""
    order = {y: i for i, y in enumerate(_YAO_ORDER)}
    keys = [k for k in yao_dict if k != "_raw"]
    return sorted(keys, key=lambda k: order.get(k, 999))


def merge(orig_path: Path, new_path: Path, out_path: Path) -> None:
    """执行融合并写入输出文件。"""
    orig = parse_original(orig_path)
    new_exp = parse_new_explanations(new_path)

    out_lines = []
    out_lines.extend(orig["header_before"])
    out_lines.append("")

    # 总论替代卦象简述：若有 new 的 总论 则用其（含格式编排），否则保留原卦象简述
    if new_exp["总论"]:
        out_lines.append("## 总论")
        out_lines.append("")
        formatted = _format_explanation_text(new_exp["总论"])
        for line in formatted.split("\n"):
            out_lines.append(line)
        out_lines.append("")
    elif orig["卦象简述_block"]:
        out_lines.extend(orig["卦象简述_block"])
        out_lines.append("")

    out_lines.append("## 卦辞")
    out_lines.append("")
    out_lines.extend(orig["卦辞"])
    out_lines.append("")

    if new_exp["核心主题"]:
        out_lines.append("### 说明")
        out_lines.append("")
        out_lines.append(_format_explanation_text(new_exp["核心主题"]))
        out_lines.append("")

    out_lines.append("## 爻辞")
    out_lines.append("")

    for yao in _sorted_yao_keys(orig["爻辞"]):
        block = orig["爻辞"][yao]
        out_lines.extend(block)
        out_lines.append("")
        if yao in new_exp["爻"]:
            out_lines.append("**说明**")
            out_lines.append("")
            formatted = _format_explanation_text(new_exp["爻"][yao])
            for line in formatted.split("\n"):
                out_lines.append(line)
            out_lines.append("")
        out_lines.append("")

    if new_exp["总结"]:
        out_lines.append("## 总结")
        out_lines.append("")
        formatted = _format_explanation_text(new_exp["总结"])
        for line in formatted.split("\n"):
            out_lines.append(line)

    out_path.write_text("\n".join(out_lines).rstrip() + "\n", encoding="utf-8")
