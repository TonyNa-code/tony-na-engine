# GitHub Release 文案模板（维护者预览版）

公开发布页正文优先使用：

- [`../../github/preview-release-draft.md`](../../github/preview-release-draft.md)

发布前最后闸门优先使用：

- [`../../../RELEASE_P0.md`](../../../RELEASE_P0.md)

生成上传清单、哈希和可复制 Release 正文：

```bash
python3 tools/release/prepare_preview_release.py
```

发布后复查 GitHub Release 页面真实附件是否和本地推荐清单一致：

```bash
python3 tools/release/prepare_preview_release.py --release-tag v0.1.0-preview
```

如果输出里出现 `missing suggested artifacts`、`extra release assets` 或 `size mismatches`，先修正 Release 附件，再把该版本标记为可公开推荐。

如果需要额外扫描旧用户名、真实姓名或其他私密字符串，不要把这些词写进仓库文件；用本地环境变量临时传入：

```bash
TNE_PRIVACY_EXTRA_PATTERNS="old-real-name,old-username" python3 tools/release/prepare_preview_release.py
```

维护者发布时应保持以下口径：

- 使用 `Preview`、`Early Access` 或 `source-available preview`。
- 不把当前版本称为完全稳定商业正式版。
- 如果没有签名 / 公证 / 代码签名，必须在 Release notes 里明确说明。
- 不宣传 Android APK / iOS IPA 正式导出。
- Native Runtime 视频当前说明为系统播放器桥接，不宣传为窗口内嵌视频解码。
