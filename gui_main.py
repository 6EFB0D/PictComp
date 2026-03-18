# -*- coding: utf-8 -*-
"""
画像圧縮アプリのメインGUI
"""
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from typing import List, Optional
from datetime import datetime
from image_compressor import ImageCompressor, CompressionSettings
from config_manager import ConfigManager
from license_manager import LicenseManager
from presets import PresetManager
import logging
from PIL import Image, ImageTk
import pillow_heif
from exif_viewer import ExifViewer
from image_viewer import ImageViewer


class PictCompGUI:
    """メインGUIクラス"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("PictComp - 画像一括圧縮アプリ")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        # 設定管理
        self.config_manager = ConfigManager()
        self.license_manager = LicenseManager()
        self.settings = self.config_manager.load_settings() or CompressionSettings()
        
        # 圧縮エンジン
        self.compressor = ImageCompressor(self.settings)
        
        # 変数
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.processing = False
        
        # ログ設定
        self.setup_logging()
        
        # GUI構築
        self.create_widgets()
        
        # 前回設定の読み込み
        self.load_last_settings()
        
        # メニューバー（Pro版準備中を表示）
        self.create_menu()
        
        # 初回起動日を記録（14日間トライアル用）
        self.license_manager.get_usage_data()
        
        # トライアル期限切れの場合は起動時に通知
        self.root.after(100, self._check_trial_expired_on_startup)
    
    def create_menu(self):
        """メニューバーを作成"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="閉じる", command=self._quit_app)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self.show_usage_info)
        # Pro版・ライセンス（サブメニュー）
        license_menu = tk.Menu(help_menu, tearoff=0)
        help_menu.add_cascade(label="Pro版・ライセンス", menu=license_menu)
        license_menu.add_command(label="Pro版について", command=self._show_pro_info)
        license_menu.add_command(label="Pro版を購入", command=self._show_pro_purchase)
        license_menu.add_command(label="ライセンスキーを入力", command=self._show_license_input)
        help_menu.add_separator()
        help_menu.add_command(label="バージョン情報", command=self.show_version_info)
        # サポート・お問い合わせ（サブメニュー）
        support_menu = tk.Menu(help_menu, tearoff=0)
        help_menu.add_cascade(label="サポート・お問い合わせ", menu=support_menu)
        support_menu.add_command(label="PictCompのページ", command=self._open_pictcomp_page)
        support_menu.add_command(label="お問い合わせ (support@office-goplan.com)", command=self._open_support_email)
        support_menu.add_command(label="Office Go Plan（ホームページ）", command=self._open_homepage)
        try:
            from version import FEEDBACK_FORM_URL
            feedback_url = os.environ.get("PICTCOMP_FEEDBACK_FORM_URL") or FEEDBACK_FORM_URL or ""
            if feedback_url:
                support_menu.add_separator()
                support_menu.add_command(label="アンケート・要望を送信", command=lambda: webbrowser.open(feedback_url))
        except ImportError:
            pass
    
    def _quit_app(self):
        """アプリを終了"""
        self.root.destroy()
    
    def _show_pro_info(self):
        """Pro版情報を表示"""
        pro_text = """Pro版について

【Pro版の機能】
• 1回の処理枚数: 無制限
• EXIF（撮影情報）の保持
• レポートのエクスポート（CSV/JSON）
• 撮影日時に基づくファイル名変更

【プレリリース】初回起動から14日間は全機能を無料でお試しいただけます。

Pro版の購入は現在準備中です。近日公開予定です。"""
        messagebox.showinfo("Pro版について", pro_text)
    
    def _show_pro_purchase(self):
        """Pro版購入情報を表示"""
        messagebox.showinfo("Pro版を購入", "Pro版の購入は現在準備中です。\n近日公開予定です。")
    
    def _show_license_input(self):
        """ライセンスキー入力ダイアログを表示"""
        messagebox.showinfo(
            "ライセンスキー入力",
            "ライセンスキー入力機能は現在準備中です。\n\n"
            "Pro版の購入とライセンスキー入力機能は近日公開予定です。\n"
            "詳細は「Pro版について」メニューをご確認ください。"
        )
    
    def _open_pictcomp_page(self):
        """PictCompのページを開く"""
        try:
            from version import PICTCOMP_PAGE_URL
            url = os.environ.get("PICTCOMP_PAGE_URL") or PICTCOMP_PAGE_URL or ""
            if url:
                webbrowser.open(url)
            else:
                messagebox.showinfo("PictCompのページ", "PictCompのページは準備中です。")
        except ImportError:
            messagebox.showinfo("PictCompのページ", "PictCompのページは準備中です。")
    
    def _open_support_email(self):
        """お問い合わせ（メール）を開く"""
        webbrowser.open("mailto:support@office-goplan.com")
    
    def _open_homepage(self):
        """Office Go Plan ホームページを開く"""
        from version import HOMEPAGE
        webbrowser.open(HOMEPAGE)
    
    def show_usage_info(self):
        """使い方（EXIFの注意・無料版とPro版の違い含む）を表示"""
        usage_text = """【基本的な使い方】
1. 入力フォルダ・出力フォルダを選択
2. プリセットを選ぶか、圧縮設定を調整
3. 「圧縮開始」で処理を実行

【EXIF（撮影情報）について】
以下の点にご注意ください：

• セキュリティ: GPS情報が含まれると撮影場所が特定されるリスクがあります。Web公開する画像ではEXIF削除を推奨します。
• 個人情報保護: 撮影日時・カメラ機種・レンズ情報などが含まれます。不特定多数に公開する場合は削除を検討してください。
• ファイル容量: EXIFを保持するとファイルサイズが増えます。容量を抑えたい場合は削除を選択してください。

※ ブログ用・SNS用・Web用・メール添付用・PNG透過保持のプリセットでは、セキュリティ・個人情報保護の観点からEXIF削除が固定されています。

【プレリリース】初回起動から14日間は全機能を無料でお試しいただけます。

【無料版とPro版の違い】※Pro版は準備中です。
• 1回の処理枚数: 無料版 20枚まで / Pro版・トライアル 無制限
• 基本圧縮・PNG/WebP・リサイズ・プリセット・EXIF情報閲覧: 両方 ✅
• EXIF保持・レポートエクスポート・ファイル名変更: 無料版 ❌ / Pro版・トライアル ✅"""
        messagebox.showinfo("使い方", usage_text)
    
    def show_version_info(self):
        """バージョン情報を表示"""
        from version import __version__, COPYRIGHT, HOMEPAGE, SUPPORT_EMAIL
        info = self.license_manager.get_usage_info()
        trial_text = ""
        if info.get("is_trial"):
            trial_text = f"\n\nプレリリース: トライアル残り {info.get('remaining_trial_days', 0)} 日"
        elif not info.get("is_pro"):
            trial_text = "\n\nトライアル期間は終了しました。"
        messagebox.showinfo(
            "バージョン情報",
            f"PictComp v{__version__}\n\n{COPYRIGHT}\n\nホームページ:\n{HOMEPAGE}\n\nお問合せ先:\n{SUPPORT_EMAIL}{trial_text}\n\nPro版は準備中です。"
        )
    
    def setup_logging(self):
        """ログ設定"""
        log_dir = os.path.expanduser("~/.pictcomp/logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "app.log")
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def create_widgets(self):
        """ウィジェットを作成"""
        # ヘッダー（ロゴとアプリ名を左上に配置）
        header_frame = ttk.Frame(self.root, padding="10 5")
        header_frame.pack(fill=tk.X)
        
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "icon", "pictcomp_bright.jpg")
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                logo_img.thumbnail((84, 56), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                ttk.Label(header_frame, image=self.logo_photo).pack(side=tk.LEFT, padx=(0, 15))
            except Exception:
                pass
        ttk.Label(header_frame, text="PictComp - 画像一括圧縮アプリ", font=("", 14, "bold")).pack(side=tk.LEFT)
        
        # 区切り線
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 5))
        
        # === 下段: 縦分割（左: 設定、右: フォルダ・ファイル操作） ===
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # 左ペイン: プリセット・圧縮設定（スクロール可能）
        left_outer = ttk.Frame(paned, padding="5")
        paned.add(left_outer, weight=1)
        
        left_scrollbar = ttk.Scrollbar(left_outer)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        left_canvas = tk.Canvas(left_outer, yscrollcommand=left_scrollbar.set, highlightthickness=0)
        left_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        left_scrollbar.config(command=left_canvas.yview)
        
        left_frame = ttk.Frame(left_canvas, padding="10")
        left_canvas_window = left_canvas.create_window((0, 0), window=left_frame, anchor="nw")
        
        def _on_left_frame_configure(event):
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        def _on_left_canvas_configure(event):
            left_canvas.itemconfig(left_canvas_window, width=event.width)
        left_frame.bind("<Configure>", _on_left_frame_configure)
        left_canvas.bind("<Configure>", _on_left_canvas_configure)
        
        def _on_mousewheel_left(event):
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                left_canvas.yview_scroll(1, "units")   # 下へ
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                left_canvas.yview_scroll(-1, "units")  # 上へ
        left_canvas.bind("<MouseWheel>", _on_mousewheel_left)  # Windows
        left_canvas.bind("<Button-4>", _on_mousewheel_left)    # Linux
        left_canvas.bind("<Button-5>", _on_mousewheel_left)   # Linux
        
        # 右ペイン: フォルダ・ファイル一覧・ボタン
        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, weight=2)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(2, weight=1)  # ファイル一覧が伸縮
        
        # 左: プリセットセクション
        preset_frame = ttk.LabelFrame(left_frame, text="プリセット", padding="8")
        preset_frame.pack(fill=tk.X, pady=3)
        preset_frame.columnconfigure(1, weight=1)
        
        ttk.Label(preset_frame, text="プリセット:").grid(row=0, column=0, sticky=tk.W, padx=5)
        # カスタムを最後に配置
        preset_names = PresetManager.get_preset_names() + ["カスタム"]
        # 初期値をリストの最初のもの（PowerPoint用）に設定
        initial_preset = preset_names[0] if preset_names else "カスタム"
        self.preset_var = tk.StringVar(value=initial_preset)
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, values=preset_names, state="readonly", width=30)
        self.preset_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.preset_combo.bind("<<ComboboxSelected>>", self.apply_preset)
        ttk.Button(preset_frame, text="プレビュー", command=self.show_preview).grid(row=0, column=2, padx=5)
        
        # 設定変更時にカスタムに自動切り替えするためのフラグ
        self.preset_locked = False
        
        # 左: 設定セクション
        settings_frame = ttk.LabelFrame(left_frame, text="圧縮設定", padding="8")
        settings_frame.pack(fill=tk.X, pady=3)
        settings_frame.columnconfigure(1, weight=1)
        
        # 設定変更時にカスタムに自動切り替えする関数
        def switch_to_custom(*args):
            if not self.preset_locked and self.preset_var.get() != "カスタム":
                self.preset_var.set("カスタム")
                self._update_exif_checkbox_state()
        
        # 目標ファイルサイズ
        ttk.Label(settings_frame, text="目標サイズ (KB):").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.target_size_var = tk.IntVar(value=self.settings.target_size_kb)
        target_spinbox = ttk.Spinbox(settings_frame, from_=50, to=2000, textvariable=self.target_size_var, width=10)
        target_spinbox.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.target_size_var.trace("w", lambda *args: (setattr(self.settings, "target_size_kb", self.target_size_var.get()), switch_to_custom()))
        
        # リサイズ設定
        ttk.Label(settings_frame, text="最大サイズ (長辺px, 0=リサイズなし):").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.max_dim_var = tk.StringVar(value=str(self.settings.max_dimension) if self.settings.max_dimension else "0")
        max_dim_spinbox = ttk.Spinbox(settings_frame, from_=0, to=10000, textvariable=self.max_dim_var, width=10)
        max_dim_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.max_dim_var.trace("w", lambda *args: (setattr(self.settings, "max_dimension", int(self.max_dim_var.get()) if self.max_dim_var.get() != "0" else None), switch_to_custom()))
        
        # JPEG品質
        ttk.Label(settings_frame, text="JPEG品質:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.jpeg_quality_var = tk.IntVar(value=self.settings.jpeg_quality)
        quality_scale = ttk.Scale(settings_frame, from_=20, to=100, variable=self.jpeg_quality_var, orient=tk.HORIZONTAL, length=250)
        quality_scale.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.quality_label = ttk.Label(settings_frame, text=str(self.settings.jpeg_quality))
        self.quality_label.grid(row=2, column=2, padx=5)
        self.jpeg_quality_var.trace("w", lambda *args: (setattr(self.settings, "jpeg_quality", self.jpeg_quality_var.get()), self.quality_label.config(text=str(self.jpeg_quality_var.get())), switch_to_custom()))
        
        # 出力形式
        ttk.Label(settings_frame, text="出力形式:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.output_format_var = tk.StringVar(value=self.settings.output_format)
        format_combo = ttk.Combobox(settings_frame, textvariable=self.output_format_var, values=["auto", "jpg", "png", "webp"], state="readonly", width=10)
        format_combo.grid(row=3, column=1, sticky=tk.W, padx=5)
        format_combo.bind("<<ComboboxSelected>>", lambda e: (setattr(self.settings, "output_format", self.output_format_var.get()), switch_to_custom()))
        
        # 撮影情報の保持（Pro版限定、Web公開プリセット時は削除固定）
        self.exif_var = tk.BooleanVar(value=self.settings.keep_exif)
        self.exif_checkbtn = ttk.Checkbutton(settings_frame, text="撮影情報を残す（日付・カメラ情報など）", variable=self.exif_var)
        self.exif_checkbtn.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=3)
        self.exif_var.trace("w", lambda *args: (setattr(self.settings, "keep_exif", self.exif_var.get()), switch_to_custom()))
        self._exif_label_text = "撮影情報を残す（日付・カメラ情報など）"
        
        # WebP設定
        webp_frame = ttk.Frame(settings_frame)
        webp_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=3)
        webp_frame.columnconfigure(1, weight=1)
        
        ttk.Label(webp_frame, text="WebP品質:").grid(row=0, column=0, sticky=tk.W)
        self.webp_quality_var = tk.IntVar(value=self.settings.webp_quality)
        webp_quality_scale = ttk.Scale(webp_frame, from_=0, to=100, variable=self.webp_quality_var, orient=tk.HORIZONTAL, length=250)
        webp_quality_scale.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.webp_lossless_var = tk.BooleanVar(value=self.settings.webp_lossless)
        ttk.Checkbutton(webp_frame, text="可逆圧縮", variable=self.webp_lossless_var).grid(row=0, column=2, padx=5)
        self.webp_quality_var.trace("w", lambda *args: (setattr(self.settings, "webp_quality", self.webp_quality_var.get()), switch_to_custom()))
        self.webp_lossless_var.trace("w", lambda *args: (setattr(self.settings, "webp_lossless", self.webp_lossless_var.get()), switch_to_custom()))
        
        # 初期プリセットを適用（設定ウィジェット作成後に実行）
        if initial_preset != "カスタム":
            try:
                self.preset_locked = True
                preset_settings = PresetManager.apply_preset(initial_preset)
                self.settings = preset_settings
                self.compressor.settings = preset_settings
                self.target_size_var.set(preset_settings.target_size_kb)
                self.max_dim_var.set(str(preset_settings.max_dimension) if preset_settings.max_dimension else "0")
                self.jpeg_quality_var.set(preset_settings.jpeg_quality)
                self.output_format_var.set(preset_settings.output_format)
                self.exif_var.set(preset_settings.keep_exif)
                self.webp_quality_var.set(preset_settings.webp_quality)
                self.webp_lossless_var.set(preset_settings.webp_lossless)
                self.quality_label.config(text=str(preset_settings.jpeg_quality))
            except Exception as e:
                self.preset_var.set("カスタム")
            finally:
                self.preset_locked = False
        
        # EXIFチェックボックスの状態を更新（Web公開プリセット・Pro版に応じて）
        self._update_exif_checkbox_state()
        
        # 右: フォルダ選択セクション
        folder_frame = ttk.LabelFrame(right_frame, text="フォルダ選択", padding="10")
        folder_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(folder_frame, text="入力フォルダ:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=self.input_folder, width=40).grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="参照", command=self.select_input_folder).grid(row=0, column=2, padx=5)
        
        ttk.Label(folder_frame, text="出力フォルダ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(folder_frame, textvariable=self.output_folder, width=40).grid(row=1, column=1, padx=5)
        ttk.Button(folder_frame, text="参照", command=self.select_output_folder).grid(row=1, column=2, padx=5)
        folder_frame.columnconfigure(1, weight=1)
        
        # 右: ファイル一覧
        list_frame = ttk.LabelFrame(right_frame, text="対象ファイル（Ctrl+クリックで複数選択可）", padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # リストボックスとスクロールバー（複数選択可能）
        list_scrollbar = ttk.Scrollbar(list_frame)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox = tk.Listbox(list_frame, yscrollcommand=list_scrollbar.set, 
                                       height=8, selectmode=tk.EXTENDED)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_scrollbar.config(command=self.file_listbox.yview)
        
        # ダブルクリックで撮影情報を表示
        self.file_listbox.bind("<Double-Button-1>", self.show_exif_info)
        
        # 右: プログレスバー
        progress_frame = ttk.Frame(right_frame)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.progress_var = tk.StringVar(value="待機中")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack()
        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 右: ボタン（2行に分けて見切れ防止）
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=4, column=0, pady=10)
        button_frame.columnconfigure(0, weight=1)
        
        btn_row1 = ttk.Frame(button_frame)
        btn_row1.pack(fill=tk.X, pady=2)
        ttk.Button(btn_row1, text="ファイル一覧を更新", command=self.update_file_list).pack(side=tk.LEFT, padx=3)
        self.start_button = ttk.Button(btn_row1, text="圧縮開始", command=self.start_compression)
        self.start_button.pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row1, text="設定を保存", command=self.save_settings).pack(side=tk.LEFT, padx=3)
        
        btn_row2 = ttk.Frame(button_frame)
        btn_row2.pack(fill=tk.X, pady=2)
        self.export_report_btn = ttk.Button(btn_row2, text="レポートをエクスポート", command=self._export_report_or_show_pro_limit)
        self.export_report_btn.pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row2, text="撮影情報を表示", command=self.show_exif_info_from_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_row2, text="画像ビューアを開く", command=self.open_image_viewer).pack(side=tk.LEFT, padx=3)
        
        # 処理結果を保存する変数
        self.last_processing_results = []
        
        # 画像ビューア
        self.image_viewer = None
        
        # Pro版制限に応じてレポートボタンの状態を更新
        self._update_export_report_button_state()
        
        # ステータスバー（トライアル残り日数など）
        status_frame = ttk.Frame(self.root, padding="5 3")
        self.status_label = ttk.Label(status_frame, text="", font=("", 9))
        self.status_label.pack(side=tk.LEFT)
        self._update_status_bar()
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, side=tk.BOTTOM)
    
    def _update_status_bar(self):
        """ステータスバーにトライアル情報を表示"""
        info = self.license_manager.get_usage_info()
        if info.get("is_trial"):
            days = info.get("remaining_trial_days", 0)
            end_date = info.get("trial_end_date", "")
            self.status_label.config(text=f"プレリリース: トライアル残り {days} 日（期限: {end_date}）")
        elif info.get("is_pro"):
            self.status_label.config(text="Pro版")
        else:
            self.status_label.config(text=f"無料版（1回{info.get('per_batch_limit', 20)}枚まで）")
    
    def _check_trial_expired_on_startup(self):
        """起動時にトライアル期限切れをチェックして通知"""
        if not self.license_manager.is_trial_active() and self.license_manager.get_usage_data().get("license_type") != "pro":
            messagebox.showinfo(
                "トライアル期間終了",
                "14日間のプレリリーストライアル期間が終了しました。\n\n"
                "引き続きご利用いただくには、無料版としてご利用ください（1回20枚まで）。\n"
                "Pro版（無制限・EXIF保持・レポート）は準備中です。"
            )
    
    def _update_exif_checkbox_state(self):
        """EXIFチェックボックスの有効/無効をプリセットとPro版に応じて更新"""
        preset_name = self.preset_var.get()
        is_pro = self.license_manager.check_license()
        is_web_preset = PresetManager.is_web_publishing_preset(preset_name)
        
        if is_web_preset:
            # Web公開プリセット: EXIF削除固定
            self.exif_var.set(False)
            self.settings.keep_exif = False
            self.exif_checkbtn.config(state="disabled", text=f"{self._exif_label_text}（Web公開用のため削除固定）")
        elif not is_pro:
            # 無料版: Pro版限定（EXIF削除に固定）
            self.exif_var.set(False)
            self.settings.keep_exif = False
            self.exif_checkbtn.config(state="disabled", text=f"{self._exif_label_text}（Pro版限定）")
        else:
            # Pro版かつ非Webプリセット: 通常選択可
            self.exif_checkbtn.config(state="normal", text=self._exif_label_text)
    
    def _update_export_report_button_state(self):
        """レポートエクスポートボタンの有効/無効をPro版に応じて更新"""
        is_pro = self.license_manager.check_license()
        if not is_pro:
            self.export_report_btn.config(state="disabled", text="レポートをエクスポート（Pro版限定）")
        else:
            self.export_report_btn.config(state="normal", text="レポートをエクスポート")
    
    def _export_report_or_show_pro_limit(self):
        """レポートエクスポート（Pro版のみ）"""
        if not self.license_manager.check_license():
            messagebox.showinfo("Pro版限定", "レポートのエクスポート（CSV/JSON）はPro版の機能です。")
            return
        self.export_report()
    
    def select_input_folder(self):
        """入力フォルダを選択"""
        folder = filedialog.askdirectory(title="入力フォルダを選択してください")
        if folder:
            self.input_folder.set(folder)
            self.update_file_list()
            self._save_last_folders()
    
    def select_output_folder(self):
        """出力フォルダを選択"""
        folder = filedialog.askdirectory(title="出力フォルダを選択してください")
        if folder:
            self.output_folder.set(folder)
            os.makedirs(folder, exist_ok=True)
            self._save_last_folders()
    
    def _save_last_folders(self):
        """前回使用したフォルダパスを保存"""
        input_path = self.input_folder.get()
        output_path = self.output_folder.get()
        if input_path or output_path:
            self.config_manager.save_last_folders(
                input_path or "",
                output_path or ""
            )
    
    def update_file_list(self):
        """ファイル一覧を更新"""
        self.file_listbox.delete(0, tk.END)
        input_path = self.input_folder.get()
        if not input_path or not os.path.exists(input_path):
            return
        
        supported_extensions = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
        files = [f for f in os.listdir(input_path) 
                if os.path.isfile(os.path.join(input_path, f)) 
                and os.path.splitext(f)[1].lower() in supported_extensions]
        
        for file in files:
            self.file_listbox.insert(tk.END, file)
    
    def load_last_settings(self):
        """前回設定を読み込み（フォルダパスの復元）"""
        input_folder, output_folder = self.config_manager.load_last_folders()
        if input_folder and os.path.exists(input_folder):
            self.input_folder.set(input_folder)
            self.update_file_list()
        if output_folder and os.path.exists(output_folder):
            self.output_folder.set(output_folder)
    
    def apply_preset(self, event=None):
        """プリセットを適用"""
        preset_name = event.widget.get()
        if preset_name == "カスタム":
            self.preset_locked = False
            self._update_exif_checkbox_state()
            return
        
        try:
            self.preset_locked = True  # プリセット適用中はロック
            preset_settings = PresetManager.apply_preset(preset_name)
            # 現在の設定をプリセットで上書き
            self.settings = preset_settings
            self.compressor.settings = preset_settings
            
            # GUIの各設定項目を更新（ロック中なので自動切り替えしない）
            self.target_size_var.set(preset_settings.target_size_kb)
            self.max_dim_var.set(str(preset_settings.max_dimension) if preset_settings.max_dimension else "0")
            self.jpeg_quality_var.set(preset_settings.jpeg_quality)
            self.output_format_var.set(preset_settings.output_format)
            # Web公開プリセットの場合はEXIF削除を強制
            if PresetManager.is_web_publishing_preset(preset_name):
                preset_settings.keep_exif = False
                self.settings.keep_exif = False
            self.exif_var.set(preset_settings.keep_exif)
            self.webp_quality_var.set(preset_settings.webp_quality)
            self.webp_lossless_var.set(preset_settings.webp_lossless)
            self.quality_label.config(text=str(preset_settings.jpeg_quality))
            
            self._update_exif_checkbox_state()
            self.preset_locked = False  # ロック解除
        except Exception as e:
            self.preset_locked = False
            messagebox.showerror("エラー", f"プリセット適用エラー: {str(e)}")
    
    def show_preview(self):
        """プレビューウィンドウを表示"""
        input_path = self.input_folder.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("警告", "入力フォルダを選択してください")
            return
        
        # 最初の画像ファイルを取得
        supported_extensions = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
        files = [f for f in os.listdir(input_path) 
                if os.path.isfile(os.path.join(input_path, f)) 
                and os.path.splitext(f)[1].lower() in supported_extensions]
        
        if not files:
            messagebox.showwarning("警告", "プレビュー対象のファイルがありません")
            return
        
        preview_file = os.path.join(input_path, files[0])
        self.open_preview_window(preview_file)
    
    def open_preview_window(self, image_path: str):
        """プレビューウィンドウを開く"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("プレビュー - 圧縮前後の比較")
        preview_window.geometry("1000x600")
        
        # 元画像を読み込み
        try:
            if image_path.lower().endswith(".heic"):
                heif_file = pillow_heif.read_heif(image_path)
                original_img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            else:
                original_img = Image.open(image_path)
            
            # リサイズして表示用に準備
            display_size = (400, 300)
            original_display = original_img.copy()
            original_display.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # 圧縮をシミュレート（実際の圧縮は行わない）
            temp_settings = CompressionSettings()
            temp_settings.target_size_kb = self.settings.target_size_kb
            temp_settings.max_dimension = self.settings.max_dimension
            temp_settings.jpeg_quality = self.settings.jpeg_quality
            
            temp_compressor = ImageCompressor(temp_settings)
            resized_img = temp_compressor.resize_image(original_img.copy())
            
            # 圧縮後のサイズを推定（簡易版）
            import io
            temp_buffer = io.BytesIO()
            resized_img.save(temp_buffer, format="JPEG", quality=self.settings.jpeg_quality)
            compressed_size = len(temp_buffer.getvalue())
            original_size = os.path.getsize(image_path)
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
            
            compressed_display = resized_img.copy()
            compressed_display.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            # 画像を表示
            frame = ttk.Frame(preview_window, padding="10")
            frame.pack(fill=tk.BOTH, expand=True)
            
            # 元画像
            original_label = ttk.Label(frame, text="元画像")
            original_label.grid(row=0, column=0, padx=10)
            original_photo = ImageTk.PhotoImage(original_display)
            original_img_label = ttk.Label(frame, image=original_photo)
            original_img_label.image = original_photo  # 参照を保持
            original_img_label.grid(row=1, column=0, padx=10)
            ttk.Label(frame, text=f"サイズ: {original_size / 1024:.1f} KB").grid(row=2, column=0)
            
            # 圧縮後画像
            compressed_label = ttk.Label(frame, text="圧縮後（推定）")
            compressed_label.grid(row=0, column=1, padx=10)
            compressed_photo = ImageTk.PhotoImage(compressed_display)
            compressed_img_label = ttk.Label(frame, image=compressed_photo)
            compressed_img_label.image = compressed_photo  # 参照を保持
            compressed_img_label.grid(row=1, column=1, padx=10)
            ttk.Label(frame, text=f"サイズ: {compressed_size / 1024:.1f} KB\n削減率: {compression_ratio:.1f}%").grid(row=2, column=1)
            
        except Exception as e:
            messagebox.showerror("エラー", f"プレビュー表示エラー: {str(e)}")
            preview_window.destroy()
    
    def save_settings(self):
        """設定を保存"""
        self.config_manager.save_settings(self.settings)
        messagebox.showinfo("設定", "設定を保存しました")
    
    def export_report(self):
        """レポートをエクスポート（CSV/JSON形式）"""
        if not hasattr(self, 'last_processing_results') or not self.last_processing_results:
            messagebox.showwarning("警告", "エクスポートする処理結果がありません。まず圧縮処理を実行してください。")
            return
        
        # エクスポート形式を選択
        export_window = tk.Toplevel(self.root)
        export_window.title("レポートエクスポート")
        export_window.geometry("400x150")
        
        ttk.Label(export_window, text="エクスポート形式を選択してください:").pack(pady=10)
        
        format_var = tk.StringVar(value="csv")
        ttk.Radiobutton(export_window, text="CSV形式", variable=format_var, value="csv").pack()
        ttk.Radiobutton(export_window, text="JSON形式", variable=format_var, value="json").pack()
        
        def do_export():
            export_format = format_var.get()
            export_window.destroy()
            
            # 保存先を選択
            if export_format == "csv":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )
            else:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
                )
            
            if not file_path:
                return
            
            try:
                if export_format == "csv":
                    import csv
                    with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                        writer = csv.DictWriter(f, fieldnames=[
                            "ファイル名", "成功", "元のサイズ (bytes)", "圧縮後サイズ (bytes)", 
                            "削減率 (%)", "処理時間 (秒)", "エラー", "形式"
                        ])
                        writer.writeheader()
                        for result in self.last_processing_results:
                            writer.writerow({
                                "ファイル名": result["filename"],
                                "成功": "はい" if result["success"] else "いいえ",
                                "元のサイズ (bytes)": result["input_size"],
                                "圧縮後サイズ (bytes)": result["output_size"],
                                "削減率 (%)": f"{result['compression_ratio']:.2f}",
                                "処理時間 (秒)": f"{result['processing_time']:.3f}",
                                "エラー": result.get("error", ""),
                                "形式": result.get("format", "unknown")
                            })
                        # サマリーを追加
                        if hasattr(self, 'last_processing_summary'):
                            summary = self.last_processing_summary
                            writer.writerow({})
                            writer.writerow({
                                "ファイル名": "=== サマリー ===",
                                "成功": f"{summary['success_count']}/{summary['total_files']}",
                                "元のサイズ (bytes)": summary["total_input_size"],
                                "圧縮後サイズ (bytes)": summary["total_output_size"],
                                "削減率 (%)": f"{summary['compression_ratio']:.2f}",
                                "処理時間 (秒)": f"{summary['processing_time']:.2f}",
                                "エラー": f"平均処理時間: {summary['average_time_per_file']:.3f}秒/ファイル"
                            })
                else:
                    import json
                    export_data = {
                        "summary": self.last_processing_summary if hasattr(self, 'last_processing_summary') else {},
                        "results": self.last_processing_results
                    }
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("成功", f"レポートをエクスポートしました:\n{file_path}")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポートエラー: {str(e)}")
    
    def open_image_viewer(self):
        """画像ビューアを開く"""
        input_path = self.input_folder.get()
        if not input_path or not os.path.exists(input_path):
            messagebox.showwarning("警告", "入力フォルダを選択してください")
            return
        
        if not self.image_viewer:
            self.image_viewer = ImageViewer(self.root, exif_callback=self.show_exif_info_window)
        
        self.image_viewer.open_viewer(input_path)
    
    def show_exif_info_from_selection(self, event=None):
        """選択されたファイルのEXIF情報を表示"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "ファイルを選択してください")
            return
        
        filename = self.file_listbox.get(selection[0])
        input_path = self.input_folder.get()
        if not input_path:
            messagebox.showwarning("警告", "入力フォルダを選択してください")
            return
        
        file_path = os.path.join(input_path, filename)
        if not os.path.exists(file_path):
            messagebox.showerror("エラー", "ファイルが見つかりません")
            return
        
        self.show_exif_info_window(file_path, filename)
    
    def show_exif_info(self, event=None):
        """ダブルクリックでEXIF情報を表示"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        filename = self.file_listbox.get(selection[0])
        input_path = self.input_folder.get()
        if not input_path:
            return
        
        file_path = os.path.join(input_path, filename)
        if not os.path.exists(file_path):
            return
        
        self.show_exif_info_window(file_path, filename)
    
    def show_exif_info_window(self, file_path: str, filename: str):
        """EXIF情報表示ウィンドウを開く（表形式）"""
        exif_window = tk.Toplevel(self.root)
        exif_window.title(f"撮影情報 - {filename}")
        exif_window.geometry("800x550")
        
        # EXIFデータを取得
        exif_data = ExifViewer.get_exif_data(file_path)
        
        # メインフレーム
        main_frame = ttk.Frame(exif_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        if not exif_data or "error" in exif_data:
            if "error" in exif_data:
                ttk.Label(main_frame, text=f"エラー: {exif_data['error']}", foreground="red").pack(pady=10)
            else:
                ttk.Label(main_frame, text="⚠️ この画像には撮影情報が含まれていません。", foreground="orange").pack(pady=10)
            
            # 撮影情報がない場合の説明
            info_frame = ttk.LabelFrame(main_frame, text="撮影情報とは？", padding="10")
            info_frame.pack(fill=tk.X, padx=10, pady=10)
            
            info_text = """カメラが記録したデータ（撮影日時・カメラ機種など）です。
