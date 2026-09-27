# iKuuu 的 libui-ng 预构建

官方基线：`43ba1ef553c8993a43a67f1ce6e35983a2660d8c`。只添加发布工作流和最小窗口检查，未引入 kojix2 分支。

- Linux x64 / arm64 使用固定 Ubuntu 20.04 镜像，在构建后检查 GLIBC 符号下限不超过 2.31。
- Windows x64 使用 MSVC，CRT 静态链接进 DLL。检查产物不再依赖 VC 运行库，方便更新器移出主 App 目录运行。
- macOS x64 / arm64 分别使用原生 runner。当前主 App 继续使用 Sparkle，不加载此库。
- 每个构建实际打开包含标签、进度条、文本框和按钮的窗口，再关闭并释放。Linux 在 Xvfb 中运行。
- 普通提交只生成 Actions artifact。只有 `ikuuu-libui-*` 标签发布 Release。
- Action 固定完整 commit SHA。构建仅有只读仓库权限；发布任务才有 Release 和产物证明写入权限。
- 每包仅包含运行库、MIT 许可证、来源与依赖记录。Release 同时提供 SHA256SUMS 和 GitHub 构建证明。

应用仓库固定 Release 和每个 ZIP 的 SHA-256，不读取 latest，不在应用开发环境安装 Meson/Ninja。版本升级须重新审查源码差异，再更新固定摘要。

构建证明核验：`gh attestation verify libui-windows-x64.zip --repo iKuuu-org/libui-ng`。

窗口检查不等于完整 UI 测试。应用侧仍须在客体执行安装、错误提示、退出和重启测试。
