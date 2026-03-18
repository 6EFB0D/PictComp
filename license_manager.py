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
        
        # 無料版の制限（1回の処理あたり）
        self.FREE_LIMIT_PER_BATCH = 20  # 1回20枚まで
        
        # プレリリース: 14日間トライアル
        self.TRIAL_DAYS = 14
    
    def get_usage_data(self) -> Dict:
        """使用状況データを取得"""
        default_data = {
            "license_type": "free",
            "license_key": None,
            "monthly_count": 0,
            "last_reset_date": datetime.now().strftime("%Y-%m-%d"),
            "total_processed": 0,
            "first_launch_date": None,
        }
        
        if not os.path.exists(self.full_path):
            data = default_data.copy()
            data["first_launch_date"] = datetime.now().strftime("%Y-%m-%d")
            self.save_usage_data(data)
            return data
        
        try:
            with open(self.full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "first_launch_date" not in data:
                data["first_launch_date"] = datetime.now().strftime("%Y-%m-%d")
                self.save_usage_data(data)
            return data
        except Exception:
            return default_data.copy()
    
    def save_usage_data(self, data: Dict):
        """使用状況データを保存"""
        try:
            with open(self.full_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"ライセンス保存エラー: {e}")
            return False
    
    def is_trial_active(self) -> bool:
        """14日間トライアルが有効かどうか"""
        data = self.get_usage_data()
        first_launch = data.get("first_launch_date")
        if not first_launch:
            return True  # 未記録の場合はトライアル有効とする
        try:
            launch_dt = datetime.strptime(first_launch, "%Y-%m-%d")
            elapsed = (datetime.now() - launch_dt).days
            return elapsed < self.TRIAL_DAYS
        except Exception:
            return True
    
    def get_remaining_trial_days(self) -> int:
        """トライアル残り日数を取得（0=期限切れ）"""
        data = self.get_usage_data()
        first_launch = data.get("first_launch_date")
        if not first_launch:
            return self.TRIAL_DAYS
        try:
            launch_dt = datetime.strptime(first_launch, "%Y-%m-%d")
            elapsed = (datetime.now() - launch_dt).days
            return max(0, self.TRIAL_DAYS - elapsed)
        except Exception:
            return self.TRIAL_DAYS
    
    def trial_end_date(self) -> Optional[str]:
        """トライアル終了日を取得"""
        data = self.get_usage_data()
        first_launch = data.get("first_launch_date")
        if not first_launch:
            return None
        try:
            launch_dt = datetime.strptime(first_launch, "%Y-%m-%d")
            end_dt = launch_dt + timedelta(days=self.TRIAL_DAYS)
            return end_dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    
    def check_license(self) -> bool:
        """ライセンスをチェック（Pro版または14日間トライアル中かどうか）"""
        data = self.get_usage_data()
        
        if data.get("license_type") == "pro":
            license_key = data.get("license_key")
            if license_key and self.validate_license_key(license_key):
                return True
        
        if self.is_trial_active():
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
        """処理可能かチェック（1回の処理枚数）"""
        if self.check_license():
            return True, None  # Pro版は無制限
        
        if file_count > self.FREE_LIMIT_PER_BATCH:
            return False, f"無料版は1回{self.FREE_LIMIT_PER_BATCH}枚までです。Pro版にアップグレードしてください。"
        
        return True, None
    
    def record_usage(self, file_count: int):
        """使用状況を記録（累計用、将来の拡張用）"""
        data = self.get_usage_data()
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
        is_trial = self.is_trial_active() and data.get("license_type") != "pro"
        
        if is_pro:
            license_label = "Pro版" if data.get("license_type") == "pro" else "トライアル中"
        else:
            license_label = "無料版"
        
        info = {
            "is_pro": is_pro,
            "license_type": license_label,
            "per_batch_limit": None if is_pro else self.FREE_LIMIT_PER_BATCH,
            "total_processed": data.get("total_processed", 0),
            "is_trial": is_trial,
            "remaining_trial_days": self.get_remaining_trial_days() if is_trial else 0,
            "trial_end_date": self.trial_end_date() if is_trial else None,
        }
        
        return info

