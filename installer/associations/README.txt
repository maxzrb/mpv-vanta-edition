MPV Vanta Edition 文件关联入口

推荐入口：current-user\
- register-multi.bat：注册 mpv 多实例音视频关联
- unregister-multi.bat：取消 mpv 多实例关联
- register-single.bat：注册 mpv-single 单实例音视频关联
- unregister-single.bat：取消 mpv-single 单实例关联

推荐入口只修改当前用户注册表（HKCU），不需要管理员权限或 UAC。
多实例和单实例身份完全独立，可分别注册或取消。
installer\ 根目录另有四个同名 BAT 镜像，用户可直接双击；镜像只负责转发，不复制注册逻辑。
icons\mpv-document.ico 是新版和旧关联迁移共用的稳定文档图标。
注册时会修复确属当前安装目录的旧 io.mpv.* 图标路径和打开命令，但不会强改 Windows 默认应用选择。

旧版兜底：legacy-system-wide\
- 保留原有 mpv-install/uninstall*.bat 及其图标资源。
- 写入系统级注册表（HKLM），需要管理员权限。
- 主要用于兼容或清理旧版系统级关联，不作为新版默认方案。
