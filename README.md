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

The delivery branches listed below are hosted in RISE. A fresh checkout
requires access to each private repository and its Git LFS payloads.

| Repository | Delivery branch | Checkout path |
| --- | --- | --- |
| [android_manifest](https://github.com/riseproject-dev/android_manifest) | `android-17` | `manifest` |
| [android_device_rise](https://github.com/riseproject-dev/android_device_rise) | `android-17` | `aosp/device/rise` |
| [android_vendor_rise](https://github.com/riseproject-dev/android_vendor_rise) | `android-17` | `aosp/vendor/rise` |
| [android_generic_hal](https://github.com/riseproject-dev/android_generic_hal) | `android-17` | `aosp/hardware/generic` |
| [android_hardware_realtek](https://github.com/riseproject-dev/android_hardware_realtek) | `android-17` | `aosp/hardware/realtek` |
| [android_external_drm_hwcomposer](https://github.com/riseproject-dev/android_external_drm_hwcomposer) | `android-17` | `aosp/external/drm_hwcomposer` |
| [android_external_minigbm](https://github.com/riseproject-dev/android_external_minigbm) | `android-17` | `aosp/external/minigbm` |
| [android_external_zlib](https://github.com/riseproject-dev/android_external_zlib) | `android-17` | `aosp/external/zlib` |
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
The source uses Android 17 interfaces. Keep build checks and hardware results
separate: K3 tests do not establish A210 functionality.

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

The [android_external_zlib](https://github.com/riseproject-dev/android_external_zlib)
fork preserves the AOSP history and includes the board-tested RVV Adler-32
tail-load fix. The manifest selects its `android-17` branch, so `repo sync`
checks out the committed fix directly.

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

The dist target exports the kernel `Image`, `vmlinux`, `System.map`,
modules and DTB. Kernel updates must keep the Image and modules from the same
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
the Git index. `--mode=debug` builds the debug chain. `--no-build` stages
the outputs of a previous build. See the board-specific README in
`build-bootloaders` for individual component builds.

K3 FSBL and bootinfo are produced by its U-Boot tree. EC firmware is an
optional existing vendor blob selected with `EC_BIN`; it is not rebuilt by
these scripts. A210 retains the vendor BootZero binary and generates its
loader and primary GPT for 64 GB eMMC.

K3 SPL loads the combined U-Boot FIT at NOR offset `0x210000`. This FIT
contains OpenSBI in debug and release builds. The flash helper writes
`bootinfo`, `fsbl`, `env` and `uboot`; it skips the standalone OpenSBI image
and its legacy NOR slot. The environment image is 64 KiB, matching the
existing environment partition. SD/genimage and vendor JSON `multi_flash`
workflows are unsupported; `--sdcard` fails explicitly.

The NOR bootinfo retains the vendor fallback SPL1 offset `0xa0000`, which
also identifies the environment slot. Only primary SPL0 at `0x20000` is
programmed. Recovery through a second SPL copy remains unverified on hardware.

Both bootloaders load the Android v4 `init_boot` ramdisk. The A210 build
matches the validated boot configuration with U-Boot AVB verification
disabled. The Android images still contain their AVB metadata.

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

After verifying the replacement APK, preserve the old binary and copy the new
one into the existing shared module:

```sh
mkdir -p "$RISE_WORKSPACE/artifact-backups" && WEBVIEW_BACKUP="$(mktemp -d "$RISE_WORKSPACE/artifact-backups/webview.XXXXXX")" && cp "$RISE_WORKSPACE/aosp/device/rise/common/webview/SystemWebView64.apk" "$WEBVIEW_BACKUP/" && cp "$RISE_WORKSPACE/android-webview-riscv64/workspace/src/out/riscv64/apks/SystemWebView64.apk" "$RISE_WORKSPACE/aosp/device/rise/common/webview/SystemWebView64.apk"
```


Both Android products include `webview_riscv64` from
`device/rise/common/webview`. Git LFS tracks its APK. Retain that
module's `Android.bp`; AOSP `external/chromium-webview` stays on its Google
remote. Rebuild both Android products after refreshing the shared APK.

The RISE host rebuild completed on 2026-10-11 from the pinned official base
and bundled commits. APK verification passes: package `com.android.webview`,
version `151.0.7922.108`, target SDK 36 and RISC-V ELF machine 243. The staged
APK is 145,131,247 bytes with SHA-256
`09dae1f296faeb93e9d61cebdbca52111d21065358f45ee380e005176d73d006`.
The command above preserves the old binary.

The rebuilt RISE provider passed a real-page WebView test on K3 on
2026-10-12. Android signs the installed APK with `default_dev_cert`, so its
SHA-256 differs from the source APK above. The tested installed APK has
SHA-256 `0909e872c1d85b3edab16a9c59463ef2740e62d440d3b2d2b6722995a594b830`.
A210 page rendering still needs a board test.

The shared Android configuration is under `device/rise/common`. Both products
inherit its product and BoardConfig makefiles. HALs, codecs, A/B and AVB
configuration, shared policies and overlays are maintained there; CPU tuning,
kernel modules, partition groups, firmware and board wiring stay with K3 or
A210. Both products include the shared SuperTuxKart, Luanti, Mindustry and
OpenTTD prebuilts. SuperTuxKart uses the common scalar-ASTC APK.

## Board deployment and checks

Use the complete image set for the board being flashed. Keep the helper next
to its images and retain K3's `factory/` directory. Do not mix image lots.
The boot chain is on SPI-NOR and Android on UFS for K3; A210 uses eMMC.

### Host tools and image directories

Use Linux with `fastboot`, `adb`, `tar`, `sha256sum` and `lsusb` (`usbutils`),
and an account with USB device access. Connect the flashing port with a
USB data cable, provide stable board power and attach UART at 115200 baud.
Set `FASTBOOT` to the executable to use, or resolve it from `PATH`:

```sh
export FASTBOOT="${FASTBOOT:-$(command -v fastboot)}" && test -x "$FASTBOOT" && "$FASTBOOT" --version
```

For images built in this workspace:

```sh
export K3_IMAGES="$RISE_WORKSPACE/aosp/out-k3/target/product/k3"
```

```sh
export A210_IMAGES="$RISE_WORKSPACE/aosp/out-a210/target/product/a210"
```

For the delivered 2026-10-12 archives, place both archives and their outer
`SHA256SUMS` in `$RISE_WORKSPACE/packages`, then verify and extract them:

```sh
cd "$RISE_WORKSPACE/packages" && sha256sum -c SHA256SUMS
```

```sh
mkdir -p "$RISE_WORKSPACE/images" && tar -xzf "$RISE_WORKSPACE/packages/spacemit-k3-android17-20261012.tar.gz" -C "$RISE_WORKSPACE/images" && export K3_IMAGES="$RISE_WORKSPACE/images/spacemit-k3-android17-20261012" && cd "$K3_IMAGES" && sha256sum -c SHA256SUMS
```

```sh
mkdir -p "$RISE_WORKSPACE/images" && tar -xzf "$RISE_WORKSPACE/packages/alibaba-a210-android17-20261012.tar.gz" -C "$RISE_WORKSPACE/images" && export A210_IMAGES="$RISE_WORKSPACE/images/alibaba-a210-android17-20261012" && cd "$A210_IMAGES" && sha256sum -c SHA256SUMS
```

Each archive contains the executable flash helper, bootloader payloads,
Android images and `SHA256SUMS`. Keep build and test records separately.
A freshly built product directory needs its own checksum record when
preparing a new delivery.

### K3 first installation and recovery

Connect power first through the full-featured Type-C port (17) or ATX
connector (15). With the board powered, follow the manufacturer's
section 3.1.2:

1. Press and hold the FDL flashing button.
2. Briefly press the RST reset button.
3. Release the FDL flashing button.
4. Use the flashing Type-C data cable to connect the DRD Type-C port to the
   host computer.

The DRD Type-C port (18) does not power the board. The
[SpacemiT K3 hardware guide](https://cdn-resource.spacemit.com/file/product/K3/k3_pico_ug_en.pdf)
shows the ports and button positions in sections 2.2, 2.3.2 and 3.1.2.
For the powered-off alternative in section 3.1.1, hold FDL while connecting
the power supply, release FDL, then connect the DRD Type-C data cable.
Confirm BROM USB ID `361c:1001`:

```sh
lsusb -d 361c:1001 && "$FASTBOOT" devices
```

Connect only the intended fastboot board: the K3 helper has no serial
selector. For a first installation with fresh data:

```sh
cd "$K3_IMAGES" && bash flash_pico_itx.sh --dfu --wipe
```

This stages this image set's FSBL and U-Boot into RAM, installs the boot
chain in SPI-NOR, creates the Android GPT on UFS/SCSI device 0, writes both
Android boot slots and `super`, initializes data, then requests a reboot.
Power-cycle if the automatic reboot fails. The complete DFU flow passed on
the independently tested K3 for the 2026-10-12 scalar-STK lot; recovery using
the secondary SPL copy remains unverified.

For recovery while retaining data on a compatible partition layout:

```sh
cd "$K3_IMAGES" && bash flash_pico_itx.sh --dfu
```

### K3 updates with a working bootloader

Connect the flashing USB port and UART, reset or power on, and press a key
in the UART terminal during the U-Boot autoboot countdown. At the **board's
U-Boot prompt**, enter:

```sh
fastboot usb 0
```

On the **host**, check the fastboot endpoint, then update Android only:

```sh
"$FASTBOOT" devices
```

```sh
cd "$K3_IMAGES" && bash flash_pico_itx.sh --android
```

To update the SPI-NOR bootloader and Android together on an existing
Android GPT layout:

```sh
cd "$K3_IMAGES" && bash flash_pico_itx.sh
```

`--bootloader` updates only SPI-NOR. Normal fastboot modes reuse the existing
UFS GPT; use the full `--dfu` flow for first installation or a new layout.
The Android flows clear `misc` and reset the A/B boot state. Without
`--wipe`, they preserve `userdata`, `metadata` and `persist`. Adding
`--wipe` writes `userdata.img` and attempts to format `metadata` and
`persist`; unsupported formatting is deferred to Android's first boot.
All Android modes request a reboot. UFS is the only supported Android
backend; the optional flag syntax is `--android-media ufs`.

### A210 board connections

Use the USB flashing connector shown for the carrier revision in the
manufacturer's [V1 guide](https://developer.zhcomputing.com/zh/docs/2.8.1/A210/A210_Burning_Instruction/A210_SODIMM_V1_Burning_Instruction/)
or [V2 guide](https://developer.zhcomputing.com/en/docs/A210/A210_SODIMM_V2_Burning_Instruction_EN/).
Connect the board's 12 V power supply, flashing USB cable and UART.

### A210 first installation and boot-ROM recovery

For the A210 SODIMM V2 development board, follow the manufacturer's
sequence to enter USB flash mode:

1. Power on the board with the Power button.
2. Press and hold the Flash button.
3. Press the Reset button while holding the Flash button.

Connect the USB flashing port shown in the board's guide to the host.
Check the endpoint on the host:

```sh
"$FASTBOOT" devices
```

Connect only this board for recovery and omit the serial argument: BROM
and the staged U-Boot may expose different identifiers. Run a full clean
installation:

```sh
cd "$A210_IMAGES" && sh flash_android_images.sh --wipe && "$FASTBOOT" reboot
```

The helper stages the supplied BootZero and SPL-with-FIT images into RAM,
reboots through those stages, then installs the eMMC bootloader and Android
images. It does not put the board into BROM itself. To retain data on a
compatible layout, omit `--wipe`. Return any latched recovery switch to its
normal position before booting. This recovery description follows the
helper and manufacturer documentation; a complete current-lot A210 hardware
validation report is still pending.

### A210 updates with a working bootloader

Reset or power on, interrupt U-Boot autoboot in the UART terminal and enter
at the **board's U-Boot prompt**:

```sh
fastboot usb 0
```

On the **host**, list the connected devices and set `FASTBOOT_SERIAL` to the
A210 identifier printed by that command:

```sh
"$FASTBOOT" devices
```

```sh
export FASTBOOT_SERIAL="<A210 identifier from fastboot devices>"
```

Check the selected U-Boot product, which the helper recognizes as `a2...`:

```sh
"$FASTBOOT" -s "$FASTBOOT_SERIAL" getvar product
```

Flash from the A210 image directory, then explicitly reboot after success:

```sh
cd "$A210_IMAGES" && sh flash_android_images.sh "$FASTBOOT_SERIAL" && "$FASTBOOT" -s "$FASTBOOT_SERIAL" reboot
```

For a first installation or a deliberate data wipe:

```sh
cd "$A210_IMAGES" && sh flash_android_images.sh --wipe "$FASTBOOT_SERIAL" && "$FASTBOOT" -s "$FASTBOOT_SERIAL" reboot
```

The helper always writes the 64 GB eMMC GPT, bootloader, U-Boot environment,
both Android boot slots, vbmeta chains and `super`. It erases `misc` to reset
A/B metadata and does not call `set_active`. It preserves `userdata` by
default; `--wipe` erases only `userdata`. It never erases `metadata` or
`persist`. Retaining data requires a compatible existing partition layout.
The helper does not reboot at the end; use the explicit reboot above or
reset/power-cycle the board after it reports success.

### Troubleshooting and first boot

If no endpoint appears, check the data cable, flashing port, power, host USB
permissions and selected board mode. During RAM bootstrap the USB device
disconnects and reconnects; if a serial-selected command waits for a device,
check `fastboot devices` again. If a flash command fails, retain its output
and UART log, correct the cause, and repeat the complete matching flow.
Use BROM recovery when the installed bootloader cannot reach fastboot.

Watch UART for bootloader, kernel and Android startup. Once ADB appears,
identify the device and use its identifier as `ADB_SERIAL`:

```sh
adb devices
```

```sh
export ADB_SERIAL="<board identifier from adb devices>"
```

Check Android boot; the expected completion value is `1`:

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

Keep the resolved `android_external_zlib` revision with the build records.
Its commit identifies the RVV tail-load fix included in the delivered
binaries.
