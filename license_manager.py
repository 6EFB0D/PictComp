# -*- coding: utf-8 -*-
"""
ライセンス管理モジュール
無料版とPro版の機能制限を管理
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib


class LicenseManager:
    """ライセンス管理クラス"""
    
    def __init__(self, license_file: str = "license.json"):
        self.license_file = license_file
        self.config_dir = os.path.expanduser("~/.pictcomp")
        self.full_path = os.path.join(self.config_dir, license_file)
        os.makedirs(self.config_dir, exist_ok=True)
        
        # 無料版の制限
        self.FREE_LIMIT_MONTHLY = 100  # 月間100枚まで
    
    def get_usage_data(self) -> Dict:
        """使用状況データを取得"""
        if not os.path.exists(self.full_path):
            return {
                "license_type": "free",
                "license_key": None,
                "monthly_count": 0,
                "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
                "total_processed": 0
            }
        
        try:
            with open(self.full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            return {
                "license_type": "free",
                "monthly_count": 0,
                "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
                "total_processed": 0
            }
    
    def save_usage_data(self, data: Dict):
        """使用状況データを保存"""
        try:
            with open(self.full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"ライセンス保存エラー: {e}")
            return False
    
    def check_license(self) -> bool:
        """ライセンスをチェック（Pro版かどうか）"""
        data = self.get_usage_data()
        
        if data.get("license_type") == "pro":
            # ライセンスキーの検証（簡易版）
            license_key = data.get("license_key")
            if license_key and self.validate_license_key(license_key):
                return True
        
        return False
    
    def validate_license_key(self, license_key: str) -> bool:
        """ライセンスキーを検証（簡易実装）"""
        # 実際の実装では、より堅牢な検証が必要
        # ここでは簡易的なチェックのみ
        if len(license_key) < 10:
            return False
        
        # ハッシュチェックなど（実装例）
        expected_hash = hashlib.md5(license_key.encode()).hexdigest()
        # 実際の検証ロジックはここに実装
        
        return True
    
    def can_process(self, file_count: int) -> tuple[bool, Optional[str]]:
        """処理可能かチェック"""
        if self.check_license():
            return True, None  # Pro版は無制限
        
        # 無料版の制限チェック
        data = self.get_usage_data()
        last_reset = datetime.strptime(data.get("last_reset_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        now = datetime.now()
        
        # 月が変わったらリセット
        if now.month != last_reset.month or now.year != last_reset.year:
            data["monthly_count"] = 0
            data["last_reset_date"] = now.strftime("%Y-%m-%d")
            self.save_usage_data(data)
        
        current_count = data.get("monthly_count", 0)
        
        if current_count + file_count > self.FREE_LIMIT_MONTHLY:
            remaining = self.FREE_LIMIT_MONTHLY - current_count
            return False, f"無料版の月間制限（{self.FREE_LIMIT_MONTHLY}枚）に達しています。残り: {remaining}枚"
        
        return True, None
    
    def record_usage(self, file_count: int):
        """使用状況を記録"""
        data = self.get_usage_data()
        data["monthly_count"] = data.get("monthly_count", 0) + file_count
        data["total_processed"] = data.get("total_processed", 0) + file_count
        self.save_usage_data(data)
    
    def activate_pro_license(self, license_key: str) -> tuple[bool, str]:
        """Pro版ライセンスを有効化"""
        if not self.validate_license_key(license_key):
            return False, "無効なライセンスキーです"
        
        data = self.get_usage_data()
        data["license_type"] = "pro"
        data["license_key"] = license_key
        data["activated_date"] = datetime.now().strftime("%Y-%m-%d")
        
        if self.save_usage_data(data):
            return True, "Pro版ライセンスが有効化されました"
        else:
            return False, "ライセンスの保存に失敗しました"
    
    def get_usage_info(self) -> Dict:
        """使用状況情報を取得"""
        data = self.get_usage_data()
        is_pro = self.check_license()
        
        info = {
            "is_pro": is_pro,
            "license_type": "Pro版" if is_pro else "無料版",
            "monthly_count": data.get("monthly_count", 0),
            "monthly_limit": None if is_pro else self.FREE_LIMIT_MONTHLY,
            "total_processed": data.get("total_processed", 0)
        }
        
        if not is_pro:
            info["remaining"] = self.FREE_LIMIT_MONTHLY - info["monthly_count"]
        
        return info

