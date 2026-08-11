# IEEE Paper Doctor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/XiaojuCH/ieee-journal-single-to-double?style=social)](https://github.com/XiaojuCH/ieee-journal-single-to-double/stargazers)
[![Test IEEE Paper Doctor](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml/badge.svg)](https://github.com/XiaojuCH/ieee-journal-single-to-double/actions/workflows/compile.yml)

**[English](README.md)** | **中文说明**

把 IEEEtran 单栏草稿安全转换为双栏期刊稿：项目级检查、可审查 diff、PDF 编译证据，全程不改论文的科学内容。

把 `onecolumn` 改成 `twocolumn` 只要一行；处理作者单位、跨栏图表、`[H]` 浮动体、参考文献页和各种空白却远不止一行。IEEE Paper Doctor 把 Codex skill 和无第三方依赖的 CLI 组合起来：机械修改由脚本稳定完成，需要判断的排版问题保留给人和 Codex 审查。

## 30 秒开始使用

直接从 GitHub 安装命令行工具：

```bash
pipx install git+https://github.com/XiaojuCH/ieee-journal-single-to-double.git
```

检查单文件论文，不修改内容：

```bash
ieee-paper-doctor check path/to/main.tex --strict
```

多文件论文直接传项目目录。CLI 会自动找到 IEEEtran 主文件，并递归跟踪 `\input`、`\include` 和 `\subfile`：

```bash
ieee-paper-doctor check path/to/project --strict
ieee-paper-doctor check path/to/project --report paper-audit.md
```

以 unified diff 预览保守修复：

```bash
ieee-paper-doctor fix path/to/main.tex
```

输出到新文件，再编译验证：

```bash
ieee-paper-doctor fix path/to/main.tex --output path/to/main.twocolumn.tex
ieee-paper-doctor verify path/to/main.twocolumn.tex --compile --strict
```

除非显式传入 `--write`，`fix` 永远不会覆盖输入文件。

## 作为 Codex skill 使用

让 Codex 从本仓库安装：

```text
$skill-installer 从 https://github.com/XiaojuCH/ieee-journal-single-to-double/tree/master/skills/ieee-paper-doctor 安装 ieee-paper-doctor
```

然后在论文项目中调用：

```text
$ieee-paper-doctor 把这篇 IEEEtran 单栏草稿转换成双栏期刊投稿版。保留科学内容，先展示 diff，再编译 PDF，并报告剩余排版风险。
```

仓库同时提供 `.codex-plugin/plugin.json`，可以作为 Codex plugin 分发。

## 能检查什么

- 任意顺序下的 `draftcls`、`draftclsnofoot`、`onecolumn` 和冲突文档类选项。
- journal 模式里残留的会议式 `\IEEEauthorblockN` / `\IEEEauthorblockA`。
- 需要重新判断位置的 `[H]` 图、表和算法。
- 单栏浮动体里的 `\textwidth` 和 `1.x\textwidth` 超宽尺寸。
- 当前投稿阶段可能不需要的作者简介和照片占位符。
- 参考文献之后残留的内容。
- 缺失或动态生成、无法解析的 TeX 子文件。
- 编译前即可发现跨文件缺失的 `\ref` 标签。
- 编译错误、过大浮动体、横向/纵向溢出和未定义引用。

使用 `--format json` 输出机器可读诊断，使用 `--format github` 在 GitHub Actions 中精确标注源码行；`--strict` 会让 warning 在 CI 中返回失败。`--report` 可生成便于协作分享的 Markdown 审计报告。

## 项目级审计

v1.2 不再只把 `main.tex` 当作整篇论文。它能从目录中自动发现唯一的 IEEEtran 主文件，同时兼容项目根目录和当前源码目录两种引用路径，递归扫描所有章节，即使出现循环引用也只检查一次，并把每个问题定位到真实文件和行号。如果目录中有多个候选主文件，工具会停止并要求明确指定，而不会擅自猜测。

```bash
# 适合本地阅读的项目审计
ieee-paper-doctor check ./paper --strict

# 在 CI 中标注准确文件和行号
ieee-paper-doctor check ./paper --strict --format github

# 编译主文件并保存审计报告
ieee-paper-doctor verify ./paper --compile --report ieee-audit.md
```

## 会自动修改什么

CLI 故意只自动执行容易审查的修改：

- 规范 IEEEtran journal 文档类选项，显式切换双栏；
- 把单栏浮动体里明显错误的 `\textwidth` 改成 `\columnwidth`；
- 保留正文、公式、图注、标签、引用和实验结果；
- 修改前给出幂等 diff。

是否使用 `figure*` / `table*`、怎样重建作者单位、是否删除 biography、要不要加入浮动体宏包，仍由 skill 根据目标期刊和编译结果判断。

## 转换前后

| 单栏草稿 | 修正后的双栏稿 |
|:---:|:---:|
| ![单栏草稿第一页](assets/before-page1.png) | ![双栏结果第一页](assets/after-page1.png) |
| ![草稿浮动体](assets/before-page2.png) | ![修正后的浮动体](assets/after-page2.png) |

完整示例位于 [`examples/before`](examples/before)、[`examples/after`](examples/after) 和多文件项目 [`examples/project`](examples/project)。

## 范围与安全边界

IEEE Paper Doctor 只处理 IEEEtran LaTeX 期刊论文，不转换 Word，也不处理 ACM、Springer、Elsevier 或任意 LaTeX 模板。

目标期刊的最新要求始终优先。处理作者信息、biography 和浮动体之前，先确认具体期刊以及初投、返修或终稿阶段。最终可继续使用 IEEE Template Selector、LaTeX Analyzer 和 PDF Checker 验证。

## 开发与测试

```bash
python -m unittest discover -s tests -v
python skills/ieee-paper-doctor/scripts/ieee_paper_doctor.py check examples/project --strict
```

CI 会运行单元测试、安装后的 CLI 冒烟测试，确认错误示例必须失败、修正示例必须通过，并编译 LaTeX 示例。

欢迎贡献最小可复现的 IEEEtran 排版问题和匿名真实转换案例，具体见 [CONTRIBUTING.md](CONTRIBUTING.md)。

如果它帮你少踩了一次排版坑，欢迎点一个 Star，让下一位作者更容易找到它。
