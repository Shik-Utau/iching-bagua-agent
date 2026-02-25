# 易经八卦映射智能体

基于八卦映射与卦爻辞的语义关联，为智能体提供检索、解释与推荐能力。

详见 [DESIGN.md](./DESIGN.md) 了解分阶段开发方案。

## 快速开始

```bash
# 安装依赖（uv）
uv sync

# 八卦映射
uv run load-bagua
uv run validate-bagua

# 卦爻辞
uv run validate-hexagrams
uv run check-hexagram-literature   # 检查彖传、象传等文献是否完整
uv run hexagram-relations 乾       # 卦象关系：错卦、综卦、同上下卦、关键词相似
uv run compare-hexagrams 乾 坤    # 两卦对比（结构、卦辞、爻辞）
uv run series-compare 上经前六卦  # 卦系列对比（含坎、屯蒙需讼师比等预设）
uv run series-compare --list-presets  # 列出可用预设

# 别名
uv run similar-hexagrams 乾  # 同 hexagram-relations
uv run add-hexagram        # 交互式录入
uv run ingest-hexagram     # 智能录入：大段文本 → JSON
```

### 智能录入（ingest-hexagram）

需设置环境变量 `DEEPSEEK_API_KEY`（可选 `DEEPSEEK_BASE_URL`）。可复制 `.env.example` 为 `.env` 并填入。

```bash
# 从文件读取文本，自动保存到 data/hexagrams/
uv run ingest-hexagram -f 某卦.txt

# 从 stdin 管道
cat 某卦.txt | uv run ingest-hexagram

# 仅输出 JSON 到 stdout，不保存
uv run ingest-hexagram -f 某卦.txt --stdout

# 指定输出路径
uv run ingest-hexagram -f 某卦.txt -o output.json
```

## 项目结构

```
data/
  bagua_mappings/   # 八卦映射 JSON
  hexagrams/        # 六十四卦卦爻辞（每卦一文件）
  associations/     # 关联发现 Markdown
  comparisons/      # 两卦对比、系列对比 Markdown
src/
  iching_bagua/     # 核心模块
  association/      # 关联发现
  comparison/       # 卦象对比（错卦、综卦、相似卦、两卦对比、系列对比）
  agent/            # Agent 工具封装（tool_find_similar 等）
scripts/            # 录入脚本
.env.example        # 环境变量示例（DeepSeek API）
```

### Agent 工具（Python API）

```python
from agent.tools import tool_find_similar, tool_compare_two, tool_compare_series, get_tool_definitions

# 相似卦
r = tool_find_similar("乾")  # -> {错卦, 综卦, 同上下卦, 关键词相似, ...}

# 两卦对比
r = tool_compare_two("乾", "坤")  # -> {structure, 卦辞, 爻辞}

# 系列对比
r = tool_compare_series("上经前六卦")  # -> {卦列表, 卦辞, 爻位对比}

# OpenAI function calling 工具定义
tools = get_tool_definitions()
```
