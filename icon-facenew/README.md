# icon-facenew — 笑脸土星应用图标集（v1.0.40）

0196983 引入、v1.0.40 发布的「facenew 笑脸土星」深色圆角瓦片应用图标全套
（源图为用户手稿 facenew.png，1024px 瓦片占画布 ~86% 居中），
被「霓虹笑脸土星」新图标（ChatGPT 生成稿）替换后归档于此，留作备用/回退。
同类归档：`icon-saturn/`（v1.0.38–39 土星环版）、`icon-legacy/`（v1.0.37 及之前旧版）。

- 来源：v1.0.40 工作树原样拷贝（`src-tauri/icons/` + `assets/icon/ic_launcher-web.png`）
- `ic_launcher-web.png` — 源图（`scripts/generate-app-icons.py` 的重采样输入）
- `icon.icns` / `icon.ico` / `icon.png` / `32x32.png` / `128x128.png` / `128x128@2x.png` /
  `Square*.png` / `StoreLogo.png` — 全套产物

如需回退：把本目录产物（除源图与 README）拷回 `src-tauri/icons/`、
源图拷回 `assets/icon/ic_launcher-web.png` 覆盖，再跑
`python scripts/generate-app-icons.py && python scripts/generate-tray-icons.py`
（托盘 saturn 组随源图联动，注意恢复 4 个手工图标，见托盘脚本头注释）。
