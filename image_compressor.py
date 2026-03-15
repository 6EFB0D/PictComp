# -*- coding: utf-8 -*-
"""
画像圧縮エンジン
PNG、JPEG、WebP、HEIC形式に対応した画像圧縮・リサイズ機能を提供
"""
import os
from PIL import Image
import pillow_heif
from typing import Optional, Tuple, Dict
import logging


class CompressionSettings:
    """圧縮設定を管理するクラス"""
    def __init__(self):
        self.target_size_kb = 300  # 目標ファイルサイズ（KB）
        self.jpeg_quality = 85  # JPEG品質（初期値）
        self.png_compress_level = 6  # PNG圧縮レベル（0-9、デフォルト6）
        self.webp_quality = 80  # WebP品質
        self.webp_lossless = False  # WebP可逆圧縮
        self.max_dimension = None  # 最大サイズ（長辺ピクセル、None=リサイズなし）
        self.keep_exif = True  # EXIF保持
        self.output_format = "auto"  # 出力形式: "auto", "jpg", "png", "webp"
    
    def to_dict(self) -> Dict:
        """設定を辞書形式で返す"""
        return {
            "target_size_kb": self.target_size_kb,
            "jpeg_quality": self.jpeg_quality,
            "png_compress_level": self.png_compress_level,
            "webp_quality": self.webp_quality,
            "webp_lossless": self.webp_lossless,
            "max_dimension": self.max_dimension,
            "keep_exif": self.keep_exif,
            "output_format": self.output_format
        }
    
    def from_dict(self, settings: Dict):
        """辞書から設定を読み込む"""
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ImageCompressor:
    """画像圧縮・リサイズを行うクラス"""
    
    def __init__(self, settings: Optional[CompressionSettings] = None):
        self.settings = settings or CompressionSettings()
        self.logger = logging.getLogger(__name__)
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """画像をリサイズ（長辺を指定ピクセルに）"""
        if self.settings.max_dimension is None:
            return img
        
        width, height = img.size
        max_dim = max(width, height)
        
        # 拡大は行わない（縮小のみ）
        if max_dim <= self.settings.max_dimension:
            return img
        
        # アスペクト比を維持してリサイズ
        if width > height:
            new_width = self.settings.max_dimension
            new_height = int(height * (self.settings.max_dimension / width))
        else:
            new_height = self.settings.max_dimension
            new_width = int(width * (self.settings.max_dimension / height))
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def get_exif(self, img: Image.Image) -> Optional[Dict]:
        """EXIFデータを取得"""
        if not self.settings.keep_exif:
            return None
        
        try:
            exif_dict = img.getexif()
            if exif_dict:
                return dict(exif_dict)
        except Exception as e:
            self.logger.warning(f"EXIF取得エラー: {e}")
        return None
    
    def apply_orientation(self, img: Image.Image) -> Image.Image:
        """EXIFのOrientationタグに基づいて画像を回転"""
        try:
            exif = img.getexif()
            orientation = exif.get(274)  # Orientation tag
            if orientation:
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except Exception:
            pass
        return img
    
    def compress_jpeg(self, img: Image.Image, output_path: str, target_size_bytes: Optional[int] = None) -> bool:
        """JPEG形式で圧縮"""
        if target_size_bytes is None:
            target_size_bytes = self.settings.target_size_kb * 1024
        
        # EXIF処理
        exif_data = self.get_exif(img)
        img = self.apply_orientation(img)
        
        quality = self.settings.jpeg_quality
        while True:
            save_kwargs = {"format": "JPEG", "quality": quality, "optimize": True}
            if exif_data and self.settings.keep_exif:
                try:
                    save_kwargs["exif"] = img.getexif()
                except Exception:
                    pass
            
            img.save(output_path, **save_kwargs)
            file_size = os.path.getsize(output_path)
            
            if file_size <= target_size_bytes or quality <= 20:
                break
            quality -= 5
        
        return True
    
    def compress_png(self, img: Image.Image, output_path: str) -> bool:
        """PNG形式で圧縮（透過情報を保持）"""
        # 透過PNGの保持
        if img.mode in ("RGBA", "LA"):
            # 透過情報を保持
            img.save(
                output_path,
                format="PNG",
                compress_level=self.settings.png_compress_level,
                optimize=True
            )
        else:
            # 透過なしPNG
            img.save(
                output_path,
                format="PNG",
                compress_level=self.settings.png_compress_level,
                optimize=True
            )
        return True
    
    def compress_webp(self, img: Image.Image, output_path: str) -> bool:
        """WebP形式で圧縮"""
        # EXIF処理
        exif_data = self.get_exif(img)
        img = self.apply_orientation(img)
        
        save_kwargs = {
            "format": "WEBP",
            "quality": self.settings.webp_quality,
            "lossless": self.settings.webp_lossless,
            "method": 6  # 最高品質の圧縮方法
        }
        
        if exif_data and self.settings.keep_exif:
            try:
                save_kwargs["exif"] = img.getexif()
            except Exception:
                pass
        
        img.save(output_path, **save_kwargs)
        return True
    
    def determine_output_format(self, input_path: str, original_format: str) -> str:
        """出力形式を決定"""
        if self.settings.output_format != "auto":
            return self.settings.output_format
        
        # 自動判定: 入力形式に合わせる
        ext = original_format.lower()
        if ext in [".jpg", ".jpeg", ".heic"]:
            return "jpg"
        elif ext == ".png":
            return "png"
        else:
            return "jpg"  # デフォルト
    
    def compress_image(self, input_path: str, output_path: str) -> Tuple[bool, Dict]:
        """画像を圧縮（メイン関数）"""
        result = {
            "success": False,
            "input_size": 0,
            "output_size": 0,
            "compression_ratio": 0.0,
            "format": "unknown",
            "error": None
        }
        
        try:
            # 入力ファイルサイズ
            result["input_size"] = os.path.getsize(input_path)
            
            # ファイル拡張子を取得
            name, ext = os.path.splitext(input_path)
            ext = ext.lower()
            
            # 画像を開く
            img = None
            if ext == ".heic":
                heif_file = pillow_heif.read_heif(input_path)
                img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            else:
                img = Image.open(input_path)
            
            # リサイズ
            img = self.resize_image(img)
            
            # 出力形式を決定
            output_format = self.determine_output_format(input_path, ext)
            result["format"] = output_format
            
            # 出力パスを確定
            output_name, _ = os.path.splitext(os.path.basename(output_path))
            if output_format == "jpg":
                final_output_path = os.path.join(os.path.dirname(output_path), f"{output_name}_compressed.jpg")
            elif output_format == "png":
                final_output_path = os.path.join(os.path.dirname(output_path), f"{output_name}_compressed.png")
            elif output_format == "webp":
                final_output_path = os.path.join(os.path.dirname(output_path), f"{output_name}_compressed.webp")
            else:
                final_output_path = output_path
            
            # 圧縮実行
            if output_format == "jpg":
                self.compress_jpeg(img, final_output_path)
            elif output_format == "png":
                self.compress_png(img, final_output_path)
            elif output_format == "webp":
                self.compress_webp(img, final_output_path)
            else:
                raise ValueError(f"未対応の出力形式: {output_format}")
            
            # 結果を記録
            result["output_size"] = os.path.getsize(final_output_path)
            result["compression_ratio"] = (1 - result["output_size"] / result["input_size"]) * 100 if result["input_size"] > 0 else 0
            result["success"] = True
            result["output_path"] = final_output_path  # 実際の出力パスを追加
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"圧縮エラー: {input_path} - {e}")
        
        return result["success"], result

