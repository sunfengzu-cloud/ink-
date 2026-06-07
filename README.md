# ink — 知识摄入笔记

视频 / PDF / 文章 → 结构化知识卡片 → Obsidian 知识库 + 分享网站

完整方法论手册：[methodology/README.md](methodology/README.md)

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

```
learn-notes/
└── <课程名>/
    ├── cards/              # Obsidian 卡片（可导入 Obsidian）
    │   ├── 监督学习.md
    │   ├── 损失函数.md
    │   └── 梯度下降.md
    ├── assets/             # 截图等附件
    ├── README.md           # 索引
    ├── MOC.md              # 知识图谱 + 孤岛卡片检测
    └── _site/              # 静态网站（可直接分享）
        ├── index.html
        ├── cards.html      # 所有卡片
        ├── moc.html        # 知识图谱
        └── review.html     # 复习问答（点击显示答案）
```

## 内置笔记方法论

### 看/读时
- 只记时间戳 + 关键词 + 疑问，不写完整句子
- `[!]` 标记没懂，`→` 标记关联
- 课后 24 小时内整理

### 整理时（工具自动化）
- LLM 拆分概念 → 生成卡片草稿（原文→理解→盲区→例子→思考题）
- 你只需要：确认理解没歪 + 补充自己的思考
- 对比自查：工具高亮你的理解 vs 原文的差异
- 至少关联一张已有卡片

### 复习时
- 每张卡片附带思考题（LLM 生成，三个层次：反思、联系、批判）
- 复习问答页：点击显示答案，检验自己能否复述
- 孤岛卡片检测：从未被引用的卡片需要处理（删或强制链接）
- 可导出为 Anki 格式

### 分享
- 自动生成静态网站，可直接部署到 GitHub Pages
- 复习问答页可自测
- 无需对方安装任何软件，打开浏览器即可
