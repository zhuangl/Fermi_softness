# Desktop application / 桌面应用

[Documentation index / 文档目录](index.md)

## macOS — English

After installing the GUI extra, create the application icon and open Studio:

```sh
fermi-softness install-app --open
```

From a source checkout, you can instead double-click
**Install Fermi Softness Studio.command**. This prepares `.venv`, installs the
GUI dependencies, creates the application entry and opens it. Python 3.10 or
newer must already be available; dependency installation may need the network.

The installer places **Fermi Softness Studio.app** in `/Applications` when that
folder is writable, otherwise in `~/Applications`. Use `--directory` to choose:

```sh
fermi-softness install-app --directory ~/Applications --open
```

Open the app in Finder's Applications folder or search for **Fermi Softness
Studio** with Spotlight (Command-Space). To keep it in the Dock, open it, then
right-click its Dock icon and choose **Options → Keep in Dock**. The app initially
loads the Pt₃Y example; use the Data tab to open your own calculation.

The application entry uses the Python environment that ran `install-app`; it
does not copy a second Python runtime. Keep that environment in place. After
moving or upgrading it, run `install-app` again. Updating an entry made by this
installer is supported; an unrelated application at the same path is preserved.
Startup messages are recorded in `~/Library/Logs/Fermi Softness Studio/studio.log`.

The Pt₃Y icon is a transparent branding cutout derived from the author's selected
Studio screenshot. Its [master PNG](../src/fermi_softness/assets/fermi-softness.png),
[macOS ICNS](../src/fermi_softness/assets/fermi-softness.icns) and
[generation record](../src/fermi_softness/assets/icon-provenance.json) are included.

The `install-app` command currently targets macOS. On other systems, start the
viewer with `fermi-softness gui` as described in the user guide.

## macOS — 中文

安装 GUI 依赖后，运行一次下面的命令，即可生成应用图标并启动：

```sh
fermi-softness install-app --open
```

使用源码目录时，也可以直接双击 **Install Fermi Softness Studio.command**。
它会准备 `.venv`、安装 GUI 依赖、创建应用入口并打开软件。电脑需要先有 Python 3.10
或更新版本，安装依赖时可能需要联网。

安装器优先将 **Fermi Softness Studio.app** 放入可写的 `/Applications`，否则放入
个人的 `~/Applications`。也可用 `--directory` 指定目录：

```sh
fermi-softness install-app --directory ~/Applications --open
```

以后在 Finder 的“应用程序”中双击即可，或者按 **Command + 空格**，搜索
**Fermi Softness Studio** 后回车。打开后，右键点击 Dock 中的图标，选择
**选项 → 在程序坞中保留**，即可固定入口。启动时展示 Pt₃Y 示例，自己的数据可在 Data 页打开。

应用入口调用安装时的 Python 环境，不另外复制一套运行环境。请保留该环境；移动或
升级后重新执行 `install-app` 即可。安装器可以更新自己创建的入口，不覆盖同名的其他
应用。启动日志保存在 `~/Library/Logs/Fermi Softness Studio/studio.log`。

图标由作者选定截图中的 Pt₃Y 三维图案制作，采用透明背景。[原始 PNG](../src/fermi_softness/assets/fermi-softness.png)、
[macOS 图标](../src/fermi_softness/assets/fermi-softness.icns)和
[生成记录](../src/fermi_softness/assets/icon-provenance.json)均随软件提供。

`install-app` 目前用于 macOS，其他系统按使用手册运行 `fermi-softness gui`。

## Implementation references

- [Apple: macOS application bundle structure](https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html)
- [Qt: application identity and icons](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QGuiApplication.html)
