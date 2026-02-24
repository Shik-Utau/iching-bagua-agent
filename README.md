# 易经八卦映射智能体

基于八卦映射与卦爻辞的语义关联，为智能体提供检索、解释与推荐能力。

详见 [DESIGN.md](./DESIGN.md) 了解分阶段开发方案。

## 快速开始

```bash
# 安装依赖（uv）
uv sync

# 加载八卦映射
uv run load-bagua

# 验证数据
uv run validate-bagua
```

## 项目结构

```
data/bagua_mappings/   # 八卦映射 JSON
src/iching_bagua/      # 核心模块
```
