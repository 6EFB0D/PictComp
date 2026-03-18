# -*- coding: utf-8 -*-
"""
PictComp 旧版（v1.x）コマンドラインアプリ
※ 新規利用は gui_main.py（GUI版）または app_streamlit.py（Web版）を推奨
"""
import os
from PIL import Image
import pillow_heif
from tkinter import Tk, filedialog
from tqdm import tqdm
import logging

# フォルダ選択ダイアログを表示
def select_folder(title):
    root = Tk()
    root.withdraw()  # Tkinterウィンドウを表示しない
    folder_path = filedialog.askdirectory(title=title)
    root.destroy()
    return folder_path

# 入力フォルダと出力フォルダを選択
input_folder = select_folder("📂 入力フォルダを選択してください")
output_folder = select_folder("📁 出力フォルダを選択してください")

# 出力フォルダが存在しない場合は作成
os.makedirs(output_folder, exist_ok=True)

# ログファイルの設定（拡張子 .log）
log_file_path = os.path.join(output_folder, "compression_log.log")
logging.basicConfig(filename=log_file_path, level=logging.INFO, format='%(asctime)s - %(message)s')

# PowerPoint用の目安サイズ（KB）
target_size_kb = 300
target_size_bytes = target_size_kb * 1024

# JPG画像を圧縮する関数
def compress_image(input_path, output_path):
    img = Image.open(input_path)
    quality = 85
    while True:
        img.save(output_path, format='JPEG', quality=quality)
        if os.path.getsize(output_path) <= target_size_bytes or quality <= 20:
            break
        quality -= 5

# 対象ファイルの一覧を取得
files = [f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))]

# プログレスバー付きで処理
for filename in tqdm(files, desc="画像圧縮中", unit="ファイル"):
    file_path = os.path.join(input_folder, filename)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    try:
        if ext in [".jpg", ".jpeg"]:
            output_path = os.path.join(output_folder, f"{name}_compressed.jpg")
            compress_image(file_path, output_path)
            logging.info(f"JPG圧縮: {filename} → {name}_compressed.jpg")

        elif ext == ".heic":
            heif_file = pillow_heif.read_heif(file_path)
            img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            jpg_path = os.path.join(output_folder, f"{name}_compressed.jpg")
            img.save(jpg_path, format="JPEG")
            compress_image(jpg_path, jpg_path)
            logging.info(f"HEIC変換・圧縮: {filename} → {name}_compressed.jpg")

        else:
            logging.info(f"スキップ（未対応形式）: {filename}")

    except Exception as e:
        logging.error(f"エラー発生: {filename} - {str(e)}")
