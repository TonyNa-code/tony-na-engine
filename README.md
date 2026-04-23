<p align="center">
  <img src="docs/github/tn-engine-hero.svg" alt="Tony Na Engine hero" width="100%" />
</p>

<h1 align="center">Tony Na Engine</h1>

<p align="center">
  一套面向视觉小说 / Galgame 创作者的可视化引擎原型。<br />
  目标是让“不懂编程的人”，也能用上传素材、输入台词、点按钮和可视化编辑的方式完成游戏开发。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-open%20source%20preview-3fb7ff?style=for-the-badge" alt="Status: Open Source Preview" />
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-0e1628?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/tests-smoke%20%2B%20playwright-1fc98b?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/license-MIT-f5c451?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#当前已经有的核心能力">核心能力</a> ·
  <a href="#免费预览版分发">预览版分发</a> ·
  <a href="#商业签名--公证">商业签名 / 公证</a> ·
  <a href="CONTRIBUTING.md">参与贡献</a>
</p>

---

## 项目定位

Tony Na Engine 当前更适合这样理解：

- `开源创作者预览版`
- `Early Access / Preview`
- `适合独立开发者、同人作者、内部测试成员先拿来试做项目`

它已经具备非常丰富的编辑器能力和导出能力，但我也想诚实说明：

- 自动化测试已经比较完整
- 但完整人工逐按钮长流程点测还没有全部做完
- 所以现在更推荐把它当成一个**很强的开源预览版**，而不是“完全稳定的正式商业版”

## 当前已经有的核心能力

- 可视化剧情编辑器
- 项目中心与空白新建项目
- 新手模式 / 高级模式分层
- 角色、素材、台词台本、配音工作流
- 项目巡检、一键发布前修复顺序、自动回归试玩路线测试
- 正式存档 / 读档、系统菜单
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

最简单的方式：

- 双击 [`start_editor.command`](start_editor.command)

或者命令行启动：

```bash
cd "/Users/na/Game Engine"
python3 run_editor.py
```

## 测试

后端 smoke：

```bash
cd "/Users/na/Game Engine"
python3 -m unittest discover -s tests -p 'test_run_editor_smoke.py' -v
```

浏览器 Playwright：

```bash
cd "/Users/na/Game Engine"
python3 -m unittest discover -s tests -p 'test_browser_playwright_smoke.py' -v
```

或者直接双击：

- [`run_tests.command`](run_tests.command)
- [`run_browser_tests.command`](run_browser_tests.command)

## 免费预览版分发

如果你现在还没有商业签名证书，也可以先把它当成：

- `Preview`
- `内测版`
- `开源创作者预览版`

直接通过 GitHub Releases 或压缩包分发。

建议先看：

- [`README_预览版发布说明.md`](README_%E9%A2%84%E8%A7%88%E7%89%88%E5%8F%91%E5%B8%83%E8%AF%B4%E6%98%8E.md)
- [`RELEASE_预览版文案模板.md`](RELEASE_%E9%A2%84%E8%A7%88%E7%89%88%E6%96%87%E6%A1%88%E6%A8%A1%E6%9D%BF.md)

## 商业签名 / 公证

如果你后面要做商业分发，可以继续看：

- [`README_商业签名与公证操作指南.md`](README_%E5%95%86%E4%B8%9A%E7%AD%BE%E5%90%8D%E4%B8%8E%E5%85%AC%E8%AF%81%E6%93%8D%E4%BD%9C%E6%8C%87%E5%8D%97.md)
- [`editor_signing.env.example`](editor_signing.env.example)
- [`check_editor_signing_readiness.py`](check_editor_signing_readiness.py)
- [`run_signing_readiness.command`](run_signing_readiness.command)

## 其他设计文档

如果你想继续看更早期的引擎规划和数据设计：

- [`galgame_engine_blueprint.md`](galgame_engine_blueprint.md)
- [`v1_ui_structure.md`](v1_ui_structure.md)
- [`v1_data_format.md`](v1_data_format.md)

## 开源许可

当前先按 **MIT License** 整理：

- [`LICENSE`](LICENSE)

如果后面你更想换成 `Apache-2.0`、`GPL`、或者“源码可见但禁止商用”的自定义协议，也可以继续调整。

## 贡献

欢迎提 Issue、提想法、做测试反馈。

先看：

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)

Issue / PR 模板也已经准备好了：

- [Bug report](.github/ISSUE_TEMPLATE/bug_report.md)
- [Feature request](.github/ISSUE_TEMPLATE/feature_request.md)
- [Pull request template](.github/pull_request_template.md)
