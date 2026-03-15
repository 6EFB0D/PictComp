# -*- coding: utf-8 -*-
"""
設定管理モジュール
JSON形式で設定を保存・読み込み
"""
import json
import os
from typing import Optional, Dict, Tuple
from image_compressor import CompressionSettings


class ConfigManager:
    """設定ファイルの管理クラス"""
    
    def __init__(self, config_file: str = "pictcomp_config.json"):
        self.config_file = config_file
        self.config_dir = os.path.expanduser("~/.pictcomp")
        self.full_path = os.path.join(self.config_dir, config_file)
        
        # 設定ディレクトリが存在しない場合は作成
        os.makedirs(self.config_dir, exist_ok=True)
    
    def save_settings(self, settings: CompressionSettings):
        """設定を保存"""
        try:
            with open(self.full_path, "w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"設定保存エラー: {e}")
            return False
    
    def load_settings(self) -> Optional[CompressionSettings]:
        """設定を読み込み"""
        if not os.path.exists(self.full_path):
            return None
        
        try:
            with open(self.full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            settings = CompressionSettings()
            settings.from_dict(data)
            return settings
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
            return None
    
    def get_default_settings(self) -> CompressionSettings:
        """デフォルト設定を取得"""
        return CompressionSettings()
    
    def _get_last_folders_path(self) -> str:
        """前回フォルダ設定ファイルのパスを取得"""
        return os.path.join(self.config_dir, "last_folders.json")
    
    def save_last_folders(self, input_folder: str, output_folder: str) -> bool:
        """前回使用したフォルダパスを保存"""
        try:
            path = self._get_last_folders_path()
            data = {
                "input_folder": input_folder,
                "output_folder": output_folder
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"フォルダ保存エラー: {e}")
            return False
    
    def load_last_folders(self) -> Tuple[Optional[str], Optional[str]]:
        """前回使用したフォルダパスを読み込み"""
        path = self._get_last_folders_path()
        if not os.path.exists(path):
            return None, None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            input_folder = data.get("input_folder")
            output_folder = data.get("output_folder")
            return input_folder, output_folder
        except Exception as e:
            print(f"フォルダ読み込みエラー: {e}")
            return None, None

