# -*- coding: utf-8 -*-
"""
バッチプリセット機能
用途別の圧縮設定テンプレートを提供
"""
from image_compressor import CompressionSettings
from typing import Dict


class PresetManager:
    """プリセット管理クラス"""
    
    PRESETS = {
        "PowerPoint用": {
            "target_size_kb": 300,
            "jpeg_quality": 85,
            "max_dimension": 1920,
            "output_format": "jpg",
            "keep_exif": False
        },
        "ブログ用": {
            "target_size_kb": 200,
            "jpeg_quality": 80,
            "max_dimension": 1600,
            "output_format": "jpg",
            "keep_exif": False
        },
        "SNS用（Twitter/Instagram）": {
            "target_size_kb": 500,
            "jpeg_quality": 85,
            "max_dimension": 2048,
            "output_format": "jpg",
            "keep_exif": False
        },
        "Web用（高品質）": {
            "target_size_kb": 500,
            "jpeg_quality": 90,
            "max_dimension": 2400,
            "output_format": "webp",
            "webp_quality": 85,
            "webp_lossless": False,
            "keep_exif": False
        },
        "Web用（軽量）": {
            "target_size_kb": 100,
            "jpeg_quality": 70,
            "max_dimension": 1200,
            "output_format": "webp",
            "webp_quality": 75,
            "webp_lossless": False,
            "keep_exif": False
        },
        "メール添付用": {
            "target_size_kb": 150,
            "jpeg_quality": 75,
            "max_dimension": 1280,
            "output_format": "jpg",
            "keep_exif": False
        },
        "アーカイブ用（高品質保持）": {
            "target_size_kb": 1000,
            "jpeg_quality": 95,
            "max_dimension": None,
            "output_format": "jpg",
            "keep_exif": True
        },
        "PNG透過保持": {
            "target_size_kb": 500,
            "png_compress_level": 9,
            "max_dimension": 1920,
            "output_format": "png",
            "keep_exif": False
        }
    }
    
    @classmethod
    def get_preset_names(cls) -> list:
        """プリセット名のリストを取得"""
        return list(cls.PRESETS.keys())
    
    @classmethod
    def apply_preset(cls, preset_name: str) -> CompressionSettings:
        """プリセットを適用して設定オブジェクトを返す"""
        if preset_name not in cls.PRESETS:
            raise ValueError(f"プリセット '{preset_name}' が見つかりません")
        
        preset_data = cls.PRESETS[preset_name]
        settings = CompressionSettings()
        settings.from_dict(preset_data)
        return settings
    
    @classmethod
    def save_custom_preset(cls, name: str, settings: CompressionSettings):
        """カスタムプリセットを保存"""
        cls.PRESETS[name] = settings.to_dict()
    
    @classmethod
    def get_all_presets(cls) -> Dict[str, Dict]:
        """すべてのプリセットを取得"""
        return cls.PRESETS.copy()

