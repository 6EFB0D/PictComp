# -*- coding: utf-8 -*-
"""
Streamlit版Webアプリ
ブラウザで動作する画像圧縮アプリ
GUI版の機能をWeb版に展開
"""
import streamlit as st
import os
from pathlib import Path
import zipfile
import io
import json
import time
import tempfile
import hashlib
from datetime import datetime
from image_compressor import ImageCompressor, CompressionSettings
from presets import PresetManager
from license_manager import LicenseManager
from exif_viewer import ExifViewer
from PIL import Image
import pillow_heif
import pandas as pd


# ページ設定（サイドバー非表示で上段全幅＋下段縦分割）
st.set_page_config(
    page_title="PictComp - 画像一括圧縮",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ライセンス管理
license_manager = LicenseManager()

# プロジェクト情報・ロゴ（背景に合わせて bright=明るい背景 / dark=暗い背景）
from version import COPYRIGHT, HOMEPAGE, SUPPORT_EMAIL
LOGO_PATH = Path(__file__).parent / "assets" / "icon" / "pictcomp_bright.jpg"  # 明るい背景向け


def sanitize_filename(filename):
    """ファイル名を安全な形式に変換"""
    # ファイル名から危険な文字を削除
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        # ファイル名が空の場合はハッシュを使用
        safe_name = hashlib.md5(filename.encode()).hexdigest()
    return safe_name


def get_temp_file_path(filename, prefix="temp"):
    """一時ファイルのパスを安全に生成"""
    # システムの一時ディレクトリを使用
    temp_dir = Path(tempfile.gettempdir()) / "pictcomp_web"
    temp_dir.mkdir(exist_ok=True)
    
    # ファイル名をサニタイズ
    safe_name = sanitize_filename(filename)
    # タイムスタンプを追加して重複を避ける
    timestamp = int(time.time() * 1000000)
    return temp_dir / f"{prefix}_{timestamp}_{safe_name}"


def display_exif_info(image_bytes, filename):
    """EXIF情報を表示（統合版）"""
    # 一時ファイルに保存してEXIF情報を取得
    temp_path = get_temp_file_path(filename, "exif")
    try:
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        
        exif_data = ExifViewer.get_exif_data(str(temp_path))
        
        if not exif_data or "error" in exif_data:
            st.warning("⚠️ **この画像にはEXIF情報が含まれていません。**")
            st.info("""
            **EXIF情報がない場合の影響:**
            - ファイル名変更機能（撮影日時に基づく）は適用されません
            - EXIF情報の表示はできません
            - ファイル日時の更新はできません
            
            ログファイル（`streamlit_debug.log`）に詳細が記録されます。
            """)
            
            # ログに記録
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"⚠️ EXIF情報なし: {filename} - EXIF関連機能は使用できません")
            return
        
        # すべてのEXIF情報を統合して表示
        filtered_exif = {k: v for k, v in exif_data.items() if not k.startswith("_")}
        all_data = ExifViewer.get_all_exif_data(filtered_exif)
        
        if all_data:
            # カテゴリごとにグループ化
            exif_list = []
            for tag, value in all_data:
                # タグ名からカテゴリを推測
                category = "その他"
                if any(x in tag.lower() for x in ["date", "time", "datetime"]):
                    category = "日時情報"
                elif any(x in tag.lower() for x in ["camera", "make", "model", "lens"]):
                    category = "カメラ情報"
                elif any(x in tag.lower() for x in ["exposure", "iso", "aperture", "focal", "shutter"]):
                    category = "撮影設定"
                elif any(x in tag.lower() for x in ["gps", "location", "latitude", "longitude"]):
                    category = "位置情報"
                elif any(x in tag.lower() for x in ["width", "height", "resolution", "orientation"]):
                    category = "画像情報"
                elif any(x in tag.lower() for x in ["file", "size", "format"]):
                    category = "ファイル情報"
                
                exif_list.append({
                    "カテゴリ": category,
                    "項目": tag,
                    "値": value
                })
            
            exif_df = pd.DataFrame(exif_list)
            st.dataframe(exif_df, width='stretch', hide_index=True)
        else:
            st.info("EXIF情報が取得できませんでした。")
        
    except Exception as e:
        st.error(f"EXIF情報の取得中にエラーが発生しました: {str(e)}")
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except:
            pass


def generate_filename_from_exif(image_bytes, filename, original_name, output_format=None):
    """EXIF情報からファイル名を生成
    
    Args:
        image_bytes: 画像のバイトデータ
        filename: ファイル名
        original_name: 元のファイル名
        output_format: 出力形式（"jpg", "png", "webp"など）
    
    Returns:
        tuple: (新しいファイル名, EXIF情報が存在したかどうか)
    """
    temp_path = get_temp_file_path(filename, "rename")
    has_exif = False
    
    try:
        with open(temp_path, "wb") as f:
            f.write(image_bytes)
        
        exif_data = ExifViewer.get_exif_data(str(temp_path))
        
        if not exif_data or "error" in exif_data:
            # EXIF情報がない場合
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"⚠️ EXIF情報なし: {original_name} - ファイル名変更は適用されません")
            return original_name, False
        
        has_exif = True
        
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
        
        if shoot_date:
            name, ext = os.path.splitext(original_name)
            # 出力形式に応じて拡張子を変更
            if output_format:
                if output_format == "jpg":
                    ext = ".jpg"
                elif output_format == "png":
                    ext = ".png"
                elif output_format == "webp":
                    ext = ".webp"
            
            new_filename = f"{shoot_date.strftime('%Y%m%d_%H%M%S')}{ext}"
            
            # ログに記録
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"✅ EXIF情報あり: {original_name} -> {new_filename} (撮影日時: {shoot_date.strftime('%Y-%m-%d %H:%M:%S')})")
            
            return new_filename, True
        
        # EXIF情報はあるが撮影日時がない場合
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"⚠️ EXIF情報あり（撮影日時なし）: {original_name} - ファイル名変更は適用されません")
        return original_name, False
        
    except Exception as e:
        # エラーが発生した場合は元のファイル名を返す
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"❌ EXIF情報取得エラー: {original_name} - {str(e)}")
        return original_name, False
    finally:
        try:
            if temp_path.exists():
                temp_path.unlink()
        except:
            pass


