# icon-legacy — v1.0.37 及之前的旧版应用图标

土星环新图标（ec487bd，v1.0.38 起生效）替换下来的完整旧版应用图标集，留作备用/回退。

- 来源：`git show v1.0.37:<原路径>`，与 v1.0.37 发布版逐字节一致
- `ic_launcher-web.png` — 源图（原 `assets/icon/ic_launcher-web.png`，图标生成的重采样源）
- `icon.icns` / `icon.ico` / `icon.png` / `32x32.png` / `128x128.png` / `128x128@2x.png` /
  `Square*.png` / `StoreLogo.png` — 原位于 `src-tauri/icons/` 的全套产物

如需回退正式应用图标：把本目录产物（除源图与 README）拷回 `src-tauri/icons/` 覆盖即可；
仅 macOS 注意 icns 旧版为透明边距设计（86% 内容），macOS 26 Tahoe 下会显示浅色底板——
这正是当初换满幅变体的原因（见 AGENTS.md §1 图标生成说明）。
