# MoE 训练终极手册（中文翻译版）

> **The Ultimate MoE Training Handbook** 的简体中文翻译版
>
> 一本按设置逐项讲解如何大规模训练混合专家（Mixture-of-Experts, MoE）模型的实战手册：路由器、负载均衡、专家、模块布局、训练稳定性与系统优化。

![预览](assets/preview.png)

- 原文：[Hugging Face Spaces · huggingface/moe-blogpost](https://huggingface.co/spaces/huggingface/moe-blogpost)
- 在线阅读：[leonyuhe.github.io/moe-handbook-zh](https://leonyuhe.github.io/moe-handbook-zh/)
- 作者：Nouamane Tazi、Leandro von Werra、Thomas Wolf（Hugging Face）
- 中文翻译维护：[leonyuhe](https://github.com/leonyuhe)

## 关于这本书

从稠密模型转到 MoE，会多出三件必须处理的事：为每个 token 选择专家的路由器、在专家之间维持均衡的负载，以及专家分散到多张 GPU 之后、每个 MoE 层都要发生的 token 全对全交换。每一项都带来稠密训练从未有过的设置，也带来新的失败方式。

本书按这些设置逐项展开，配合可直接运行的 Megatron-LM 代码、集群实验数据和失败排查索引。全书包括：

1. **引言**：为什么前沿模型走向稀疏，以及训练 MoE 的三个新问题
2. **环境搭建与第一次运行**：硬件检查、镜像构建、分词、稠密基线，以及你的第一个 MoE
3. **MoE 训练剖析**：监控、路由打分、路由策略、负载均衡、专家配置、模块布局、训练稳定性、系统性能
4. **从训练到推理**：推理时的 top-k、低比特专家、专家并行、Attention-FFN 分离、RL 路由
5. **结论**与致谢
6. **附录**：监控细节、42 条症状的调试索引、代码与配置

## 翻译说明

- 正文、章节标题、图注、表格和界面文案已翻译为简体中文。
- 代码、命令行参数、变量名、URL、模型名、论文名、数字与公式保持原文，避免破坏可运行性。
- 交互式图表由原站脚本渲染，**图内标签**与**脚注引用卡片**保留英文原文；正文对每张图的解释均已翻译。
- 本译文为社区翻译，**非 Hugging Face 官方中文版**。如发现术语或表述问题，欢迎提交 Issue / PR。

## 本地运行

需要 Node.js 20+。

```bash
cd app
npm install
npm run dev          # 本地开发，默认 http://localhost:4321/moe-handbook-zh/
```

构建静态站点：

```bash
cd app
npm run build        # 输出到 app/dist
```

## 部署到 GitHub Pages

在线站点：<https://leonyuhe.github.io/moe-handbook-zh/>

仓库中的 `docs/` 是构建好的静态站点，`gh-pages` 分支与它保持同步，GitHub Pages 从该分支发布。

重新构建并发布：

```bash
cd app
npm install
npm run build:gh
cd ..
git add docs
git commit -m "rebuild site"
git subtree push --prefix docs origin gh-pages
```

`build:gh` 会依次执行 Astro 构建、把根路径资源改写成 `/moe-handbook-zh/` 前缀，并把产物复制到 `docs/`；最后一步把 `docs/` 推到 `gh-pages` 分支。

## 目录结构

```text
.
├── app/                 # Astro 源码（内容、组件、交互图脚本）
│   ├── src/content/     # 中文章节 MDX
│   ├── public/          # 图片、交互图与静态资源
│   └── plugins/         # Markdown / 引用 / 代码块插件
├── docs/                # 构建产物，GitHub Pages 站点根目录
├── tools/               # 翻译分块、校验、回填与路径修正脚本
├── LICENSE              # CC BY 4.0
└── NOTICE               # 原文署名与翻译说明
```

## 许可与署名

原文及图表由 Hugging Face 与原作者以 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) 发布。本译文沿用同一许可，转载请注明原文与译者，并链接到本仓库。

详见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。

## 致谢

感谢 Nouamane Tazi、Leandro von Werra、Thomas Wolf 写出这本手册，并开放原文与全部图表；感谢 Hugging Face 提供原文与交互式图表。