def main():
    # === カスタムCSS: タブ拡大・左ペイン余白・ヘッダー固定・左右ペイン独立スクロール ===
    st.markdown("""
    <style>
        /* タブをもう一段大きくする */
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 1.4rem !important;
            padding: 0.75rem 1.5rem !important;
        }
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.4rem !important;
        }
        /* ヘッダー固定＋コンパクトに（余白削減） */
        div[data-testid="stVerticalBlock"]:has(div.fixed-header) {
            position: sticky;
            top: 0;
            background-color: var(--background-color, #ffffff);
            z-index: 999;
            padding-top: 0.5rem !important;
            padding-bottom: 0.25rem !important;
        }
        div[data-testid="stVerticalBlock"]:has(div.fixed-header) [data-testid="stHorizontalBlock"] {
            padding-bottom: 0 !important;
        }
        /* ヘッダー内の要素をコンパクトに */
        div[data-testid="stVerticalBlock"]:has(div.fixed-header) .stMarkdown {
            margin-bottom: 0 !important;
        }
        div[data-testid="stVerticalBlock"]:has(div.fixed-header) hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        /* 左右ペインを独立してスクロール可能に（高さを最大限確保） */
        div[data-testid="stVerticalBlock"]:has(div.scrollable-panes-marker) {
            max-height: calc(100vh - 80px) !important;
            overflow: hidden !important;
        }
        div[data-testid="stVerticalBlock"]:has(div.scrollable-panes-marker) [data-testid="stHorizontalBlock"] {
            max-height: calc(100vh - 80px) !important;
            overflow: hidden !important;
        }
        /* 左右カラムそれぞれ独立スクロール */
        div[data-testid="stVerticalBlock"]:has(div.scrollable-panes-marker) [data-testid="stHorizontalBlock"] > div {
            overflow-y: auto !important;
            overflow-x: hidden !important;
            max-height: calc(100vh - 80px) !important;
            min-height: 0 !important;  /* flex子要素でoverflowを効かせる */
            padding-bottom: 120px !important;  /* スクロール最下部でフッターに隠れないよう余白 */
        }
        /* フッター（ZipSearch参考）: 常に画面下部に固定表示 */
        .pictcomp-footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: #f8f9fa;
            padding: 12px 24px;
            text-align: center;
            color: #6c757d;
            font-size: 13px;
            border-top: 3px solid #764ba2;
            z-index: 998;
        }
        .pictcomp-footer a {
            color: #6c757d;
            text-decoration: none;
        }
        .pictcomp-footer a:hover {
            text-decoration: underline;
        }
        /* フッター分の余白をメインコンテンツに追加 */
        div[data-testid="stAppViewContainer"] > div {
            padding-bottom: 80px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # === 上段: 全幅ヘッダー（ロゴ・アプリ名）※スクロール時も固定表示 ===
    header_container = st.container()
    with header_container:
        header_col1, header_col2 = st.columns([1, 4])
        with header_col1:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width=80)
        with header_col2:
            st.markdown("# PictComp - 画像一括圧縮アプリ")
            st.caption("すべての処理はあなたのコンピュータ上で完結します。画像ファイルを選択して、一括して圧縮・リサイズできます。")
        st.divider()
        st.markdown('<div class="fixed-header"></div>', unsafe_allow_html=True)
    
    # セキュリティとプライバシーに関する説明
    with st.expander("🔒 プライバシーとセキュリティについて", expanded=False):
        st.success("""
        **✅ すべての処理はあなたのコンピュータ上で完結します**
        
        - 📁 選択したファイルは**あなたのコンピュータ上でのみ処理**されます
        - 🔒 ファイルがクラウドやインターネット上に送信されることは**一切ありません**
        - 🗑️ 一時ファイルは処理後、**自動的に削除**されます
        - 💻 すべての処理は**あなたのマシン上で完結**します
        
        **一時ファイルの保存場所**: `{}`
        
        ⚠️ **注意**: このアプリはブラウザで動作しますが、すべての処理はローカルで実行されます。
        ファイルは一時的にローカルの一時ディレクトリに保存されますが、処理後は自動的に削除されます。
        """.format(Path(tempfile.gettempdir()) / "pictcomp_web"))
    
    # Streamlitバージョンを確認して複数ファイル選択の可否を判定
    if "support_multiple_files" not in st.session_state:
        try:
            import streamlit as _st_module
            streamlit_version = _st_module.__version__
            version_parts = streamlit_version.split('.')
            major = int(version_parts[0]) if len(version_parts) > 0 else 0
            minor = int(version_parts[1]) if len(version_parts) > 1 else 0
            patch = int(version_parts[2]) if len(version_parts) > 2 else 0
            
            # Streamlit 0.63.0以降でaccept_multipleがサポート
            # ただし、安定性を考慮して1.0.0以降を推奨
            if major > 1:
                support_multiple = True
            elif major == 1:
                support_multiple = minor >= 28  # 1.28.0以降を推奨
            elif major == 0:
                support_multiple = minor >= 63  # 0.63.0以降でサポート
            else:
                support_multiple = False
            
            # 実際にaccept_multipleパラメータが存在するか確認
            import inspect
            file_uploader_sig = inspect.signature(st.file_uploader)
            accept_multiple_exists = 'accept_multiple' in file_uploader_sig.parameters
            if not accept_multiple_exists:
                support_multiple = False
            
            st.session_state.support_multiple_files = support_multiple
            st.session_state.streamlit_version = streamlit_version
            
            # ログをファイルに書き出し
            import logging
            log_file = Path("streamlit_debug.log")
            logging.basicConfig(
                filename=str(log_file),
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                encoding='utf-8',
                filemode='a'  # 追記モード
            )
            logger = logging.getLogger(__name__)
            logger.info("=" * 50)
            logger.info(f"Streamlitバージョン: {streamlit_version}")
            logger.info(f"バージョン詳細: major={major}, minor={minor}, patch={patch}")
            logger.info(f"複数ファイル選択サポート: {support_multiple}")
            logger.info(f"accept_multipleパラメータ存在: {accept_multiple_exists}")
            logger.info("=" * 50)
        except Exception as e:
            # エラーが発生した場合は安全のためFalse
            st.session_state.support_multiple_files = False
            st.session_state.streamlit_version = "不明"
            
            # エラーログ
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"バージョン確認エラー: {str(e)}")
            except:
                pass
            
            st.error(f"バージョン確認エラー: {str(e)}")
    
    # ライセンスチェック
    is_pro = license_manager.check_license()
    
    # === 下段: 縦分割（左: 設定、右: メインコンテンツ）※左右ペインは独立スクロール ===
    pane_container = st.container()
    with pane_container:
        st.markdown('<div class="scrollable-panes-marker"></div>', unsafe_allow_html=True)
        left_col, right_col = st.columns([1, 3])
    
    # 左カラム: 圧縮設定（上段に約3行分の余白）
    with left_col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.header("⚙️ 圧縮設定")
        
        # プリセット選択（カスタムを最後に）
        preset_names = PresetManager.get_preset_names() + ["カスタム"]
        if "selected_preset" not in st.session_state:
            st.session_state.selected_preset = preset_names[0]
        
        selected_preset = st.selectbox("プリセット", preset_names, index=0, key="preset_select")
        st.session_state.selected_preset = selected_preset
        
        settings = CompressionSettings()
        
        if selected_preset != "カスタム":
            try:
                settings = PresetManager.apply_preset(selected_preset)
                st.success(f"✅ プリセット '{selected_preset}' を適用")
            except Exception as e:
                st.error(f"プリセット適用エラー: {e}")
        
        # カスタム設定（常に表示）
        st.subheader("詳細設定")
        if selected_preset == "カスタム":
            st.info("カスタム設定を調整してください")
        
        settings.target_size_kb = st.slider("目標サイズ (KB)", 50, 2000, settings.target_size_kb, key="target_size")
        settings.max_dimension = st.number_input("最大サイズ (長辺px, 0=リサイズなし)", 0, 10000, settings.max_dimension or 0, key="max_dim")
        if settings.max_dimension == 0:
            settings.max_dimension = None
        settings.jpeg_quality = st.slider("JPEG品質", 20, 100, settings.jpeg_quality, key="jpeg_quality")
        settings.output_format = st.selectbox("出力形式", ["auto", "jpg", "png", "webp"], key="output_format")
        
        # EXIF保持: Web公開プリセットは削除固定、無料版はPro限定、Pro版のみ選択可
        is_web_preset = PresetManager.is_web_publishing_preset(selected_preset)
        if is_web_preset:
            settings.keep_exif = False
            st.caption("🔒 Web公開用のため、EXIFは削除されます（セキュリティ・個人情報保護の観点で変更不可）")
        elif not is_pro:
            settings.keep_exif = False
            st.caption("🔒 EXIF保持はPro版限定機能です")
        else:
            settings.keep_exif = st.checkbox("EXIFメタデータを保持", value=settings.keep_exif, key="keep_exif")
        
        if settings.output_format == "webp":
            settings.webp_quality = st.slider("WebP品質", 0, 100, settings.webp_quality, key="webp_quality")
            settings.webp_lossless = st.checkbox("WebP可逆圧縮", value=settings.webp_lossless, key="webp_lossless")
        
        # ファイル名変更オプション（Pro版限定）
        st.divider()
        st.subheader("ファイル名設定")
        if is_pro:
            st.checkbox(
                "撮影日時に基づいてファイル名を変更", 
                value=st.session_state.get("rename_by_shoot_date", False),
                key="rename_by_shoot_date",
                help="EXIF情報の撮影日時を使用してファイル名を変更します（例: 20240126_143022.jpg）\n⚠️ 注意: EXIF情報がない画像では、この機能は適用されません。"
            )
            st.caption("⚠️ EXIF情報がない画像では、ファイル名変更は適用されません")
        else:
            st.caption("🔒 ファイル名変更はPro版限定機能です")
            if "rename_by_shoot_date" not in st.session_state:
                st.session_state.rename_by_shoot_date = False
        
        # 保存設定
        st.divider()
        st.subheader("保存設定")
        
        # ダウンロードファイル名のプレフィックス（keyを指定することで、session_stateが自動的に管理される）
        st.text_input(
            "ダウンロードファイル名のプレフィックス",
            value="",
            key="download_prefix",
            help="ダウンロードするファイル名の前に追加する文字列（例: compressed_）"
        )
        
        # ZIPファイル名の設定（keyを指定することで、session_stateが自動的に管理される）
        st.text_input(
            "ZIPファイル名",
            value="compressed_images",
            key="zip_filename",
            help="ダウンロードするZIPファイルの名前（拡張子なし）"
        )
        
        # 設定をsession_stateに保存
        st.session_state.compression_settings = settings
        
        # ライセンス情報
        st.divider()
        if is_pro:
            st.success("✅ Pro版ライセンス")
        else:
            st.info("📊 無料版")
            if st.button("Pro版にアップグレード"):
                st.info("Pro版は準備中です。しばらくお待ちください。")
    
    # session_stateの初期化
    if "uploaded_files_list" not in st.session_state:
        st.session_state.uploaded_files_list = []
    if "file_info_dict" not in st.session_state:
        st.session_state.file_info_dict = {}
    
    # 右カラム: メインコンテンツ（タブ）
    with right_col:
        tab1, tab2, tab3 = st.tabs(["📁 画像処理", "📊 使い方", "ℹ️ アプリ情報"])
    
    with tab1:
        # ステップ1: ファイル選択
        st.header("ステップ1: 画像ファイルを選択")
        st.info("💡 **すべての処理はあなたのコンピュータ上で完結します**。ファイルは一時的にローカルに保存されますが、処理後は自動的に削除されます。")
        
        # フォルダ選択についての説明
        support_multiple = st.session_state.get("support_multiple_files", False)
        if support_multiple:
            st.info("💡 **複数ファイル選択**: Streamlitのバージョンが対応しているため、複数のファイルを一度に選択できます。")
        else:
            with st.expander("ℹ️ 複数ファイル選択・フォルダ選択について", expanded=False):
                st.markdown("""
                **複数ファイル選択について**
                - 現在のStreamlitバージョンでは単一ファイル選択のみサポートされています
                - 複数ファイルを処理するには、ファイルを1つずつ追加してください
                - 複数ファイルを一度に選択するには、Streamlitをアップグレードしてください: `pip install --upgrade streamlit`
                
                **フォルダ選択について**
                - ブラウザのセキュリティ制限により、Webアプリではフォルダ選択はサポートされていません
                - GUI版（`gui_main.py`）ではフォルダ選択が可能です
                """)
        
        # Streamlitのバージョンに応じて複数ファイル選択を有効化
        # accept_multipleがサポートされているか試行して、エラーが発生した場合は単一ファイル選択にフォールバック
        uploaded_result = None
        
        # まず複数ファイル選択を試行（サポートされている場合）
        if support_multiple:
            try:
                uploaded_result = st.file_uploader(
                    "画像ファイルを選択（複数選択可）",
                    type=["jpg", "jpeg", "png", "heic", "webp"],
                    accept_multiple=True,
                    key="file_uploader_main"
                )
                
                # ログに記録
                if uploaded_result:
                    import logging
                    logger = logging.getLogger(__name__)
                    if isinstance(uploaded_result, list):
                        logger.info(f"✅ 複数ファイル選択モード: {len(uploaded_result)}個のファイルが選択されました")
                        for idx, file in enumerate(uploaded_result, 1):
                            logger.info(f"  - ファイル{idx}: {file.name} ({file.size} bytes)")
                    else:
                        logger.info(f"⚠️ 単一ファイルが選択されました（複数選択モード中）: {uploaded_result.name}")
            except (TypeError, Exception) as e:
                # accept_multipleがサポートされていない場合のフォールバック
                support_multiple = False
                st.session_state.support_multiple_files = False
                
                # エラーログ
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"❌ accept_multipleエラー: {str(e)}")
                logger.error(f"   エラータイプ: {type(e).__name__}")
                
                st.error(f"⚠️ 複数ファイル選択でエラーが発生しました: {str(e)}")
                uploaded_result = None
        else:
            # 単一ファイル選択（support_multipleがFalseの場合、またはエラーが発生した場合）
            uploaded_result = st.file_uploader(
                "画像ファイルを選択",
                type=["jpg", "jpeg", "png", "heic", "webp"],
                key="file_uploader_main"
            )
            
            # ログに記録
            if uploaded_result:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"📎 単一ファイル選択モード: {uploaded_result.name} ({uploaded_result.size} bytes)")
        
        # ファイルをリストに追加する共通処理
        files_to_add = []
        if uploaded_result:
            if isinstance(uploaded_result, list):
                files_to_add = uploaded_result
            else:
                files_to_add = [uploaded_result]
        
        # ファイルをリストに追加
        if files_to_add:
            added_count = 0
            duplicate_count = 0
            for file_to_add in files_to_add:
                # ファイルが既にリストにないかチェック
                file_exists = False
                for existing_file in st.session_state.uploaded_files_list:
                    if existing_file.name == file_to_add.name and existing_file.size == file_to_add.size:
                        file_exists = True
                        break
                
                if not file_exists:
                    st.session_state.uploaded_files_list.append(file_to_add)
                    # ファイル情報を保存
                    st.session_state.file_info_dict[file_to_add.name] = {
                        "file": file_to_add,
                        "bytes": file_to_add.getbuffer()
                    }
                    added_count += 1
                else:
                    duplicate_count += 1
            
            # 一時的な通知メッセージ（toastが使える場合は使用）
            if added_count > 0:
                if hasattr(st, 'toast'):
                    if added_count == 1:
                        st.toast(f"✅ '{files_to_add[0].name}' を追加しました", icon="✅")
                    else:
                        st.toast(f"✅ {added_count}個のファイルを追加しました", icon="✅")
            
            if duplicate_count > 0:
                if hasattr(st, 'toast'):
                    st.toast(f"⚠️ {duplicate_count}個のファイルは既に追加済みです", icon="⚠️")
        
        uploaded_files = st.session_state.uploaded_files_list
        
        # アップロード済みファイルの一覧を明確に表示
        if uploaded_files:
            st.divider()
            st.subheader(f"アップロード済みファイル ({len(uploaded_files)}個)")
            
            # ファイルリストをテーブル形式で表示
            file_list_data = []
            for idx, file in enumerate(uploaded_files, 1):
                file_size_mb = file.size / 1024 / 1024
                file_list_data.append({
                    "No.": idx,
                    "ファイル名": file.name,
                    "サイズ": f"{file_size_mb:.2f} MB"
                })
            
            file_df = pd.DataFrame(file_list_data)
            st.dataframe(file_df, width='stretch', hide_index=True)
            
            # EXIF情報表示ボタンを追加
            st.subheader("EXIF情報の表示")
            st.info("💡 各ファイルのEXIF情報を表示するには、以下のボタンをクリックしてください。")
            
            # EXIF情報表示用のセレクトボックス
            exif_file_options = ["選択してください"] + [f"{idx}. {file.name}" for idx, file in enumerate(uploaded_files, 1)]
            selected_exif_file = st.selectbox(
                "EXIF情報を表示するファイルを選択",
                options=exif_file_options,
                key="exif_file_select"
            )
            
            if selected_exif_file != "選択してください":
                try:
                    file_idx = int(selected_exif_file.split(".")[0]) - 1
                    if 0 <= file_idx < len(uploaded_files):
                        selected_file = uploaded_files[file_idx]
                        st.divider()
                        st.subheader(f"📋 EXIF情報: {selected_file.name}")
                        display_exif_info(selected_file.getbuffer(), selected_file.name)
                except Exception as e:
                    st.error(f"EXIF情報の表示中にエラーが発生しました: {str(e)}")
            
            # ファイル削除機能
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_file_idx = st.selectbox(
                    "削除するファイルを選択",
                    options=["選択してください"] + [f"{idx}. {file.name}" for idx, file in enumerate(uploaded_files, 1)],
                    key="delete_file_select"
                )
            with col2:
                if st.button("🗑️ 削除", key="delete_file_btn"):
                    if selected_file_idx != "選択してください":
                        try:
                            file_idx = int(selected_file_idx.split(".")[0]) - 1
                            if 0 <= file_idx < len(uploaded_files):
                                removed_file = st.session_state.uploaded_files_list.pop(file_idx)
                                if removed_file.name in st.session_state.file_info_dict:
                                    del st.session_state.file_info_dict[removed_file.name]
                                # 削除通知（一時的）
                                if hasattr(st, 'toast'):
                                    st.toast(f"✅ '{removed_file.name}' を削除しました", icon="✅")
                                st.rerun()
                        except:
                            pass
            
            if st.button("🗑️ すべてのファイルをクリア", width='stretch', type="secondary"):
                st.session_state.uploaded_files_list = []
                st.session_state.file_info_dict = {}
                st.rerun()
        else:
            st.info("📎 画像ファイルを選択してください")
        
        if uploaded_files:
            # 無料版の制限チェック（1回20枚まで）
            limit = license_manager.FREE_LIMIT_PER_BATCH
            if not is_pro and len(uploaded_files) > limit:
                st.warning(f"⚠️ 無料版は1回{limit}枚までです。先頭{limit}枚のみ処理します。Pro版で無制限にご利用いただけます。")
                uploaded_files = uploaded_files[:limit]
            
            st.divider()
            st.header("ステップ2: 設定確認")
            
            # 設定を取得（session_stateから、なければデフォルト）
            if "compression_settings" in st.session_state:
                settings = st.session_state.compression_settings
            else:
                settings = CompressionSettings()
                st.session_state.compression_settings = settings
            
            # プリセット名を取得
            if "selected_preset" in st.session_state:
                selected_preset = st.session_state.selected_preset
            else:
                selected_preset = "カスタム"
            
            # 設定のサマリーを表示
            col1, col2 = st.columns(2)
            with col1:
                st.metric("プリセット", selected_preset)
                st.metric("目標サイズ", f"{settings.target_size_kb} KB")
                st.metric("最大サイズ", f"{settings.max_dimension or 'なし'} px")
            with col2:
                st.metric("JPEG品質", f"{settings.jpeg_quality}")
                st.metric("出力形式", settings.output_format)
                rename_status = "有効" if ("rename_by_shoot_date" in st.session_state and st.session_state.rename_by_shoot_date) else "無効"
                st.metric("ファイル名変更", rename_status)
            
            st.divider()
            st.header("ステップ3: 処理実行")
            
            # プレビューセクション
            with st.expander("📷 プレビュー（最初の画像）", expanded=False):
                if uploaded_files:
                    first_file = uploaded_files[0]
                    img = Image.open(io.BytesIO(first_file.getbuffer()))
                    st.image(img, caption=first_file.name, width='stretch')
                    
                    # EXIF情報を表示
                    if st.button("EXIF情報を表示", key="preview_exif"):
                        display_exif_info(first_file.getbuffer(), first_file.name)
            
            if st.button("🚀 圧縮開始", type="primary", width='stretch'):
                # 設定の最終確認
                if "compression_settings" not in st.session_state:
                    st.error("設定が正しく読み込まれていません。ページを再読み込みしてください。")
                    st.stop()
                
                settings = st.session_state.compression_settings
                compressor = ImageCompressor(settings)
                
                # 一時ディレクトリを作成（システムの一時ディレクトリを使用）
                temp_dir = Path(tempfile.gettempdir()) / "pictcomp_web" / "output"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                results = []
                total_input_size = 0
                total_output_size = 0
                start_time = time.time()
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    # プログレス更新
                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"処理中: {uploaded_file.name} ({idx + 1}/{len(uploaded_files)})")
                    
                    # 一時ファイルに保存（安全なファイル名を使用）
                    safe_input_name = sanitize_filename(uploaded_file.name)
                    input_path = temp_dir / f"input_{idx}_{safe_input_name}"
                    try:
                        with open(input_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    except Exception as e:
                        st.error(f"ファイル '{uploaded_file.name}' の保存中にエラーが発生しました: {str(e)}")
                        continue
                    
                    # 圧縮実行
                    safe_output_name = sanitize_filename(uploaded_file.name)
                    output_path = temp_dir / f"compressed_{idx}_{safe_output_name}"
                    success, result = compressor.compress_image(str(input_path), str(output_path))
                    
                    if success:
                        # 実際の出力パスを取得（compress_imageが返す実際のパスを使用）
                        actual_output_path = result.get("output_path", str(output_path))
                        actual_output_path_obj = Path(actual_output_path)
                        
                        # ファイルが正しく作成されたか確認
                        if not actual_output_path_obj.exists():
                            st.error(f"⚠️ 圧縮は成功しましたが、ファイルが見つかりません: {actual_output_path}")
                            continue
                        # 出力形式を取得
                        output_format = result.get("format", "jpg")
                        
                        # ファイル名変更オプション（session_stateから取得）
                        final_filename = uploaded_file.name
                        has_exif_info = False
                        exif_rename_applied = False
                        
                        # 撮影日時に基づくファイル名変更
                        if "rename_by_shoot_date" in st.session_state and st.session_state.rename_by_shoot_date:
                            final_filename, has_exif_info = generate_filename_from_exif(
                                uploaded_file.getbuffer(), 
                                uploaded_file.name,
                                uploaded_file.name,
                                output_format
                            )
                            exif_rename_applied = has_exif_info
                            
                            # EXIF情報がない場合の警告
                            if not has_exif_info:
                                import logging
                                logger = logging.getLogger(__name__)
                                logger.warning(f"⚠️ {uploaded_file.name}: EXIF情報がないため、ファイル名変更は適用されませんでした")
                        
                        # 出力形式に応じて拡張子を変更
                        name, original_ext = os.path.splitext(final_filename)
                        if output_format == "jpg":
                            final_ext = ".jpg"
                        elif output_format == "png":
                            final_ext = ".png"
                        elif output_format == "webp":
                            final_ext = ".webp"
                        else:
                            final_ext = original_ext
                        
                        # 拡張子が変更される場合のみ更新
                        if final_ext != original_ext:
                            final_filename = f"{name}{final_ext}"
                        
                        # プレフィックスを追加
                        if "download_prefix" in st.session_state and st.session_state.download_prefix:
                            name, ext = os.path.splitext(final_filename)
                            final_filename = f"{st.session_state.download_prefix}{name}{ext}"
                        
                        # 重複チェック
                        counter = 1
                        base_name, ext = os.path.splitext(final_filename)
                        while any(r["filename"] == final_filename for r in results):
                            final_filename = f"{base_name}_{counter:03d}{ext}"
                            counter += 1
                        
                        # ログに記録
                        import logging
                        logger = logging.getLogger(__name__)
                        log_message = f"📝 ファイル処理: {uploaded_file.name} -> {final_filename}"
                        log_message += f" (出力形式: {output_format}"
                        if exif_rename_applied:
                            log_message += ", EXIFリネーム: 適用"
                        elif "rename_by_shoot_date" in st.session_state and st.session_state.rename_by_shoot_date:
                            log_message += ", EXIFリネーム: EXIF情報なしのため未適用"
                        log_message += ")"
                        logger.info(log_message)
                        
                        # EXIF情報がない場合の警告を表示
                        if "rename_by_shoot_date" in st.session_state and st.session_state.rename_by_shoot_date and not exif_rename_applied:
                            if hasattr(st, 'toast'):
                                st.toast(f"⚠️ {uploaded_file.name}: EXIF情報がないため、ファイル名変更は適用されませんでした", icon="⚠️")
                        
                        results.append({
                            "filename": final_filename,
                            "original_filename": uploaded_file.name,
                            "input_size": result["input_size"],
                            "output_size": result["output_size"],
                            "compression_ratio": result["compression_ratio"],
                            "output_path": actual_output_path,  # 実際の出力パスを使用
                            "processing_time": result.get("processing_time", 0)
                        })
                        total_input_size += result["input_size"]
                        total_output_size += result["output_size"]
                    
                    # 一時ファイルを削除
                    try:
                        if input_path.exists():
                            input_path.unlink()
                    except Exception as e:
                        # 削除エラーは無視（後でクリーンアップされる）
                        pass
                
                total_processing_time = time.time() - start_time
                progress_bar.progress(1.0)
                status_text.text("完了！")
                
                # 結果表示
                st.success(f"✅ {len(results)}個のファイルを処理しました")
                
                compression_ratio = (1 - total_output_size / total_input_size) * 100 if total_input_size > 0 else 0
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("合計サイズ削減", f"{compression_ratio:.1f}%")
                with col2:
                    st.metric("元のサイズ", f"{total_input_size / 1024 / 1024:.2f} MB")
                with col3:
                    st.metric("圧縮後サイズ", f"{total_output_size / 1024 / 1024:.2f} MB")
                
                # 結果テーブル
                if results:
                    df = pd.DataFrame(results)
                    df["input_size_mb"] = df["input_size"] / 1024 / 1024
                    df["output_size_mb"] = df["output_size"] / 1024 / 1024
                    st.dataframe(
                        df[["filename", "input_size_mb", "output_size_mb", "compression_ratio"]].rename(columns={
                            "filename": "ファイル名",
                            "input_size_mb": "元のサイズ (MB)",
                            "output_size_mb": "圧縮後 (MB)",
                            "compression_ratio": "削減率 (%)"
                        }),
                        width='stretch'
                    )
                    
                    # レポートエクスポート（Pro版限定）
                    col1, col2 = st.columns(2)
                    with col1:
                        if is_pro:
                            csv_data = df.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                label="📊 CSVレポートを保存",
                                data=csv_data,
                                file_name=f"compression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.caption("🔒 CSVレポートはPro版限定です")
                    with col2:
                        if is_pro:
                            report_data = {
                                "summary": {
                                    "total_files": len(results),
                                    "total_input_size": total_input_size,
                                    "total_output_size": total_output_size,
                                    "compression_ratio": compression_ratio,
                                    "processing_time": total_processing_time
                                },
                                "results": results
                            }
                            json_data = json.dumps(report_data, indent=2, ensure_ascii=False, default=str)
                            st.download_button(
                                label="📋 JSONレポートを保存",
                                data=json_data,
                                file_name=f"compression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
                        else:
                            st.caption("🔒 JSONレポートはPro版限定です")
                
                # ZIPファイルとして保存（ダウンロード）
                if results:
                    zip_buffer = io.BytesIO()
                    files_added_to_zip = 0
                    missing_files = []
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for result in results:
                            output_path_str = result["output_path"]
                            
                            # ファイルが存在するか確認
                            path_obj = Path(output_path_str)
                            if path_obj.exists() and path_obj.is_file():
                                try:
                                    zip_file.write(output_path_str, result["filename"])
                                    files_added_to_zip += 1
                                except Exception as e:
                                    missing_files.append(f"{result['filename']}: {str(e)}")
                            else:
                                missing_files.append(f"{result['filename']}: ファイルが見つかりません (パス: {output_path_str})")
                    
                    # エラーメッセージを表示
                    if missing_files:
                        with st.expander("⚠️ 一部のファイルが見つかりませんでした", expanded=True):
                            for msg in missing_files:
                                st.warning(msg)
                    
                    if files_added_to_zip > 0:
                        # ZIPファイル名を取得（設定から、またはデフォルト）
                        zip_name = st.session_state.get("zip_filename", "compressed_images")
                        if not zip_name:
                            zip_name = "compressed_images"
                        # タイムスタンプを追加（オプション）
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        zip_file_name = f"{zip_name}_{timestamp}.zip"
                        
                        st.download_button(
                            label="💾 圧縮済みファイルを保存 (ZIP)",
                            data=zip_buffer.getvalue(),
                            file_name=zip_file_name,
                            mime="application/zip",
                            help="ZIPファイルとして保存します。ブラウザの設定で保存先フォルダが指定されます。"
                        )
                        
                        # 個別ファイルの保存オプション
                        st.divider()
                        st.subheader("個別ファイルの保存")
                        st.info("💡 個別にファイルを保存する場合は、以下のボタンを使用してください。")
                        
                        # 個別ダウンロードボタンを列で表示
                        cols_per_row = 3
                        for i in range(0, len(results), cols_per_row):
                            cols = st.columns(cols_per_row)
                            for j, col in enumerate(cols):
                                if i + j < len(results):
                                    result = results[i + j]
                                    output_path_str = str(result["output_path"])
                                    path_obj = Path(output_path_str)
                                    
                                    with col:
                                        if path_obj.exists():
                                            try:
                                                with open(path_obj, "rb") as f:
                                                    file_data = f.read()
                                                
                                                st.download_button(
                                                    label=f"💾 {result['filename']}",
                                                    data=file_data,
                                                    file_name=result["filename"],
                                                    mime="image/jpeg" if result["filename"].lower().endswith((".jpg", ".jpeg")) else "image/png",
                                                    key=f"download_{i+j}",
                                                    help="このファイルを保存します"
                                                )
                                            except Exception as e:
                                                st.error(f"ダウンロードエラー: {str(e)}")
                                        else:
                                            st.warning(f"ファイルが見つかりません: {result['filename']}")
                    else:
                        st.error("ZIPファイルに追加できるファイルがありませんでした。")
                    
                    # 一時ファイルをクリーンアップ
                    for result in results:
                        try:
                            output_path = result["output_path"]
                            if isinstance(output_path, Path):
                                path_obj = output_path
                            else:
                                path_obj = Path(str(output_path))
                            
                            if path_obj.exists():
                                path_obj.unlink()
                        except Exception as e:
                            # 削除エラーは無視
                            pass
                    
                    # 一時ディレクトリも削除を試みる（空の場合）
                    try:
                        if temp_dir.exists() and not any(temp_dir.iterdir()):
                            temp_dir.rmdir()
                    except:
                        pass
    
    with tab2:
        st.header("使い方")
        st.markdown("""
        ### 基本的な使い方
        
        1. **ステップ1: ファイル選択**: 「画像処理」タブで画像ファイルを選択（複数回選択で追加可能）
        2. **ステップ2: 設定確認**: サイドバーでプリセットを選択するか、カスタム設定を調整
        3. **ステップ3: 処理実行**: 「圧縮開始」ボタンをクリック
        4. **ダウンロード**: 処理完了後、ZIPファイルまたはレポート（CSV/JSON）としてダウンロード
        
        ### ファイル管理
        
        - アップロードしたファイルは一覧で確認できます
        - 個別にファイルを削除することも、すべてクリアすることも可能です
        - プレビューで最初の画像とEXIF情報を確認できます
        
        ### EXIF（撮影情報）について
        
        EXIFには以下の点にご注意ください：
        
        - **🔒 セキュリティ**: GPS情報が含まれると撮影場所が特定されるリスクがあります。Web公開する画像ではEXIF削除を推奨します。
        - **🔒 個人情報保護**: 撮影日時・カメラ機種・レンズ情報などが含まれます。不特定多数に公開する場合は削除を検討してください。
        - **📦 ファイル容量**: EXIFを保持するとファイルサイズが増えます。容量を抑えたい場合は削除を選択してください。
        
        ※ ブログ用・SNS用・Web用・メール添付用・PNG透過保持のプリセットでは、セキュリティ・個人情報保護の観点からEXIF削除が固定されています。
        
        ### ファイル名変更について
        
        - **撮影日時に基づいてファイル名を変更**をONにすると、ダウンロード時のファイル名が撮影日時形式（`YYYYMMDD_HHMMSS`）に変わります
        - 例: `IMG_1234.jpg` → `20240126_143022.jpg`（2024年1月26日 14:30:22 撮影の場合）
        - 圧縮処理後、ZIPまたは個別ファイルをダウンロードする際に適用されます
        - EXIF情報（撮影日時）がない画像は、元のファイル名のままです
        - 同じ撮影日時の画像が複数ある場合は、`20240126_143022_001.jpg` のように連番が付きます
        - **ダウンロードファイル名のプレフィックス**を設定すると、すべてのファイル名の先頭に指定した文字列が付きます（例: `compressed_` → `compressed_20240126_143022.jpg`）
        
        ### プリセットについて
        
        - **PowerPoint用**: プレゼン資料に最適化
        - **ブログ用**: Webサイト用に最適化
        - **SNS用**: Twitter/Instagram投稿用
        - **Web用**: Webサイト用（WebP形式）
        - **メール添付用**: メール送信用に最適化
        
        ### 対応形式
        
        - **入力**: JPEG, PNG, HEIC, WebP
        - **出力**: JPEG, PNG, WebP
        
        ### 無料版とPro版の違い
        
        ※Pro版は準備中です。
        
        | 機能 | 無料版 | Pro版 |
        |------|--------|-------|
        | 1回の処理枚数 | 20枚まで | 無制限 |
        | 基本圧縮 | ✅ | ✅ |
        | PNG/WebP | ✅ | ✅ |
        | リサイズ | ✅ | ✅ |
        | プリセット | ✅ | ✅ |
        | EXIF情報閲覧 | ✅ | ✅ |
        | EXIF保持 | ❌ | ✅ |
        | レポートエクスポート（CSV/JSON） | ❌ | ✅ |
        | ファイル名変更 | ❌ | ✅ |
        
        ⚠️ **Web版の制限事項**
        - ファイルシステムへの直接アクセスは不可（セキュリティ上の理由）
        - ファイル日時の更新機能はWeb版では利用不可
        - フォルダ選択はファイルアップロードに置き換え
        """)
    
    with tab3:
        from version import __version__, COPYRIGHT, HOMEPAGE, SUPPORT_EMAIL, FEEDBACK_FORM_URL as DEFAULT_FEEDBACK_URL, PICTCOMP_PAGE_URL
        
        st.header("アプリ情報")
        
        # バージョン
        st.subheader("📌 バージョン")
        st.markdown(f"**PictComp v{__version__}**")
        
        # 機能一覧
        st.subheader("📌 機能一覧")
        st.markdown("""
        ✅ **基本機能**: 画像一括圧縮（JPEG、PNG、HEIC、WebP）、リサイズ、EXIFメタデータ保持オプション、プリセット
        
        ✅ **EXIF情報閲覧**: 撮影日時、カメラ情報、GPS情報の表示
        
        ✅ **レポート機能**: CSV/JSON形式でのエクスポート（Pro版）
        
        ✅ **ファイル名変更**: 撮影日時に基づいたファイル名変更（Pro版）
        
        ⚠️ **Web版の制限**: フォルダ選択不可、ファイルアップロードに置き換え
        """)
        
        # クレジット
        st.subheader("📌 クレジット")
        st.markdown("""
        - **Pillow** (PIL): 画像処理 - [BSD License](https://github.com/python-pillow/Pillow/blob/main/LICENSE)
        - **pillow-heif**: HEIC形式対応 - [MIT License](https://github.com/bigcat88/pillow_heif/blob/main/LICENSE)
        - **Streamlit**: Webアプリフレームワーク - [Apache 2.0](https://github.com/streamlit/streamlit/blob/develop/LICENSE)
        - **pandas**: データ処理 - [BSD License](https://github.com/pandas-dev/pandas/blob/main/LICENSE)
        """)
        
        # 法的文書・リンク
        st.subheader("📌 法的文書・リンク")
        pictcomp_url = os.environ.get("PICTCOMP_PAGE_URL") or PICTCOMP_PAGE_URL or ""
        link_lines = [f"- **著作権**: {COPYRIGHT}"]
        if pictcomp_url:
            link_lines.insert(1, f"- **PictCompのページ**: [PictComp]({pictcomp_url})（新しいタブで開く）")
        link_lines.extend([
            f"- **ホームページ**: [Office Go Plan]({HOMEPAGE})（新しいタブで開く）",
            f"- **お問い合わせ**: [{SUPPORT_EMAIL}](mailto:{SUPPORT_EMAIL})"
        ])
        st.markdown("\n".join(link_lines))
        
        # アンケート・要望フォーム
        st.subheader("📌 ご要望・アンケート")
        st.markdown("""
        開発してほしい機能やご要望がありましたら、お気軽にお聞かせください。
        お問い合わせ先までメールいただくか、下記のフォームからご送信ください。
        """)
        # アンケートフォームのURL（環境変数 > version.py の順で優先）
        feedback_form_url = os.environ.get("PICTCOMP_FEEDBACK_FORM_URL") or DEFAULT_FEEDBACK_URL or ""
        if feedback_form_url:
            st.markdown(f"[📝 ご要望・アンケートフォームを開く]({feedback_form_url})")
        else:
            st.info("💡 アンケートフォームのURLが設定されていません。お問い合わせはメールでお願いします。")
            st.markdown(f"**メール**: [{SUPPORT_EMAIL}](mailto:{SUPPORT_EMAIL}?subject=PictComp%20ご要望)")

    # === フッター（ZipSearch参考: ライセンス情報・著作権・ホームページ・お問合せ） ===
    if is_pro:
        license_text = "Pro版 - 無制限"
    else:
        license_text = f"無料版 - 制限: 1回{license_manager.FREE_LIMIT_PER_BATCH}枚まで（Pro版は準備中）"
    st.markdown(
        f'<div class="pictcomp-footer">'
        f'{license_text}<br>'
        f'{COPYRIGHT} | <a href="{HOMEPAGE}" target="_blank">Office Go Plan</a> | '
        f'<a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>'
        f'</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
