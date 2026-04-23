# Tony Na Engine 编辑器商业签名与公证操作指南

这份说明给你最后做正式发布时用。现在编辑器导出链已经接通了：

- `macOS`：`.app`、`.pkg`、签名、公证、staple
- `Windows`：Inno Setup 安装器 `.exe`、安装器签名、时间戳
- `Linux`：当前以安装脚本和桌面入口为主，暂时不走代码签名

## 1. 先准备发行配置

先确认根目录下这份配置已经填好：

- [`editor_distribution.json`](editor_distribution.json)

至少把这些改成你正式要发布的内容：

- `productName`
- `bundleIdentifier`
- `publisherName`
- `companyName`
- `website`
- `supportEmail`
- `copyright`

## 2. 准备本地环境变量

再把下面这份示例复制成你自己的本地环境变量文件：

- [`editor_signing.env.example`](editor_signing.env.example)

### macOS 需要

- `TONY_NA_EDITOR_MAC_APP_IDENTITY`
- `TONY_NA_EDITOR_MAC_INSTALLER_IDENTITY`
- `TONY_NA_EDITOR_MAC_NOTARY_PROFILE`

建议先在本机确认这些命令可用：

```bash
codesign --version
productsign --help
xcrun notarytool --help
```

### Windows 需要

- `TONY_NA_EDITOR_WINDOWS_ISCC`
- `TONY_NA_EDITOR_WINDOWS_SIGNTOOL`

再从下面三种证书方式里任选一种：

1. 证书主题名
   - `TONY_NA_EDITOR_WINDOWS_CERT_SUBJECT`
2. 证书指纹
   - `TONY_NA_EDITOR_WINDOWS_CERT_THUMBPRINT`
3. PFX 文件
   - `TONY_NA_EDITOR_WINDOWS_PFX_PATH`
   - `TONY_NA_EDITOR_WINDOWS_PFX_PASSWORD`

可选：

- `TONY_NA_EDITOR_WINDOWS_TIMESTAMP_URL`

如果你要在非 Windows 环境跨平台触发 Windows 编译/签名，还可以补：

- `TONY_NA_EDITOR_WINDOWS_ISCC_RUNNER`
- `TONY_NA_EDITOR_WINDOWS_SIGNTOOL_RUNNER`

## 3. macOS 真签名与公证建议顺序

1. 先准备好 Apple Developer 证书和 notary profile
2. 确认上面的 3 个 `TONY_NA_EDITOR_MAC_*` 环境变量都能取到
3. 在编辑器里执行：
   - `导出编辑器桌面包`
   - 或 `导出三系统编辑器套装`
4. 导出结果里重点确认：
   - `签名状态`
   - `安装包`
   - `商业发布说明`
5. 如果状态变成：
   - `已公证并可商业分发`
   说明这条链已经完全跑通

## 4. Windows 真签名建议顺序

1. 在 Windows 真机上安装 Inno Setup
2. 确认可用的 `signtool.exe`
3. 准备好真实代码签名证书
4. 配好：
   - `TONY_NA_EDITOR_WINDOWS_ISCC`
   - `TONY_NA_EDITOR_WINDOWS_SIGNTOOL`
   - 以及主题名 / 指纹 / PFX 三选一
5. 在编辑器里执行：
   - `导出编辑器桌面包`
   - 或 `导出三系统编辑器套装`
6. 导出结果里重点确认：
   - `Windows 安装器编译：已编译 Windows 安装器`
   - `Windows 安装器签名：已签名并加时间戳`

## 5. 导出后你应该检查什么

### macOS

- `.app` 是否能打开
- `.pkg` 是否能安装
- 系统是否不再提示“来源不明”
- 安装后能正常启动编辑器

### Windows

- `.exe` 安装器是否能启动
- 安装后桌面或开始菜单入口是否正常
- 安装后首次打开是否无签名警告
- 编辑器能否正常创建项目、导出项目

## 6. 什么时候才算真正商业版

至少满足这几条再往外发：

- `mac` 已完成签名 + 公证
- `Windows` 已完成安装器签名 + 时间戳
- 关键导出链、创建项目链、启动链都实机走查过
- 你已经留过一份正式发行配置快照

## 7. 现在这套链已经做到哪里

当前工程已经做到：

- 导出页能直接显示签名/公证状态
- 自动化测试已经覆盖商业打包主链
- `mac / Windows` 真签名与公证参数都已经接入

还差你自己提供的只有：

- 真实开发者证书
- 真实签名身份
- 最后一轮真机安装与启动走查
