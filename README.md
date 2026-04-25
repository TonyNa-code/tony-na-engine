<p align="center">
  <img src="docs/github/tn-engine-hero.png" alt="Tony Na Engine hero" width="100%" />
</p>

<h1 align="center">Tony Na Engine</h1>

<p align="center">
  一套面向视觉小说 / Galgame 创作者的可视化引擎原型。<br />
  目标是让“不懂编程的人”，也能用上传素材、输入台词、点按钮和可视化编辑的方式完成游戏开发。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-source--available%20preview-3fb7ff?style=for-the-badge" alt="Status: Source-Available Preview" />
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-0e1628?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/tests-smoke%20%2B%20playwright-1fc98b?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/license-Creator%20License%201.0-f5c451?style=for-the-badge" alt="Creator License 1.0" />
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#当前已经有的核心能力">核心能力</a> ·
  <a href="#发布状态">发布状态</a> ·
  <a href="CONTRIBUTING.md">参与贡献</a>
</p>

---

## 项目定位

Tony Na Engine 当前更适合这样理解：

- `源码可见创作者预览版`
- `Early Access / Preview`
- `适合独立开发者、同人作者、内部测试成员先拿来试做项目`

当前版本已经具备较完整的编辑器能力、导出能力和自动化测试基础，但仍然保留以下发布边界：

- 已接入后端 smoke、浏览器 Playwright smoke 和发布前自检脚本
- 适合做小型项目试制、导出链验证、功能体验和问题反馈
- 仍按 **Preview / Early Access** 口径发布；正式商业稳定版会在签名、公证、安装器和长流程点测进一步完成后单独标记

## 当前已经有的核心能力

- 可视化剧情编辑器
- 项目中心与空白新建项目
- 新手模式 / 高级模式分层
- 角色、素材、台词台本、配音工作流
- 项目巡检、一键发布前修复顺序、自动回归试玩路线测试
- 正式存档 / 读档、系统菜单
- 项目级成品 UI 皮肤、UI Kit 部件绑定、九宫格贴图、按钮多状态贴图、布局位置微调与视觉小说文本框设计
- EXTRA 回想馆、图鉴馆、成就馆、章节回放、结局回放、语音回听
- 高级粒子系统、项目级粒子预设库
- 网页试玩包、Windows 桌面包、编辑器桌面包、三系统编辑器套装
- 自动化测试体系（后端 smoke + Playwright 浏览器烟测）

## 仓库结构

- [`run_editor.py`](run_editor.py)  
  本地编辑器服务、导出链、项目管理、打包链的主入口

- [`prototype_editor`](prototype_editor)  
  编辑器前端

- [`export_player_template`](export_player_template)  
  导出后玩家端 Runtime 模板

- [`template_project`](template_project)  
  示例项目

- [`tests`](tests)  
  自动化测试

## 快速开始

### 运行环境

- Python 3
- macOS / Windows / Linux

如果只想启动编辑器，默认依赖只有 Python 3。

### 启动编辑器

最简单的方式是使用对应系统的启动脚本：

- macOS：双击 [`start_editor.command`](start_editor.command)
- Windows：双击 [`start_editor.cmd`](start_editor.cmd)
- Linux：运行 [`start_editor.sh`](start_editor.sh)

或者命令行启动。下面这些命令逻辑是通用的，主要差别只是不同系统里 Python 启动器名字不一样：

macOS / Linux：

```bash
git clone https://github.com/TonyNa-code/tony-na-engine.git
cd tony-na-engine
python3 run_editor.py
```

Windows：

```bat
git clone https://github.com/TonyNa-code/tony-na-engine.git
cd tony-na-engine
py -3 run_editor.py
```

如果 Windows 没有 `py` 启动器，也可以改用：

```bat
python run_editor.py
```

## 下载成 App 形式

如果只是想直接下载可运行包，而不是从源码启动：

- `编辑器本体`
  - 可在 GitHub Releases 下载：
    - `macos.tar.gz`
    - `windows.zip`
    - `linux.tar.gz`
  - 当前支持：
    - Windows
    - macOS
    - Linux

- `做完游戏后的成品`
  - 可在编辑器的 `预览导出` 页直接导出：
    - 网页试玩包
    - Windows 桌面包
    - macOS 桌面包
    - Linux 桌面包
    - 原生 Runtime 包（含独立 App 打包脚手架）

当前说明可以简单理解成：

- 想下载“引擎本体 App”，看 Releases 里的编辑器包
- 想下载“游戏成品 App”，在项目里用导出功能生成

说明：

