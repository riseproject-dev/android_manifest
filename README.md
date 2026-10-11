# RISE Android 17 BSP

Android 17 for SpacemiT K3 Pico-ITX and Alibaba A210 EVB. These are the two
RISE board products. Each board has independent kernel and bootloader build
workspaces. Android consumes their outputs as prebuilts; an Android-only
checkout already contains those prebuilts.

## RISE repositories and branches

All BSP repositories below are private. GitHub access to `riseproject-dev`
and an authorized SSH key are required. These instructions use the RISE
repositories directly; AOSP dependencies retain their Google remotes.
All BSP forks, build scripts, board prebuilts and RISC-V WebView changes must
be available in RISE. The delivered manifests and build recipes require no
BayLibre repository; original commit history and authorship are preserved.

The prepared imports must be published on the listed branches before a
fresh network sync can succeed. Local builds made before publication use
cached source commits and local imports; they do not prove those branches
are already available from the RISE remotes.

| Repository | Delivery branch | Checkout path |
| --- | --- | --- |
| [android_manifest](https://github.com/riseproject-dev/android_manifest) | `android-17` | `manifest` |
| [android_device_rise](https://github.com/riseproject-dev/android_device_rise) | `android-17` | `aosp/device/rise` |
| [android_vendor_rise](https://github.com/riseproject-dev/android_vendor_rise) | `android-17` | `aosp/vendor/rise` |
| [android_generic_hal](https://github.com/riseproject-dev/android_generic_hal) | `android-17` | `aosp/hardware/generic` |
| [android_hardware_realtek](https://github.com/riseproject-dev/android_hardware_realtek) | `android-17` | `aosp/hardware/realtek` |
| [android_external_drm_hwcomposer](https://github.com/riseproject-dev/android_external_drm_hwcomposer) | `android-17` | `aosp/external/drm_hwcomposer` |
| [android_external_minigbm](https://github.com/riseproject-dev/android_external_minigbm) | `android-17` | `aosp/external/minigbm` |
| [android_build_soong](https://github.com/riseproject-dev/android_build_soong) | `android-17` | `aosp/build/soong` |
| [android_build_blueprint](https://github.com/riseproject-dev/android_build_blueprint) | `android-17` | `aosp/build/blueprint` |
| [android_kernel_common](https://github.com/riseproject-dev/android_kernel_common) | `android-mainline-spacemit / android-mainline-alibaba` | `kernel_*/common` |
| [android_kernel_device](https://github.com/riseproject-dev/android_kernel_device) | `android-17` | `kernel_*/devices/rise` |
| [android_bootloader_build](https://github.com/riseproject-dev/android_bootloader_build) | `spacemit-android-17 / alibaba-android-17` | `bootloaders_*/build-bootloaders` |
| [u-boot](https://github.com/riseproject-dev/u-boot) | `v2026.07-k3 / v2024.10-a210` | `bootloaders_*/u-boot` |
| [opensbi](https://github.com/riseproject-dev/opensbi) | `v1.8-k3 / v1.5-a210` | `bootloaders_*/opensbi` |
| [mesa](https://github.com/riseproject-dev/mesa) | `android-17-imagination` | `mesa` |
| [android-webview-riscv64](https://github.com/riseproject-dev/android-webview-riscv64) | `android-17` | `android-webview-riscv64` |

The manifest remote is:

```xml
<remote name="rise" fetch="ssh://git@github.com/riseproject-dev/" />
```

`repo` appends the project name to this prefix. For example,
`android_device_rise` resolves to
`ssh://git@github.com/riseproject-dev/android_device_rise`.

The HWC fork preserves the pinned Android source history and the original
authors and signoffs of the preferred-mode and external sRGB fixes.
The client must create `android_external_drm_hwcomposer` before publication.
The prepared source uses Android 17 interfaces; complete Android builds
and display tests remain required on both boards.

## Host and workspace

Use Linux x86_64 and Bash. Follow the
[AOSP host requirements](https://source.android.com/docs/setup/start/requirements)
for packages, RAM and disk space, and install `repo` and Git LFS. Android
provides its own Java and compiler prebuilts. Budget additional disk space
for the two Android output directories and the independent source trees.

Bootloader builds also need `make`, `bison`, `flex`, `dtc`, Python 3,
`shyaml`, `tar`, and `wget` or `curl`. Their scripts obtain the cross-toolchains:
SpacemiT v1.2.4 for K3 and kernel.org GCC 14.2.0 for A210. Hardware checks use
`adb` and `fastboot`.

Create a parent directory and run the following from it. Every command below
uses its absolute path, so changing directory does not change destinations.

```sh
export RISE_WORKSPACE="$PWD"
```
```text
rise/
  aosp/                       Android 17, both products
  kernel_k3/                  K3 kernel and Kleaf dependencies
  kernel_alibaba/             A210 kernel and Kleaf dependencies
  bootloaders_k3/             K3 OpenSBI, U-Boot and build scripts
  bootloaders_alibaba/        A210 OpenSBI, U-Boot and build scripts
  mesa/                       Shared Mesa source, board-specific builds
  android-webview-riscv64/    Chromium/WebView build recipe
```

| Manifest | Workspace | Source selection |
| --- | --- | --- |
| [default.xml](default.xml) | `aosp` | complete `android17-release` plus RISE overrides |
| [kernel-spacemit.xml](kernel-spacemit.xml) | `kernel_k3` | K3 common branch plus pinned Google dependencies |
| [kernel-alibaba.xml](kernel-alibaba.xml) | `kernel_alibaba` | A210 common branch plus pinned Google dependencies |
| [bootloader-spacemit.xml](bootloader-spacemit.xml) | `bootloaders_k3` | K3 OpenSBI, U-Boot and orchestration |
| [bootloader-alibaba.xml](bootloader-alibaba.xml) | `bootloaders_alibaba` | A210 OpenSBI, U-Boot and orchestration |

## Android sync and builds

Initialize the complete Android checkout:

```sh
mkdir -p "$RISE_WORKSPACE/aosp" && cd "$RISE_WORKSPACE/aosp" && repo init -u git@github.com:riseproject-dev/android_manifest.git -b android-17 -m default.xml && repo sync -j24
```


Accept the `device/rise/post-sync.py` hook when `repo` requests approval.
It installs Git LFS locally for the device repo and materializes the APK
and kernel payloads. A Git LFS pointer is not a usable APK or kernel image.
Fix reported LFS errors before building.

| Board | Lunch target | Output with the commands below |
| --- | --- | --- |
| K3 Pico-ITX | `aosp_k3_pico_itx-trunk_staging-userdebug` | `aosp/out-k3/target/product/k3` |
| A210 EVB | `aosp_a210_evb-trunk_staging-userdebug` | `aosp/out-a210/target/product/a210` |

Build K3:

```sh
cd "$RISE_WORKSPACE/aosp" && export OUT_DIR=out-k3 && source build/envsetup.sh && lunch aosp_k3_pico_itx-trunk_staging-userdebug && m -j24
```

Build A210:

```sh
cd "$RISE_WORKSPACE/aosp" && export OUT_DIR=out-a210 && source build/envsetup.sh && lunch aosp_a210_evb-trunk_staging-userdebug && m -j24
```


`out-k3` and `out-a210` keep each product's outputs separate. `-j24` controls
sync concurrency; the build commands use `-j24`. Adjust build concurrency to
the host's available memory. Re-run the relevant Android build after any
kernel, bootloader, Mesa or WebView prebuilt replacement.

## Rebuild the kernels

Each manifest contains all Kleaf, compiler, tools and library dependencies.
The kernel device repo is shared, but the common branches and the selected
`device.bazelrc` are board-specific. No external kernel workspace is needed.

K3 checkout:

```sh
mkdir -p "$RISE_WORKSPACE/kernel_k3" && cd "$RISE_WORKSPACE/kernel_k3" && repo init -u git@github.com:riseproject-dev/android_manifest.git -b android-17 -m kernel-spacemit.xml && repo sync -j24
```

A210 checkout:

```sh
mkdir -p "$RISE_WORKSPACE/kernel_alibaba" && cd "$RISE_WORKSPACE/kernel_alibaba" && repo init -u git@github.com:riseproject-dev/android_manifest.git -b android-17 -m kernel-alibaba.xml && repo sync -j24
```


Build and export the K3 distribution:

```sh
cd "$RISE_WORKSPACE/kernel_k3" && KERNEL_DIST="$RISE_WORKSPACE/aosp/device/rise/spacemit/kernel/mainline" && mkdir -p "$RISE_WORKSPACE/artifact-backups" && if [ -d "$KERNEL_DIST" ]; then mv "$KERNEL_DIST" "$RISE_WORKSPACE/artifact-backups/k3-mainline-$(date +%Y%m%dT%H%M%S)-$$"; fi && tools/bazel run --config=fast //devices/rise/spacemit/spacemit_soc:spacemit_k3_dist -- --destdir="$KERNEL_DIST"
```

Build and export the A210 distribution:

```sh
cd "$RISE_WORKSPACE/kernel_alibaba" && KERNEL_DIST="$RISE_WORKSPACE/aosp/device/rise/alibaba/kernel/mainline" && mkdir -p "$RISE_WORKSPACE/artifact-backups" && if [ -d "$KERNEL_DIST" ]; then mv "$KERNEL_DIST" "$RISE_WORKSPACE/artifact-backups/a210-mainline-$(date +%Y%m%dT%H%M%S)-$$"; fi && tools/bazel run --config=fast //devices/rise/alibaba/a210:zhihe_a210_dist -- --destdir="$KERNEL_DIST"
```


| Board | Android prebuilt directory | Board DTB |
| --- | --- | --- |
| K3 | `device/rise/spacemit/kernel/mainline` | `k3-pico-itx.dtb` |
| A210 | `device/rise/alibaba/kernel/mainline` | `a210-evb.dtb` |

The dist target exports the kernel `Image`, modules, DTB and its build
metadata. Kernel updates must keep the Image and modules from the same
build together. The K3 target exports only the K3 board DTB.
The commands preserve the previous prebuilt directory under
`$RISE_WORKSPACE/artifact-backups/` and export the complete new distribution
to Android. Rebuild Android after replacing the kernel and modules.

## Rebuild the bootloaders

Each bootloader checkout contains its own build scripts, OpenSBI and U-Boot.
The two branches of `android_bootloader_build` contain their respective
board configurations.

K3 checkout:

```sh
mkdir -p "$RISE_WORKSPACE/bootloaders_k3" && cd "$RISE_WORKSPACE/bootloaders_k3" && repo init -u git@github.com:riseproject-dev/android_manifest.git -b android-17 -m bootloader-spacemit.xml && repo sync -j24
```

A210 checkout:

```sh
mkdir -p "$RISE_WORKSPACE/bootloaders_alibaba" && cd "$RISE_WORKSPACE/bootloaders_alibaba" && repo init -u git@github.com:riseproject-dev/android_manifest.git -b android-17 -m bootloader-alibaba.xml && repo sync -j24
```


Build the K3 release chain and copy the results into Android:

```sh
cd "$RISE_WORKSPACE/bootloaders_k3/build-bootloaders" && bash release_android.sh --aosp="$RISE_WORKSPACE/aosp" --config=config/boards/spacemit-k3.yaml --mode=release
```

Build the A210 release chain and copy the results into Android:

```sh
cd "$RISE_WORKSPACE/bootloaders_alibaba/build-bootloaders" && bash release_android.sh --aosp="$RISE_WORKSPACE/aosp" --config=config/boards/alibaba-a210.yaml --mode=release
```


| Board | Config | Android destination |
| --- | --- | --- |
| K3 | `config/boards/spacemit-k3.yaml` | `vendor/rise/spacemit/k3/bootloader` |
| A210 | `config/boards/alibaba-a210.yaml` | `vendor/rise/alibaba/a210/bootloader` |

The default release command copies files without making a commit or changing
the Git index. `--mode=debug` builds the debug chain; `--no-build` stages
existing outputs. See the board-specific README in `build-bootloaders` for
individual component builds.

K3 FSBL and bootinfo are produced by its U-Boot tree. EC firmware is an
optional existing vendor blob selected with `EC_BIN`; it is not rebuilt by
these scripts. A210 retains the vendor BootZero binary and generates its
loader and primary GPT for 64 GB eMMC.

Both bootloaders load the Android v4 `init_boot` ramdisk. The A210 build
enables AVB verification of boot, vendor_boot and init_boot. Its current
development backend reports an unlocked device and does not persist rollback
indexes; a locked production chain needs a secure backend and separate tests.

## Mesa PowerVR builds

RISE Mesa sources live in
[`riseproject-dev/mesa`](https://github.com/riseproject-dev/mesa) on the single
branch `android-17-imagination`, which retains the original source history.
The PowerVR source matches commit
`f0cabdd9b5683daee75ad9a253fd71154f739278`. Build both board payloads in the
RISE Mesa checkout against their respective RISE Android output trees.

```sh
cd "$RISE_WORKSPACE" && git clone -b android-17-imagination git@github.com:riseproject-dev/mesa.git mesa
```


| Board | Mesa namespace | Prebuilt payload |
| --- | --- | --- |
| K3 | `device/rise/spacemit/k3/mesa` | `lib64/` and `etc/vulkan/icd.d/` |
| A210 | `device/rise/alibaba/a210/mesa` | `lib64/` and `etc/vulkan/icd.d/` |

The cross-build helper is `build-mesa-powervr.sh` in the Mesa repo. Its RISE
adaptation uses the two destinations above and their separate Android output
trees. Host tools required are Meson, Ninja, CMake, LLVM 15 or later with its
C++ libraries, `pkg-config`, `patchelf` and Python 3. Build Android first so
the sysroot, CRT objects and product libraries exist.

Build and deploy K3:

```sh
cd "$RISE_WORKSPACE/mesa" && bash build-mesa-powervr.sh --board=k3 --aosp="$RISE_WORKSPACE/aosp" --out=out-k3
```

Build and deploy A210:

```sh
cd "$RISE_WORKSPACE/mesa" && bash build-mesa-powervr.sh --board=a210 --aosp="$RISE_WORKSPACE/aosp" --out=out-a210
```

These commands replace the board's Android Mesa prebuilts. Rebuild Android
after deploying them. `--skip-native` reuses host compilers previously built
in this RISE Mesa checkout.
Existing Meson build directories are reconfigured and retained.

Save the exact source commit, cross file, Android output path, build options,
successful log and SHA-256 checksums with each payload. Test the complete
RISE bootloader, kernel and Android image set on each board; verify the
deployed libraries and validate Vulkan and OpenGL ES before describing them
as validated.

`external/mesa3d` remains the AOSP project selected by `default.xml`. It is
independent of these PowerVR prebuilts. Switching that manifest project does
not update the libraries consumed by K3 or A210.

## Chromium and WebView

K3 and A210 consume the same Android `riscv64` APK. Builds use the normal
`android-webview-riscv64/workspace/src` checkout created by the recipe below.

The recipe is in
[`riseproject-dev/android-webview-riscv64`](https://github.com/riseproject-dev/android-webview-riscv64).
It fetches the pinned base from the official
[Chromium repository](https://chromium.googlesource.com/chromium/src/), then
replays the seven original RISC-V commits bundled in `patches/chromium/`.
Original author and committer metadata, messages and signoffs are preserved;
each reconstructed commit SHA is checked against `series.json`. The recipe
also carries the three patches for separate DEPS repositories. `depot_tools`
and DEPS dependencies come from their public upstreams. All local changes
needed to rebuild the APK are in the RISE recipe repository.

| Input | Revision |
| --- | --- |
| Chromium release | `151.0.7922.108` |
| Upstream commit | `4744b886309d987d292e43232776d2206cccb13d` |
| Official release tag | `151.0.7922.108` |
| Reconstructed series tip | `0139499e9c33d18e27a0499ead341ca649f069e2` |
| depot_tools | `533321c34e1c3ba816bc5e820004fffe5b7fe4ad` |

Clone the recipe:

```sh
cd "$RISE_WORKSPACE" && git clone -b android-17 git@github.com:riseproject-dev/android-webview-riscv64.git android-webview-riscv64
```

Fetch, apply, build and inspect the riscv64 APK:

```sh
cd "$RISE_WORKSPACE/android-webview-riscv64" && ./scripts/01-fetch.sh && ./scripts/02-apply-series.sh && ./scripts/03-build.sh && ./scripts/04-verify-apk.sh
```


See the recipe's [README](https://github.com/riseproject-dev/android-webview-riscv64/blob/android-17/README.md)
for host requirements, GN options and runtime checks. The source remote is
`https://chromium.googlesource.com/chromium/src.git`; applying the bundled
series requires no separate fork. The dependency patches must be reapplied
after a `gclient sync`.

After verifying the replacement APK, copy it into the existing shared module:

```sh
cp "$RISE_WORKSPACE/android-webview-riscv64/workspace/src/out/riscv64/apks/SystemWebView64.apk" "$RISE_WORKSPACE/aosp/device/rise/common/webview/SystemWebView64.apk"
```


Both Android products include `webview_riscv64` from
`device/rise/common/webview`. Git LFS tracks its APK. Retain that
module's `Android.bp`; AOSP `external/chromium-webview` stays on its Google
remote. Rebuild both Android products after refreshing the shared APK.

The inherited M151 APK was tested on K3 in the BayLibre environment. A210
and the rebuilt RISE images require their own runtime checks.

The shared Android configuration is under `device/rise/common`. Both products
inherit its product and BoardConfig makefiles. HALs, codecs, A/B and AVB
configuration, shared policies and overlays are maintained there; CPU tuning,
kernel modules, partition groups, firmware and board wiring stay with K3 or
A210. The riscv64 SuperTuxKart prebuilt is also under `common/supertuxkart`.
Its module is available to both products but is not selected in their default
package lists.

## Board deployment and checks

Only use completed images for the corresponding board and storage layout.
The output directory contains its Android images, bootloader payloads and
flash helper. Flashing changes board storage; the A210 helper also erases
`userdata` and `misc`.

K3: start `fastboot usb 0` from the U-Boot console. The K3 helper has no
serial selector, so connect only the intended fastboot board. The RISE K3
configuration targets SPI-NOR for the boot chain and UFS/SCSI device 0
for Android. `--android-media` accepts only `ufs`; it does not change the
backend compiled into U-Boot. Confirm this bootloader and partition layout
on the board before using the flash helper. With a working bootloader,
flash Android only:

```sh
cd "$RISE_WORKSPACE/aosp/out-k3/target/product/k3" && bash flash_pico_itx.sh --android
```


`--bootloader` writes the K3 boot chain to SPI-NOR; `--dfu` uses the BROM
staging path. These bring-up paths and the K3 storage selection require
hardware verification; a host build does not establish that they work.

A210: set `FASTBOOT_SERIAL` to the board's fastboot identifier before using
its full bootloader and Android flash helper:

```sh
cd "$RISE_WORKSPACE/aosp/out-a210/target/product/a210" && sh flash_android_images.sh "$FASTBOOT_SERIAL"
```


After boot, set `ADB_SERIAL` to the board being tested. Check Android boot:

```sh
adb -s "$ADB_SERIAL" shell getprop sys.boot_completed
```

Check the selected WebView provider:

```sh
adb -s "$ADB_SERIAL" shell dumpsys webviewupdate
```

Inspect the graphics service:

```sh
adb -s "$ADB_SERIAL" shell dumpsys SurfaceFlinger
```


Also test display, GPU/Vulkan/OpenGL ES, WiFi, Bluetooth, audio, USB, storage,
reboot and slot switching on both boards. Exercise an app using WebView and
inspect renderer crashes and its sandbox. Record image hashes, UART/ADB
logs and results per board. A successful kernel or bootloader build is not
an Android or hardware test result.

## Record the delivery

Export resolved
manifest revisions for Android and for each kernel/bootloader workspace.
For Android:

```sh
cd "$RISE_WORKSPACE/aosp" && repo manifest -r -o "$RISE_WORKSPACE/android-sources.xml"
```


Keep those revision snapshots with artifact checksums and board results.
They must identify the commits actually used to produce the delivered
binaries; a snapshot taken with uncommitted changes does not capture those
changes.
