# ink — 知识摄入笔记

视频 / PDF / 文章 → 结构化知识卡片 → Obsidian 知识库

## 安装

```bash
pip install -r requirements.txt
```

需要 `ffmpeg` 在 PATH 中（截图功能需要）。

## 使用方法

### CLI

```bash
# 视频 + 字幕
python cli.py lesson.mp4 --sub lesson.vtt

# PDF 文档
python cli.py paper.pdf

# Markdown 笔记
python cli.py notes.md

# 整个文件夹递归处理
python cli.py course-folder/ --output my-vault

# 指定 LLM API key
python cli.py video.mp4 --sub sub.vtt --api-key YOUR_KEY

# 纯模板（不用 LLM）
python cli.py doc.pdf --no-llm
```

环境变量：`INK_API_KEY`

### Web UI

```bash
python app.py
# 打开 http://localhost:8080
```

## 输出

生成 Obsidian 格式的知识库：

```
learn-notes/
└── <课程名>/
    ├── cards/
    │   ├── 监督学习.md
    │   ├── 损失函数.md
    │   └── 梯度下降.md
    ├── assets/
    │   └── screenshot_000.png
    ├── README.md       # 索引
    └── MOC.md          # 知识图谱
```

## 笔记方法论

### 看/读时
- 只记时间戳 + 关键词 + 疑问
- `[!]` 标记没懂，`→` 标记关联
- 不写完整句子

### 整理时
- 一张卡片一个概念
- 不复制粘贴
- 格式：原文 → 自己的话 → 盲区 → 例子
- 至少关联一张已有卡片

### 复习时
- 每周随机抽 5 张，尝试复述
- 说不清的回看原素材
- 检查孤岛卡片
