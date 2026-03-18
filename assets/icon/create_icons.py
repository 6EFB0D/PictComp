# -*- coding: utf-8 -*-
"""
JPG画像からWindows用.icoとmacOS用.icnsを作成するスクリプト

- Windows用: .ico ファイル（Pillowで直接生成）
- macOS用: .icns ファイル（iconutil または iconset から Python で生成）
"""

from PIL import Image
from pathlib import Path
import sys
import platform
import struct

# ICOに含めるサイズ（Windows標準）
ICO_SIZES = [16, 32, 48, 64, 128, 256]

# macOS iconset に必要なサイズ
ICONSET_SIZES = [16, 32, 64, 128, 256, 512]


def load_and_prepare_image(path: Path) -> Image.Image:
    """画像を読み込み、RGBAに変換"""
    img = Image.open(path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    return img


def create_ico(img: Image.Image, ico_path: Path) -> bool:
    """複数サイズのICOファイルを作成"""
    try:
        images = []
        for size in ICO_SIZES:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            images.append(resized)

        ico_path.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(
            ico_path,
            format="ICO",
            sizes=[(img.width, img.height) for img in images],
            append_images=images[1:] if len(images) > 1 else [],
        )
        print(f"  [OK] {ico_path.name}")
        return True
    except Exception as e:
        print(f"  [NG] {ico_path.name}: {e}")
        return False


def create_iconset(img: Image.Image, iconset_dir: Path) -> bool:
    """macOS用iconsetフォルダを作成（.icns変換用のPNG群）"""
    try:
        if iconset_dir.exists():
            for f in iconset_dir.iterdir():
                f.unlink()
        iconset_dir.mkdir(parents=True, exist_ok=True)

        for size in ICONSET_SIZES:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(iconset_dir / f"icon_{size}x{size}.png")
            size2 = size * 2
            resized2 = img.resize((size2, size2), Image.Resampling.LANCZOS)
            resized2.save(iconset_dir / f"icon_{size}x{size}@2x.png")

        print(f"  [OK] {iconset_dir.name}/")
        return True
    except Exception as e:
        print(f"  [NG] {iconset_dir.name}: {e}")
        return False


def create_icns_from_iconset(iconset_dir: Path, icns_path: Path) -> bool:
    """
    iconset フォルダから .icns を作成（iconify のロジックを参考、全プラットフォーム対応）
    """
    # サイズと ICNS タイプの対応（Apple Icon Image format）
    sizetotypes = {
        16: [b"icp4"],
        32: [b"icp5", b"ic11"],
        64: [b"icp6", b"ic12"],
        128: [b"ic07"],
        256: [b"ic08", b"ic13"],
        512: [b"ic09", b"ic14"],
        1024: [b"ic10"],
    }

    withtypes = []
    for png_path in sorted(iconset_dir.glob("*.png")):
        try:
            pilimg = Image.open(png_path)
            width, height = pilimg.size
            if width != height or width not in sizetotypes:
                continue
            imagedata = png_path.read_bytes()
            for icontype in sizetotypes[width]:
                withtypes.append([icontype, imagedata])
        except Exception:
            continue

    if not withtypes:
        return False

    withtypes.sort(key=lambda x: x[0])

    try:
        with open(icns_path, "wb") as f:
            f.write(b"icns")
            filelen = 8 + sum((8 + len(imagedata)) for _, imagedata in withtypes)
            f.write(struct.pack(">I", filelen))
            for icontype, imagedata in withtypes:
                f.write(icontype)
                f.write(struct.pack(">I", 8 + len(imagedata)))
                f.write(imagedata)
        print(f"  [OK] {icns_path.name}")
        return True
    except Exception as e:
        print(f"  [NG] {icns_path.name}: {e}")
        return False


def create_icns_on_macos(iconset_dir: Path, icns_path: Path) -> bool:
    """macOS上でiconutilを使って.icnsを作成（利用可能なら）"""
    if platform.system() != "Darwin":
        return False
    try:
        import subprocess

        subprocess.run(
            ["iconutil", "-c", "icns", "-o", str(icns_path), str(iconset_dir)],
            check=True,
            capture_output=True,
        )
        print(f"  [OK] {icns_path.name}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    script_dir = Path(__file__).parent

    # 入力JPG
    sources = [
        ("pictcomp_bright.jpg", "pictcomp_bright"),
        ("pictcomp_dark.jpg", "pictcomp_dark"),
    ]

    print("アイコンファイルを作成します...")
    print()

    success_ico = 0
    success_iconset = 0
    success_icns = 0

    for jpg_name, base_name in sources:
        jpg_path = script_dir / jpg_name
        if not jpg_path.exists():
            print(f"[NG] {jpg_name} not found")
            continue

        print(f"[{base_name}]")
        img = load_and_prepare_image(jpg_path)

        # Windows用 .ico
        ico_path = script_dir / f"{base_name}.ico"
        if create_ico(img, ico_path):
            success_ico += 1

        # macOS用 .iconset
        iconset_dir = script_dir / f"{base_name}.iconset"
        if create_iconset(img, iconset_dir):
            success_iconset += 1

        # macOS用 .icns 作成（iconutil または iconset から Python で生成）
        icns_path = script_dir / f"{base_name}.icns"
        if create_icns_on_macos(iconset_dir, icns_path):
            success_icns += 1
        elif create_icns_from_iconset(iconset_dir, icns_path):
            success_icns += 1

        print()

    # 結果サマリー
    print("=" * 50)
    print(f"Windows用 .ico: {success_ico}/{len(sources)} 作成")
    print(f"macOS用 .iconset: {success_iconset}/{len(sources)} 作成")
    print(f"macOS用 .icns: {success_icns}/{len(sources)} 作成")
    print("=" * 50)

    return 0 if success_ico == len(sources) else 1


if __name__ == "__main__":
    sys.exit(main())
