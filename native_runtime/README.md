# 原生 Runtime 包

这是 Tony Na Engine 在“先原生化 Runtime，编辑器先保留网页技术”路线上的第一阶段预览。

当前目标不是一次性替换现有网页播放器，而是先把最核心的剧情播放主链迁到真正不依赖 HTML 的桌面运行时里。

## 当前已覆盖

- 背景切换
- 角色显示 / 隐藏
- 台词 / 旁白
- 选项
- 跳转 / 条件分支
- 基础变量修改
- BGM / SFX / 语音播放
- 第一版正式存档 / 快速存档
- 可视化存档 / 读档面板
- 基础系统菜单
- 主题 / 显示模式 / 文字速度 / 四路音量设置
- 玩家档案 / 自动续玩记录
- 原生标题页 / 主菜单入口
- 多馆标签页资料馆
- 章节回放 / 音乐鉴赏 / CG 回想
- 地点图鉴 / 角色图鉴 / 结局回放 / 成就馆
- CG / 地点 / 角色 / 旁白 / 关系 / 成就详情查看页
- 项目级正式存档位数量
- 项目级文本框样式基础同步
- 项目级成品 UI 皮肤颜色 / 标题资源同步
- 项目级 UI 九宫格绘制、存档卡片皮肤与按钮多状态贴图
- 基础粒子特效表现
- 基础镜头 / 闪屏 / 淡入淡出 / 滤镜 / 景深演出
- 视频卡片的影院式原生预览卡 / 可选 OpenCV 帧预览 / 系统播放器桥接
- PyInstaller 独立 App 打包脚手架

## Preview 路线图

原生 Runtime 已经可以承担第一版桌面预览和小型项目试玩导出；后续增强会按“先稳定主链，再补高级演出”的顺序推进：

| 模块 | 当前状态 | 后续增强方向 |
| --- | --- | --- |
| 剧情主链 | 已支持背景、角色、台词、选项、跳转、条件与变量 | 持续对齐网页 Runtime 的高级演出边角场景 |
| 存档与系统菜单 | 已支持正式存档、快速存档、主题、显示模式、文字速度和四路音量 | 增加更细的按键映射、辅助功能和项目级菜单扩展 |
| 项目 UI 皮肤 | 已在 Pygame 中绘制基础颜色、标题资源、面板九宫格、存档卡片和按钮多状态贴图 | 后续补 UI Kit 部件库、皮肤包导入导出和更多控件级绑定 |
| 资料馆 / 回想馆 | 已支持章节、音乐、CG、地点、角色、结局、成就及详情页 | 增加高级筛选、排序、专属转场和更多馆内互动 |
| 粒子与镜头 | 已支持基础粒子、镜头、闪屏、淡入淡出、滤镜和景深 | 补齐组合层、更多物理参数和复杂粒子表现 |
| 视频卡片 | 当前使用影院式原生预览卡，可选 OpenCV 显示剪辑起点帧，并通过系统播放器桥接 OP / ED / PV | 规划完整窗口内嵌播放、时间轴裁切、音画同步和自动播完检测 |

## 启动要求

- Python 3.10+
- `pygame-ce`

安装命令：

```bash
python3 -m pip install -r requirements.txt
```

如果是在编辑器导出的原生 Runtime 包里运行，依赖文件会被改名为：

```bash
python3 -m pip install -r requirements-native-runtime.txt
```

## 快速验证

```bash
python3 runtime_player.py --validate-bundle .
```

## 发布前自检

不启动窗口，输出发布前诊断报告。这个检查会覆盖入口场景、缺失素材、素材格式风险、大文件风险、存档位数量、成品 UI 皮肤素材引用等：

```bash
python3 runtime_player.py --release-check .
```

## 视频后端状态

原生 Runtime 默认使用“影院式预览卡 + 系统播放器桥接”，包体轻、三平台风险低，适合 Preview 版验证 OP / ED / PV。

查看当前机器的视频后端能力：

```bash
python3 runtime_player.py --describe-video-backends .
```

如果想检查当前导出包是否能生成窗口内视频帧预览，可以运行：

```bash
python3 runtime_player.py --probe-video-preview .
```

如果想启用窗口内画面帧预览，可以额外安装可选依赖：

```bash
python3 -m pip install -r requirements-native-runtime-video.txt
```

安装后，视频卡片会优先尝试读取剪辑起点附近的一帧作为窗口内预览图；如果读取失败，会自动回落到默认的影院式桥接卡片，不影响玩家按 `V` 调用系统播放器。`--probe-video-preview` 会输出每个视频的探针状态，方便发布前确认是缺依赖、缺 pygame、文件缺失还是编码无法读取。

这条路线目前仍是实验性候选：OpenCV 可以帮助解码画面帧，但不负责音频播放和音画同步；正式商业级内嵌 OP / ED 仍需要继续评估 FFmpeg/PyAV/平台原生播放器等方案。

## 快速启动

```bash
python3 runtime_player.py game_data.json
```

## 打包成独立 App

导出的原生 Runtime 包已经包含 PyInstaller 打包入口。创作者在目标系统上执行对应脚本，就可以把 `runtime_player.py + game_data.json + 素材` 打进 `native_app_dist/`，同时生成 `native_app_package_manifest.json` 和一个用于上传到 Release 的 Preview zip：

- macOS：双击 `打包原生Runtime应用.command`
- Linux：运行 `./build_native_runtime_app.sh`
- Windows：双击 `build_native_runtime_app.bat`

也可以手动执行：

```bash
python3 -m pip install -r requirements.txt -r requirements-build.txt
python3 build_native_runtime_app.py --mode onedir .
```

打包清单会记录发布前自检、视频后端状态和视频帧预览探针结果，方便排查目标系统上的视频/素材问题。

