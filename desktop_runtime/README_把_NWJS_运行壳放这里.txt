Tony Na Engine · NW.js 本地运行壳投放说明

如果你想在外网受限的环境里也导出真正的 Windows .exe 桌面包，可以把 NW.js Windows x64 运行壳手动放到这里。

支持这几种放法：
1. 直接把压缩包放成：nwjs-v0.105.0-win-x64.zip
2. 解压成目录放成：nwjs-v0.105.0-win-x64
3. 或者用环境变量指定：TONY_NA_NWJS_RUNTIME_DIR / TONY_NA_NWJS_RUNTIME_ZIP

编辑器下次导出 Windows 桌面包时，会先找这里的本地运行壳，再尝试联网下载。
