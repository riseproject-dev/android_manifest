#!/bin/bash
# Package the Android images of one board like the RISE releases: a tarball
# with the images, the flash script and tools, the license notices and the
# pinned manifest the images were built from.
#
# usage: package-android.sh <aosp workspace> <out dir> <k3|a210> <name> <pinned manifest> <destination>
set -eo pipefail

aosp=$1
out=$2
board=$3
name=$4
manifest=$5
dest=$6

case $board in
k3)
	product=k3
	dir="rise-$name-k3-pico-itx"
	extra="dtb.img flash_pico_itx.sh u-boot.itb fw_dynamic.itb env.bin partition_nor.json factory/FSBL.bin factory/bootinfo_spinor.bin"
	;;
a210)
	product=a210
	dir="rise-$name-a210-evb"
	extra="dtb.img flash_android_images.sh bootzero-rvbl.bin spl-with-fit-rvbl.bin emmc_boot-loader.img emmc-gpt_primary.img emmc-uboot_env.img"
	;;
*)
	echo "Unknown board '$board'." >&2
	exit 1
	;;
esac

staging="$dest/staging/$dir"
prod="$aosp/$out/target/product/$product"
host="$aosp/$out/host/linux-x86/bin"

mkdir -p "$staging"
for image in boot init_boot vendor_boot vbmeta vbmeta_vendor_dlkm vbmeta_system_dlkm super userdata; do
	cp "$prod/$image.img" "$staging/"
done
cp "$prod/system/etc/NOTICE.xml.gz" "$staging/NOTICE_system.xml.gz"
cp "$prod/vendor/etc/NOTICE.xml.gz" "$staging/NOTICE_vendor.xml.gz"
for file in $extra; do
	mkdir -p "$staging/$(dirname "$file")"
	cp "$prod/$file" "$staging/$file"
done
for file in adb fastboot mke2fs; do
	cp "$host/$file" "$staging/"
done
cp "$manifest" "$staging/manifest.xml"
tar -czf "$dest/$dir.tar.gz" -C "$dest/staging" "$dir"
rm -rf "$dest/staging"
