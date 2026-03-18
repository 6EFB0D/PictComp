# -*- coding: utf-8 -*-
"""
画像ビューアモジュール
画像を閲覧し、撮影日時でソートする機能を提供
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pillow_heif
from exif_viewer import ExifViewer
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import threading


class ImageViewer:
    """画像ビューアクラス"""
    
    def __init__(self, parent_window, exif_callback=None):
        self.parent = parent_window
        self.exif_callback = exif_callback  # EXIF情報表示のコールバック関数
        self.viewer_window = None
        self.current_folder = None
        self.image_files = []
        self.current_index = 0
        self.sort_mode = "filename"  # "filename", "shoot_date", "file_date"
        self.image_cache = {}
    
    def open_viewer(self, folder_path: str = None):
        """ビューアを開く"""
        if not folder_path:
            folder_path = filedialog.askdirectory(title="画像フォルダを選択してください")
            if not folder_path:
                return
        
        self.current_folder = folder_path
        self.load_images()
        
        if not self.image_files:
            messagebox.showwarning("警告", "画像ファイルが見つかりませんでした。")
            return
        
        self.create_viewer_window()
    
    def load_images(self):
        """画像ファイルを読み込む"""
        if not self.current_folder:
            return
        
        supported_extensions = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
        all_files = [f for f in os.listdir(self.current_folder) 
                    if os.path.isfile(os.path.join(self.current_folder, f)) 
                    and os.path.splitext(f)[1].lower() in supported_extensions]
        
        # ファイル情報を取得
        self.image_files = []
        for filename in all_files:
            file_path = os.path.join(self.current_folder, filename)
            file_stat = os.stat(file_path)
            
            # EXIF情報から撮影日時を取得
            exif_data = ExifViewer.get_exif_data(file_path)
            shoot_date = None
            
            if exif_data and not "error" in exif_data:
                if "DateTimeOriginal" in exif_data:
                    try:
                        shoot_date = datetime.strptime(exif_data["DateTimeOriginal"], "%Y:%m:%d %H:%M:%S")
                    except:
                        pass
                elif "DateTimeDigitized" in exif_data:
                    try:
                        shoot_date = datetime.strptime(exif_data["DateTimeDigitized"], "%Y:%m:%d %H:%M:%S")
                    except:
                        pass
                elif "DateTime" in exif_data:
                    try:
                        shoot_date = datetime.strptime(exif_data["DateTime"], "%Y:%m:%d %H:%M:%S")
                    except:
                        pass
            
            self.image_files.append({
                "filename": filename,
                "path": file_path,
                "file_date": datetime.fromtimestamp(file_stat.st_ctime),
                "shoot_date": shoot_date,
                "size": file_stat.st_size
            })
        
        # ソート
        self.sort_images()
    
    def sort_images(self):
        """画像をソート"""
        if self.sort_mode == "filename":
            self.image_files.sort(key=lambda x: x["filename"].lower())
        elif self.sort_mode == "shoot_date":
            self.image_files.sort(key=lambda x: x["shoot_date"] if x["shoot_date"] else datetime.min)
        elif self.sort_mode == "file_date":
            self.image_files.sort(key=lambda x: x["file_date"])
    
    def create_viewer_window(self):
        """ビューアウィンドウを作成"""
        if self.viewer_window:
            self.viewer_window.destroy()
        
        self.viewer_window = tk.Toplevel(self.parent)
        self.viewer_window.title(f"画像ビューア - {os.path.basename(self.current_folder)}")
        self.viewer_window.geometry("1200x800")
        
        # メインフレーム
        main_frame = ttk.Frame(self.viewer_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ツールバー
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Label(toolbar, text="ソート:").pack(side=tk.LEFT, padx=5)
        
        # ソートモードの表示名を日本語に
        sort_display_names = {
            "filename": "ファイル名",
            "shoot_date": "撮影日時",
            "file_date": "ファイル日時"
        }
        
        # 現在のソートモードに対応する日本語表示名を取得
        current_display = sort_display_names.get(self.sort_mode, self.sort_mode)
        
        sort_var = tk.StringVar(value=current_display)
        sort_combo = ttk.Combobox(toolbar, textvariable=sort_var, 
                                  values=list(sort_display_names.values()),
                                  state="readonly", width=15)
        sort_combo.pack(side=tk.LEFT, padx=5)
        
        def on_sort_change(event):
            # 日本語表示名から内部値に変換
            display_name = sort_var.get()
            mode = None
            for key, value in sort_display_names.items():
                if value == display_name:
                    mode = key
                    break
            if mode:
                self.change_sort_mode(mode)
        
        sort_combo.bind("<<ComboboxSelected>>", on_sort_change)
        
        ttk.Button(toolbar, text="撮影日時に合わせてファイル日時を一括更新", 
                  command=self.batch_update_file_dates).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="フォルダを変更", command=self.change_folder).pack(side=tk.LEFT, padx=5)
        
        # 画像表示エリアとファイル一覧を分割
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左側: ファイル一覧（サムネイル付き）
        list_frame = ttk.LabelFrame(paned, text="ファイル一覧", padding="5")
        paned.add(list_frame, weight=1)
        
        # サムネイル表示用のキャンバス
        canvas_frame = ttk.Frame(list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        list_scroll = ttk.Scrollbar(canvas_frame)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.thumbnail_canvas = tk.Canvas(canvas_frame, yscrollcommand=list_scroll.set)
        self.thumbnail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.thumbnail_canvas.yview)
        
        # サムネイル用のフレーム
        self.thumbnail_frame = ttk.Frame(self.thumbnail_canvas)
        self.thumbnail_canvas_window = self.thumbnail_canvas.create_window(
            (0, 0), window=self.thumbnail_frame, anchor="nw"
        )
        
        def configure_canvas(event):
            self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
            self.thumbnail_canvas.itemconfig(self.thumbnail_canvas_window, width=event.width)
        
        self.thumbnail_canvas.bind("<Configure>", configure_canvas)
        self.thumbnail_frame.bind("<Configure>", configure_canvas)
        
        # マウスホイールでスクロール
        def on_mousewheel(event):
            self.thumbnail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.thumbnail_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        self.thumbnail_widgets = []  # サムネイルウィジェットを保持
        
        # 右側: 画像表示
        image_frame = ttk.LabelFrame(paned, text="画像プレビュー", padding="5")
        paned.add(image_frame, weight=2)
        
        self.image_label = ttk.Label(image_frame, text="画像を選択してください")
        self.image_label.pack(expand=True)
        
        # 情報表示
        info_frame = ttk.Frame(image_frame)
        info_frame.pack(fill=tk.X, pady=5)
        
        self.info_label = ttk.Label(info_frame, text="", font=("Courier", 9))
        self.info_label.pack()
        
        # ナビゲーションボタン
        nav_frame = ttk.Frame(image_frame)
        nav_frame.pack(pady=5)
        
        ttk.Button(nav_frame, text="前へ", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="撮影情報", command=self.show_exif_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="次へ", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        # ファイル一覧を更新
        self.update_file_list()
        
        # 最初の画像を表示
        if self.image_files:
            self.current_index = 0
            self.display_image(0)
    
    def update_file_list(self):
        """ファイル一覧を更新（サムネイル付き）"""
        # 既存のサムネイルを削除
        for widget in self.thumbnail_widgets:
            widget.destroy()
        self.thumbnail_widgets.clear()
        
        thumbnail_size = (150, 100)  # サムネイルサイズ
        
        for idx, img_info in enumerate(self.image_files):
            # サムネイル用のフレーム
            thumb_frame = ttk.Frame(self.thumbnail_frame, relief=tk.RAISED, borderwidth=1)
            thumb_frame.pack(fill=tk.X, padx=2, pady=2)
            
            # サムネイル画像を読み込み
            try:
                if img_info["path"].lower().endswith(".heic"):
                    heif_file = pillow_heif.read_heif(img_info["path"])
                    img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
                else:
                    img = Image.open(img_info["path"])
                
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # サムネイル画像を表示
                thumb_label = ttk.Label(thumb_frame, image=photo)
                thumb_label.image = photo  # 参照を保持
                thumb_label.pack(pady=2)
                thumb_label.bind("<Button-1>", lambda e, i=idx: self.select_image(i))
                
            except Exception as e:
                # 画像読み込みエラーの場合
                error_label = ttk.Label(thumb_frame, text="画像読み込みエラー", foreground="red")
                error_label.pack(pady=2)
            
            # ファイル名と日時情報
            filename = img_info["filename"]
            shoot_date_str = ""
            if img_info["shoot_date"]:
                shoot_date_str = img_info["shoot_date"].strftime("%Y-%m-%d %H:%M")
            else:
                shoot_date_str = "撮影日時なし"
            
            file_date_str = img_info["file_date"].strftime("%Y-%m-%d %H:%M")
            
            # 警告マーク
            warning_mark = ""
            if img_info["shoot_date"] and img_info["shoot_date"] != img_info["file_date"]:
                warning_mark = "⚠ "
            
            # ファイル名（短縮）
            display_filename = filename if len(filename) <= 30 else filename[:27] + "..."
            info_label = ttk.Label(thumb_frame, text=f"{warning_mark}{display_filename}\n撮影:{shoot_date_str}", 
                                   font=("Courier", 8), wraplength=150)
            info_label.pack(pady=2)
            info_label.bind("<Button-1>", lambda e, i=idx: self.select_image(i))
            
            # 選択状態の視覚化
            if idx == self.current_index:
                thumb_frame.configure(relief=tk.SOLID, borderwidth=2)
                for widget in thumb_frame.winfo_children():
                    if isinstance(widget, ttk.Label):
                        widget.configure(background="lightblue")
            
            self.thumbnail_widgets.append(thumb_frame)
        
        # スクロール位置を調整
        if self.current_index < len(self.image_files):
            # 選択されたサムネイルまでスクロール
            self.thumbnail_canvas.update_idletasks()
            widget = self.thumbnail_widgets[self.current_index]
            y_position = widget.winfo_y()
            self.thumbnail_canvas.yview_moveto(y_position / self.thumbnail_frame.winfo_height())
    
    def select_image(self, index: int):
        """画像を選択"""
        self.current_index = index
        self.display_image(index)
        self.update_file_list()  # 選択状態を更新
    
    def change_sort_mode(self, mode: str):
        """ソートモードを変更"""
        self.sort_mode = mode
        self.sort_images()
        old_index = self.current_index
        # 現在のファイル名を保持
        if self.image_files:
            current_filename = self.image_files[old_index]["filename"]
            # 新しいインデックスを検索
            for idx, img_info in enumerate(self.image_files):
                if img_info["filename"] == current_filename:
                    self.current_index = idx
                    break
        self.update_file_list()
        if self.image_files:
            self.display_image(self.current_index)
    
    def change_folder(self):
        """フォルダを変更"""
        folder = filedialog.askdirectory(title="画像フォルダを選択してください")
        if folder:
            self.current_folder = folder
            self.load_images()
            if self.image_files:
                self.current_index = 0
                self.update_file_list()
                if self.image_files:
                    self.display_image(0)
            else:
                messagebox.showwarning("警告", "画像ファイルが見つかりませんでした。")
    
    
    def display_image(self, index: int):
        """画像を表示"""
        if not (0 <= index < len(self.image_files)):
            return
        
        img_info = self.image_files[index]
        file_path = img_info["path"]
        
        try:
            # 画像を読み込み
            if file_path.lower().endswith(".heic"):
                heif_file = pillow_heif.read_heif(file_path)
                img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            else:
                img = Image.open(file_path)
            
            # 表示サイズにリサイズ
            display_width = 800
            display_height = 600
            
            img.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo, text="")
            self.image_label.image = photo  # 参照を保持
            
            # 情報を表示
            shoot_date_str = img_info["shoot_date"].strftime("%Y-%m-%d %H:%M:%S") if img_info["shoot_date"] else "不明"
            file_date_str = img_info["file_date"].strftime("%Y-%m-%d %H:%M:%S")
            size_mb = img_info["size"] / 1024 / 1024
            
            info_text = f"ファイル: {img_info['filename']}\n"
            info_text += f"撮影日時: {shoot_date_str}\n"
            info_text += f"ファイル作成日時: {file_date_str}\n"
            info_text += f"サイズ: {size_mb:.2f} MB | {index + 1}/{len(self.image_files)}"
            
            if img_info["shoot_date"] and img_info["shoot_date"] != img_info["file_date"]:
                info_text += "\n⚠ 撮影日時とファイル日時が異なります"
            
            self.info_label.config(text=info_text)
            
        except Exception as e:
            self.image_label.config(image="", text=f"画像読み込みエラー: {str(e)}")
            self.info_label.config(text=f"エラー: {str(e)}")
    
    def prev_image(self):
        """前の画像を表示"""
        if self.current_index > 0:
            self.current_index -= 1
            self.display_image(self.current_index)
            self.update_file_list()  # 選択状態を更新
    
    def next_image(self):
        """次の画像を表示"""
        if self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.display_image(self.current_index)
            self.update_file_list()  # 選択状態を更新
    
    def show_exif_info(self):
        """EXIF情報を表示"""
        if not (0 <= self.current_index < len(self.image_files)):
            return
        
        img_info = self.image_files[self.current_index]
        # コールバック関数があればそれを使用、なければ簡易表示
        if self.exif_callback:
            self.exif_callback(img_info["path"], img_info["filename"])
        else:
            self.show_exif_info_simple(img_info["path"], img_info["filename"])
    
    def show_exif_info_simple(self, file_path: str, filename: str):
        """EXIF情報を簡易表示"""
        exif_window = tk.Toplevel(self.viewer_window)
        exif_window.title(f"撮影情報 - {filename}")
        exif_window.geometry("800x550")
        
        exif_data = ExifViewer.get_exif_data(file_path)
        
        main_frame = ttk.Frame(exif_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        if not exif_data or "error" in exif_data:
            if "error" in exif_data:
                ttk.Label(main_frame, text=f"エラー: {exif_data['error']}", foreground="red").pack(pady=20)
            else:
                ttk.Label(main_frame, text="この画像には撮影情報が含まれていません。", foreground="gray").pack(pady=20)
            ttk.Button(main_frame, text="閉じる", command=exif_window.destroy).pack(pady=10)
            return
        
        # 簡易表示
        text_widget = tk.Text(main_frame, wrap=tk.WORD, font=("Courier", 9))
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        summary_data = ExifViewer.get_exif_summary(exif_data)
        for category, item, value in summary_data:
            text_widget.insert(tk.END, f"{category} | {item}: {value}\n")
        
        text_widget.config(state=tk.DISABLED)
        ttk.Button(main_frame, text="閉じる", command=exif_window.destroy).pack(pady=10)
    
    def batch_update_file_dates(self):
        """撮影日時に基づいてファイル日時を一括更新"""
        # 撮影日時があるファイルをフィルタ
        files_to_update = [img for img in self.image_files 
                          if img["shoot_date"] and img["shoot_date"] != img["file_date"]]
        
        if not files_to_update:
            messagebox.showinfo("情報", "更新が必要なファイルはありません。")
            return
        
        result = messagebox.askyesno(
            "確認",
            f"{len(files_to_update)}個のファイルの日時を更新しますか？\n\n"
            f"撮影日時に合わせてファイルの作成日時と更新日時を変更します。"
        )
        
        if not result:
            return
        
        success_count = 0
        error_count = 0
        
        for img_info in files_to_update:
            try:
                import time
                timestamp = img_info["shoot_date"].timestamp()
                os.utime(img_info["path"], (timestamp, timestamp))
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"エラー: {img_info['filename']} - {str(e)}")
        
        messagebox.showinfo(
            "完了",
            f"ファイル日時の更新が完了しました。\n\n"
            f"成功: {success_count}個\n"
            f"失敗: {error_count}個"
        )
        
        # ファイル情報を再読み込み
        self.load_images()
        self.update_file_list()
        self.display_image(self.current_index)

