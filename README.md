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
  hexagrams/       # 六十四卦卦爻辞（每卦一文件）
src/iching_bagua/  # 核心模块
scripts/           # 录入脚本
.env.example       # 环境变量示例（DeepSeek API）
```