- `Windows / macOS / Linux 桌面包` 当前主要走 NW.js 桌面 Runtime
- `原生 Runtime 包` 是正在推进中的新路线，当前已经覆盖标题页主菜单、基础剧情主链、正式存档/读档、系统菜单设置项、文本历史、自动播放、已读快进、项目字体、玩家档案/自动续玩、基础粒子与镜头演出、可选 PyAV/FFmpeg 音画同步内嵌视频播放、OpenCV 画面兜底、系统播放器桥接兜底，以及第一批资料馆和详情查看能力；导出包内会附带发布前自检报告、崩溃日志能力和 PyInstaller 脚本，可在 macOS / Windows / Linux 目标系统继续打成 Preview App
- `手机端 Runtime` 目前处于实验规划阶段，不走 PyInstaller；更适合先用 WebView / 网页 Runtime 验证触控和音频策略，再决定是否做 Android / iOS 独立原生壳
- Release 附件应优先使用发布工具生成的清单校验；维护者可运行 `python3 tools/release/prepare_preview_release.py --release-tag v0.1.0-preview` 检查 GitHub Release 页面是否漏传或混入旧包
- 发布前建议按 [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) 做一次 Preview 发布体检
- 最后发布闸门可参考 [`RELEASE_P0.md`](RELEASE_P0.md)，GitHub Release 正文草稿可参考 [`docs/github/preview-release-draft.md`](docs/github/preview-release-draft.md)

## 测试

### 测试环境准备

浏览器自动化测试依赖 Playwright。第一次运行前建议先执行：

macOS / Linux：

```bash
cd tony-na-engine
python3 -m pip install -r requirements-dev.txt
python3 -m playwright install chromium
```

Windows：

```bat
cd tony-na-engine
py -3 -m pip install -r requirements-dev.txt
py -3 -m playwright install chromium
```

### 本地检查

前端脚本与关键 Python 文件语法检查：

macOS / Linux：

```bash
cd tony-na-engine
node --check prototype_editor/app.js
node --check export_player_template/player.js
python3 -m py_compile run_editor.py
```

Windows：

```bat
cd tony-na-engine
node --check prototype_editor/app.js
node --check export_player_template/player.js
py -3 -m py_compile run_editor.py
```

### 自动化测试

后端 smoke：

macOS / Linux：

```bash
cd tony-na-engine
python3 -m unittest discover -s tests -p 'test_run_editor_smoke.py' -v
```

Windows：

```bat
cd tony-na-engine
py -3 -m unittest discover -s tests -p "test_run_editor_smoke.py" -v
```

浏览器 Playwright：

macOS / Linux：

```bash
cd tony-na-engine
python3 -m unittest discover -s tests -p 'test_browser_playwright_smoke.py' -v
```

Windows：

```bat
cd tony-na-engine
py -3 -m unittest discover -s tests -p "test_browser_playwright_smoke.py" -v
```

或者直接运行对应系统脚本：

- macOS：[`run_tests.command`](run_tests.command) / [`run_browser_tests.command`](run_browser_tests.command)
- Windows：[`run_tests.cmd`](run_tests.cmd) / [`run_browser_tests.cmd`](run_browser_tests.cmd)
- Linux：[`run_tests.sh`](run_tests.sh) / [`run_browser_tests.sh`](run_browser_tests.sh)

### GitHub Actions

仓库已内置 CI，会在 `push / pull request` 时自动执行：

- Python 语法检查
- 前端脚本语法检查
- 后端 smoke 测试
- Playwright 浏览器烟测

## 发布状态

当前仓库以 **源码可见创作者预览版** 方式维护。

- 源码可直接在本地启动与修改
- 自动化测试已经接通
- GitHub Releases 可用于提供编辑器可运行包
- 导出链和桌面打包链已经具备原型级完整度

维护者相关的发布与签名资料已经挪到 `docs/maintainers/release` 与 `tools/release`，不再作为公开首页的主要内容展示。

## 其他设计文档

如果需要继续查看更早期的引擎规划和数据设计，可参考：

- [`galgame_engine_blueprint.md`](galgame_engine_blueprint.md)
- [`v1_ui_structure.md`](v1_ui_structure.md)
- [`v1_data_format.md`](v1_data_format.md)

## 许可说明

当前仓库采用 **Tony Na Engine Creator License 1.0**：

- [`LICENSE`](LICENSE)

这份许可的核心口径是：

- 允许使用本引擎制作并商业发布游戏
- 允许为了自己的项目修改引擎
- 不允许把引擎本体或修改版引擎当作引擎产品再次商业化出售

因此它不是标准 OSI 意义上的开源协议，而是更接近“源码可见 / source-available”的创作者许可。

## 贡献

欢迎提 Issue、提想法、做测试反馈。

贡献前建议先看：

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
- [`SECURITY.md`](SECURITY.md)

Issue / PR 入口：

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Pull request template](.github/pull_request_template.md)