スクショや編集済み画像には含まれないことがあります。

使えない機能：
• 撮影日時でのファイル名変更
• ファイル日時の更新
• 撮影情報の表示"""
            ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)
            
            # ログに記録
            logging.warning(f"⚠️ {filename}: EXIF情報がないため、EXIF関連機能は使用できません")
            
            ttk.Button(main_frame, text="閉じる", command=exif_window.destroy).pack(pady=10)
            return
        
        # メタデータ表示（サマリーと詳細を統合）
        tree_frame = ttk.Frame(main_frame, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar_y = ttk.Scrollbar(tree_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        tree = ttk.Treeview(tree_frame, columns=("カテゴリ", "項目", "値"), show="headings", 
                           yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        tree.heading("カテゴリ", text="カテゴリ")
        tree.heading("項目", text="項目")
        tree.heading("値", text="値")
        tree.column("カテゴリ", width=150, minwidth=120)
        tree.column("項目", width=250, minwidth=200)
        tree.column("値", width=450, minwidth=300)
        
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # サマリーデータを追加
        summary_data = ExifViewer.get_exif_summary(exif_data)
        for category, item, value in summary_data:
            tree.insert("", tk.END, values=(category, item, value))
        
        # 詳細データも追加（サマリーにないもののみ）
        filtered_exif = {k: v for k, v in exif_data.items() if not k.startswith("_")}
        all_data = ExifViewer.get_all_exif_data(filtered_exif)
        summary_tags = {item for _, item, _ in summary_data}
        
        # セパレータ
        tree.insert("", tk.END, values=("---", "---", "---"))
        tree.insert("", tk.END, values=("詳細情報", "", ""))
        
        for tag, value in all_data:
            # サマリーに含まれていないタグのみ追加
            if tag not in summary_tags:
                tree.insert("", tk.END, values=("詳細情報", tag, value))
        
        # GPS情報がある場合は追加
        if "GPSInfo" in exif_data and isinstance(exif_data["GPSInfo"], dict):
            tree.insert("", tk.END, values=("---", "---", "---"))
            tree.insert("", tk.END, values=("GPS情報", "", ""))
            gps_info = exif_data["GPSInfo"]
            coordinates = ExifViewer.format_gps_coordinates(gps_info)
            if coordinates:
                tree.insert("", tk.END, values=("GPS情報", "座標", coordinates))
            for tag, value in sorted(gps_info.items()):
                formatted_value = ExifViewer.format_exif_value(value)
                tree.insert("", tk.END, values=("GPS情報", tag, formatted_value))
        
        # ボタン
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        def copy_to_clipboard():
            """EXIF情報をクリップボードにコピー"""
            filtered_exif = {k: v for k, v in exif_data.items() if not k.startswith("_")}
            all_data = ExifViewer.get_all_exif_data(filtered_exif)
            text = "\n".join(f"{tag}: {value}" for tag, value in all_data)
            exif_window.clipboard_clear()
            exif_window.clipboard_append(text)
            messagebox.showinfo("コピー", "撮影情報をクリップボードにコピーしました")
        
        # ファイル日時更新機能
        def update_file_date():
            """撮影日時に基づいてファイルの作成日時を更新"""
            # 撮影日時を取得（優先順位: DateTimeOriginal > DateTimeDigitized > DateTime）
            shoot_date = None
            if "DateTimeOriginal" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTimeOriginal"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except Exception as e:
                    print(f"DateTimeOriginal parse error: {e}")
                    pass
            
            if not shoot_date and "DateTimeDigitized" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTimeDigitized"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except Exception as e:
                    print(f"DateTimeDigitized parse error: {e}")
                    pass
            
            if not shoot_date and "DateTime" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTime"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except Exception as e:
                    print(f"DateTime parse error: {e}")
                    pass
            
            if not shoot_date:
                messagebox.showwarning("警告", "撮影日時情報が見つかりません。")
                return
            
            # 確認ダイアログ
            result = messagebox.askyesno(
                "確認",
                f"ファイルの作成日時を撮影日時 ({shoot_date.strftime('%Y-%m-%d %H:%M:%S')}) に更新しますか？\n\n"
                f"ファイル: {filename}"
            )
            
            if result:
                try:
                    import time
                    timestamp = shoot_date.timestamp()
                    os.utime(file_path, (timestamp, timestamp))
                    messagebox.showinfo("成功", "ファイルの作成日時と更新日時を更新しました。")
                    # ウィンドウを閉じて再表示
                    exif_window.destroy()
                    self.show_exif_info_window(file_path, filename)
                except Exception as e:
                    messagebox.showerror("エラー", f"ファイル日時の更新に失敗しました:\n{str(e)}")
        
        # ファイル名変更機能
        def rename_file_by_shoot_date():
            """撮影日時に基づいてファイル名を変更"""
            # 撮影日時を取得
            shoot_date = None
            if "DateTimeOriginal" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTimeOriginal"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except:
                    pass
            
            if not shoot_date and "DateTimeDigitized" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTimeDigitized"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except:
                    pass
            
            if not shoot_date and "DateTime" in exif_data:
                try:
                    shoot_date_str = exif_data["DateTime"]
                    if isinstance(shoot_date_str, str):
                        shoot_date = datetime.strptime(shoot_date_str, "%Y:%m:%d %H:%M:%S")
                except:
                    pass
            
            if not shoot_date:
                messagebox.showwarning("警告", "撮影日時情報が見つかりません。")
                return
            
            # 新しいファイル名を生成
            name, ext = os.path.splitext(filename)
            base_filename = f"{shoot_date.strftime('%Y%m%d_%H%M%S')}{ext}"
            new_file_path = os.path.join(os.path.dirname(file_path), base_filename)
            
            # 既に同名ファイルが存在する場合、または元のファイル名と同じになる場合
            # 必ず連番を付与して識別可能にする
            if os.path.exists(new_file_path) or new_file_path == file_path:
                counter = 1
                while True:
                    new_filename = f"{shoot_date.strftime('%Y%m%d_%H%M%S')}_{counter:03d}{ext}"
                    new_file_path = os.path.join(os.path.dirname(file_path), new_filename)
                    # 存在しないファイル名が見つかるまで、または元のファイルと異なるまで
                    if not os.path.exists(new_file_path) and new_file_path != file_path:
                        break
                    counter += 1
                    # 無限ループ防止（999まで）
                    if counter > 999:
                        messagebox.showerror("エラー", "利用可能なファイル名が見つかりません。")
                        return
            else:
                new_filename = base_filename
            
            # 確認ダイアログ
            result = messagebox.askyesno(
                "確認",
                f"ファイル名を変更しますか？\n\n"
                f"現在: {filename}\n"
                f"変更後: {new_filename}"
            )
            
            if result:
                try:
                    os.rename(file_path, new_file_path)
                    messagebox.showinfo("成功", f"ファイル名を変更しました。\n\n{new_filename}")
                    # ウィンドウを閉じて再表示
                    exif_window.destroy()
                    self.show_exif_info_window(new_file_path, new_filename)
                    # ファイル一覧を更新
                    self.update_file_list()
                except Exception as e:
                    messagebox.showerror("エラー", f"ファイル名の変更に失敗しました:\n{str(e)}")
        
        ttk.Button(button_frame, text="撮影日時に合わせてファイル日時を更新", command=update_file_date).pack(side=tk.LEFT, padx=5)
        def rename_or_show_pro_limit():
            if not self.license_manager.check_license():
                messagebox.showinfo("Pro版限定", "撮影日時に基づくファイル名変更はPro版の機能です。")
                return
            rename_file_by_shoot_date()
        ttk.Button(button_frame, text="撮影日時に合わせてファイル名を変更", command=rename_or_show_pro_limit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="クリップボードにコピー", command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="閉じる", command=exif_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def start_compression(self):
        """圧縮を開始"""
        if self.processing:
            messagebox.showwarning("警告", "処理中です。しばらくお待ちください。")
            return
        
        input_path = self.input_folder.get()
        output_path = self.output_folder.get()
        
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("エラー", "入力フォルダを選択してください")
            return
        
        if not output_path:
            messagebox.showerror("エラー", "出力フォルダを選択してください")
            return
        
        os.makedirs(output_path, exist_ok=True)
        self._save_last_folders()
        
        # 選択されたファイルを取得
        selected_indices = self.file_listbox.curselection()
        
        # 圧縮エンジンの設定を更新
        self.compressor.settings = self.settings
        
        # 別スレッドで処理
        thread = threading.Thread(target=self.process_images, args=(input_path, output_path, selected_indices))
        thread.daemon = True
        thread.start()
    
    def process_images(self, input_path: str, output_path: str, selected_indices: tuple = None):
        """画像を処理（別スレッドで実行）"""
        import time
        self.processing = True
        self.start_button.config(state="disabled")
        start_time = time.time()
        
        try:
            # 対象ファイルを取得
            supported_extensions = [".jpg", ".jpeg", ".png", ".heic", ".webp"]
            all_files = [f for f in os.listdir(input_path) 
                        if os.path.isfile(os.path.join(input_path, f)) 
                        and os.path.splitext(f)[1].lower() in supported_extensions]
            
            # 選択されたファイルがある場合は、それらのみ処理
            if selected_indices:
                selected_files = [self.file_listbox.get(i) for i in selected_indices]
                # ファイル名のみを抽出（表示テキストから）
                selected_filenames = []
                for display_text in selected_files:
                    # "[!] "プレフィックスを除去
                    if display_text.startswith("[!] "):
                        display_text = display_text[4:]
                    # ファイル名部分を抽出（" | "で分割）
                    filename = display_text.split(" | ")[0]
                    selected_filenames.append(filename)
                files = [f for f in all_files if f in selected_filenames]
            else:
                files = all_files
            
            total_files = len(files)
            if total_files == 0:
                self.root.after(0, lambda: messagebox.showwarning("警告", "処理対象のファイルがありません"))
                return
            
            # 無料版の制限チェック（1回20枚まで）
            limit = self.license_manager.FREE_LIMIT_PER_BATCH
            is_pro = self.license_manager.check_license()
            if not is_pro and total_files > limit:
                self.root.after(0, lambda: messagebox.showwarning(
                    "無料版の制限",
                    f"無料版は1回{limit}枚までです。\n先頭{limit}枚のみ処理します。\nPro版で無制限にご利用いただけます。"
                ))
                files = files[:limit]
                total_files = len(files)
            
            # プログレスバー設定
            self.root.after(0, lambda: self.progress_bar.config(maximum=total_files))
            
            success_count = 0
            total_input_size = 0
            total_output_size = 0
            self.last_processing_results = []
            
            for idx, filename in enumerate(files):
                file_path = os.path.join(input_path, filename)
                output_file_path = os.path.join(output_path, filename)
                file_start_time = time.time()
                
                # プログレス更新
                self.root.after(0, lambda i=idx+1, f=filename: self.progress_var.set(f"処理中: {f} ({i}/{total_files})"))
                self.root.after(0, lambda i=idx+1: self.progress_bar.config(value=i))
                
                # 出力形式を取得して拡張子を変更
                output_format = self.settings.output_format
                if output_format == "auto":
                    # 自動判定: 入力形式に合わせる
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in [".jpg", ".jpeg", ".heic"]:
                        output_format = "jpg"
                    elif ext == ".png":
                        output_format = "png"
                    else:
                        output_format = "jpg"
                
                # 出力ファイル名の拡張子を変更
                name, original_ext = os.path.splitext(output_file_path)
                if output_format == "jpg":
                    output_file_path = f"{name}.jpg"
                elif output_format == "png":
                    output_file_path = f"{name}.png"
                elif output_format == "webp":
                    output_file_path = f"{name}.webp"
                
                # 圧縮実行
                success, result = self.compressor.compress_image(file_path, output_file_path)
                file_processing_time = time.time() - file_start_time
                
                # 実際の出力パスを取得（compress_imageが返す実際のパスを使用）
                if success and "output_path" in result:
                    actual_output_path = result["output_path"]
                    # 実際の出力パスにファイルを移動（必要に応じて）
                    if actual_output_path != output_file_path and os.path.exists(actual_output_path):
                        import shutil
                        shutil.move(actual_output_path, output_file_path)
                    actual_filename = os.path.basename(output_file_path)
                else:
                    actual_filename = filename
                
                # EXIF情報の確認とログ記録
                has_exif = False
                if success:
                    try:
                        exif_data = ExifViewer.get_exif_data(file_path)
                        has_exif = exif_data and "error" not in exif_data
                        if not has_exif:
                            logging.warning(f"⚠️ {filename}: EXIF情報がないため、EXIF関連機能は使用できません")
                    except:
                        pass
                
                result_record = {
                    "filename": actual_filename,  # 実際の出力ファイル名を使用
                    "original_filename": filename,  # 元のファイル名も保存
                    "success": success,
                    "input_size": result.get("input_size", 0),
                    "output_size": result.get("output_size", 0),
                    "compression_ratio": result.get("compression_ratio", 0),
                    "processing_time": file_processing_time,
                    "error": result.get("error"),
                    "format": result.get("format", "unknown"),
                    "has_exif": has_exif  # EXIF情報の有無を記録
                }
                self.last_processing_results.append(result_record)
                
                if success:
                    success_count += 1
                    total_input_size += result["input_size"]
                    total_output_size += result["output_size"]
                    logging.info(f"圧縮成功: {filename} - {result['compression_ratio']:.1f}%削減 ({file_processing_time:.2f}秒)")
                else:
                    logging.error(f"圧縮失敗: {filename} - {result.get('error', 'Unknown error')}")
            
            total_processing_time = time.time() - start_time
            compression_ratio = (1 - total_output_size / total_input_size) * 100 if total_input_size > 0 else 0
            
            # 処理結果を保存
            self.last_processing_summary = {
                "total_files": total_files,
                "success_count": success_count,
                "failed_count": total_files - success_count,
                "total_input_size": total_input_size,
                "total_output_size": total_output_size,
                "compression_ratio": compression_ratio,
                "processing_time": total_processing_time,
                "average_time_per_file": total_processing_time / total_files if total_files > 0 else 0
            }
            
            # 完了メッセージ
            message = f"処理完了\n成功: {success_count}/{total_files}\n"
            message += f"合計サイズ削減: {compression_ratio:.1f}%\n"
            message += f"処理時間: {total_processing_time:.2f}秒"
            
            self.root.after(0, lambda: (
                self.progress_var.set("完了"),
                messagebox.showinfo("完了", message),
                self.start_button.config(state="normal")
            ))
            
        except Exception as e:
            logging.error(f"処理エラー: {e}")
            self.root.after(0, lambda: (
                messagebox.showerror("エラー", f"処理中にエラーが発生しました: {str(e)}"),
                self.start_button.config(state="normal")
            ))
        finally:
            self.processing = False


def main():
    """メイン関数"""
    root = tk.Tk()
    app = PictCompGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

