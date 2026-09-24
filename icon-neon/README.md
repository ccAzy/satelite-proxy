# icon-neon — 霓虹笑脸土星应用图标集（2026-09-22）

39a0002 引入（未单独发版，随工作树迭代至 2026-09-23）、icns 满幅变体与 ico
小尺寸调优均在其任内落地。2026-09-23 应用户要求整体回退「土星环版」
（`icon-saturn/`）后归档于此，留作备用/回退。Windows 侧另有同画风的候选稿
实验管线（`src-tauri/icons/win0-2.png` + `scripts/generate-windows-app-icon.py`）。

- 来源：回退前 git HEAD 工作树原样拷贝（`src-tauri/icons/` + `assets/icon/ic_launcher-web.png`）
- `ic_launcher-web.png` — 源图（`scripts/generate-app-icons.py` 的重采样输入，
  876px 瓦片占画布 ~86% 居中、圆角已内建在 alpha）
- `icon.icns` / `icon.ico` / `icon.png` / `32x32.png` / `128x128.png` / `128x128@2x.png` /
  `Square*.png` / `StoreLogo.png` — 全套产物

如需回退：把本目录产物（除源图与 README）拷回 `src-tauri/icons/`、
源图拷回 `assets/icon/ic_launcher-web.png` 覆盖，再跑
`python scripts/generate-app-icons.py && python scripts/generate-tray-icons.py`
（托盘 saturn 组随源图联动；记得恢复 4 个手工托盘图标，
`git checkout HEAD -- src-tauri/icons/tray/{buddy-off,buddy-on,ghost-on,mark-on}.png`）。

## 原始稿（纯黑底）提取配方

源图来自 ChatGPT 生成稿（1254px 纯黑底，墨绿瓦片 + 霓虹绿发光笑脸土星 +
冰蓝光环），**环辉光会溢出到瓦片外的黑底上**（左下/右侧各一块、最远超边界
~63px），简单「外向内描摹轮廓」会把辉光一起带进 alpha；且瓦片体内部也含
纯黑渐变像素，**不能全域按颜色抠**。正确做法 = **鲁棒圆角矩形拟合**：

1. 阈值 maxchannel>6 取最大连通域补洞；
2. 中带行/列取直边中位数（L77/R1176/T95/B1162）；
3. 只用无辉光窗口的四角弧点做逐角圆拟合（r≈283–294、共享 290）；
4. 按 SDF 渲染 4x 超采样掩膜（外扩 1.5px 吞掉边缘抗锯齿）裁切；
5. 1099×1067 归方 → 876px @86% 居中。

同画风的 `win1.png` / `win2.png`（1254px 纯黑底 RGB 原始候选稿）如需启用，
提取思路同上（或参照 `scripts/generate-windows-app-icon.py` 对已抠图稿的
阴影裁切处理）。