在编辑器导出的原生 Runtime 包中，对应命令是：

```bash
python3 -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt
python3 build_native_runtime_app.py --mode onedir .
```

打包脚本默认会先运行 `python3 runtime_player.py --release-check .`。如果自检发现错误，会先停止打包，避免把明显缺素材或入口错误的版本发出去。

如果想生成单文件可执行程序：

```bash
python3 build_native_runtime_app.py --mode onefile .
```

如果想覆盖应用名和 macOS Bundle Identifier：

```bash
python3 build_native_runtime_app.py --mode onedir --app-name YourGame --bundle-id com.tonyna.yourgame .
```

macOS 的 `onedir` 模式会在 `native_app_dist/` 下生成 `.app` 和一个同名运行目录。优先把 `.app` 作为本机测试对象；正式分发前再做签名、公证和完整点测。

## 三系统分发状态

PyInstaller 通常需要在目标系统本机打包，不建议期待从 macOS 直接交叉编译 Windows / Linux：

- macOS：生成 `.app`，未签名/未公证时可作为 Preview 下载测试，正式公开分发需要 Developer ID 签名和 notarization。
- Windows：在 Windows 上运行 `build_native_runtime_app.bat`，会生成 `.exe` 或 onedir 目录；未签名时 SmartScreen 可能提示未知发布者。
- Linux：在 Linux 上运行 `./build_native_runtime_app.sh`，会生成 Linux 可执行目录；后续可继续封装 AppImage、deb/rpm 或 Flatpak。

## 手机端状态

手机端不走 PyInstaller，当前不能直接由这个脚本生成 Android APK 或 iOS IPA。可行路线分三档：

- 近期可试：继续使用网页 Runtime / WebView 包装，先验证手机触控、横竖屏、音频策略和存档。
- 中期路线：做独立 Android Runtime，把 `game_data.json` 映射到 Kivy / Python-for-Android 或 Godot 这类移动壳。
- 长期路线：做 iOS / Android 双端原生 Runtime，共用项目格式，但渲染、音频、存档和商店发布链要单独实现。

因此手机端现在应标记为实验规划，不建议和桌面原生 Runtime 混在同一个发布承诺里。

Runtime 启动失败时，会在用户目录写入错误日志：

```text
~/.tony-na-engine/native-runtime-logs/
```

打包脚本不会替你做平台签名、公证或杀毒误报处理；正式公开发布前，仍建议在对应系统上做一次完整人工点测。

## 第一版存档 / 读档

当前已经支持：

- `F5`：快速存档
- `F8 / F9`：读入快速存档
- `F6`：打开正式存档面板
- `F7`：打开读档面板
- `F11`：切换窗口 / 全屏
- `F1 / Tab`：打开系统菜单
- 系统菜单里的 `体验设置`：主题 / 显示模式 / 文字速度 / 四路音量
- 系统菜单里的 `玩家档案`：本地游玩次数、累计时长、续玩次数
- 系统菜单里的 `续玩记录`：读取或清除自动续玩位置
- 系统菜单里的 `资料馆`：支持章节 / 音乐 / CG / 地点 / 角色 / 结局 / 成就标签切换
- 资料馆里 `← / →`：切换馆页
- `Ctrl + 1 / 2 / 3`：写入前 3 个正式存档位
- `Ctrl + Shift + 1 / 2 / 3`：读入前 3 个正式存档位
- `Esc`：关闭面板 / 退出预览

存档文件会写到用户目录下：

```text
~/.tony-na-engine/native-runtime-saves/
```

玩家档案和续玩记录也会写到用户目录下：

```text
~/.tony-na-engine/native-runtime-profiles/
~/.tony-na-engine/native-runtime-autoresume/
```

## 存档自检

不启动窗口，只验证存档写入和读回：

```bash
python3 runtime_player.py --exercise-save-load .
```

## 存档面板摘要自检

不启动窗口，输出当前项目的正式存档分页摘要：

```bash
python3 runtime_player.py --describe-save-dialog .
```

## 标题页自检

不启动窗口，输出原生标题页的菜单、Logo、续玩与存档摘要：

```bash
python3 runtime_player.py --describe-title-screen .
```

## 设置自检

不启动窗口，验证主题 / 显示模式 / 文字速度 / 音量设置的写入与读回：

```bash
python3 runtime_player.py --exercise-settings .
```

## 资料馆进度自检

不启动窗口，验证章节 / 音乐 / CG / 地点 / 角色 / 结局资料馆进度的写入与读回：

```bash
python3 runtime_player.py --exercise-archives .
```

## 粒子自检

不启动窗口，验证当前项目里的粒子卡能否生成原生 Runtime 可播放条目：

```bash
python3 runtime_player.py --exercise-particles .
```

## 高级演出自检

不启动窗口，验证镜头 / 闪屏 / 淡入淡出 / 滤镜 / 景深这类演出卡能否被原生 Runtime 规范化：

```bash
python3 runtime_player.py --exercise-visual-effects .
```

## 视频桥接自检

原生 Runtime Preview 的完整播放仍通过系统默认视频播放器桥接；如果安装了可选 OpenCV 依赖，视频卡片会额外尝试显示一帧窗口内预览图。这个命令可检查导出包里有哪些视频、是否存在、被哪些视频卡引用，以及当前系统是否能唤起默认播放器：

```bash
python3 runtime_player.py --describe-video-bridge .
```

如果项目依赖 OP / ED / PV，正式发布前仍建议同时导出网页包或 NW.js 桌面包实机确认，因为那两条链路可以直接在 Runtime 内播放视频。

## 玩家档案自检

不启动窗口，验证玩家档案和自动续玩记录的写入、读回与清除：

```bash
python3 runtime_player.py --exercise-profile .
```
