# -*- coding: utf-8 -*-
"""
EXIFメタデータ閲覧モジュール
画像のEXIF情報を読み取り、表示する機能を提供
"""
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS, GPSTAGS
import pillow_heif
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import os
from pathlib import Path


class ExifViewer:
    """EXIF情報を閲覧するクラス"""
    
    @staticmethod
    def get_exif_data(image_path: str) -> Optional[Dict]:
        """画像からEXIFデータを取得（ファイル情報も含む）"""
        try:
            if image_path.lower().endswith(".heic"):
                heif_file = pillow_heif.read_heif(image_path)
                img = Image.frombytes(heif_file.mode, heif_file.size, heif_file.data)
            else:
                img = Image.open(image_path)
            
            exif_data = img.getexif()
            
            exif_dict = {}
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # GPS情報の処理
                    if tag == "GPSInfo":
                        gps_data = {}
                        for gps_tag_id, gps_value in value.items():
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = gps_value
                        exif_dict[tag] = gps_data
                    else:
                        exif_dict[tag] = value
            
            # ファイル情報を追加
            file_stat = os.stat(image_path)
            exif_dict["_file_created"] = datetime.fromtimestamp(file_stat.st_ctime)
            exif_dict["_file_modified"] = datetime.fromtimestamp(file_stat.st_mtime)
            exif_dict["_file_size"] = file_stat.st_size
            
            return exif_dict
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def format_exif_value(value) -> str:
        """EXIF値を人間が読みやすい形式に変換"""
        if isinstance(value, bytes):
            try:
                return value.decode('utf-8', errors='ignore')
            except:
                return str(value)
        elif isinstance(value, tuple):
            if len(value) == 2 and isinstance(value[0], int):
                # 分数形式 (numerator, denominator)
                if value[1] != 0:
                    return f"{value[0] / value[1]:.6f}"
                else:
                    return str(value[0])
            return ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            return "\n".join(f"  {k}: {v}" for k, v in value.items())
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return str(value)
    
    @staticmethod
    def get_exif_summary(exif_data: Dict) -> List[Tuple[str, str, str]]:
        """EXIFデータのサマリーを取得（主要な情報のみ）
        戻り値: [(カテゴリ, 項目名, 値), ...]
        """
        if not exif_data or "error" in exif_data:
            return []
        
        summary = []
        
        # 日時情報（優先順位: DateTimeOriginal > DateTimeDigitized > DateTime）
        date_time_info = []
        if "DateTimeOriginal" in exif_data:
            date_time_info.append(("撮影日時（元）", ExifViewer.format_exif_value(exif_data["DateTimeOriginal"])))
        if "DateTimeDigitized" in exif_data:
            date_time_info.append(("デジタル化日時", ExifViewer.format_exif_value(exif_data["DateTimeDigitized"])))
        if "DateTime" in exif_data:
            date_time_info.append(("ファイル変更日時", ExifViewer.format_exif_value(exif_data["DateTime"])))
        
        # ファイル情報
        if "_file_created" in exif_data:
            summary.append(("ファイル情報", "ファイル作成日時", exif_data["_file_created"].strftime("%Y-%m-%d %H:%M:%S")))
        if "_file_modified" in exif_data:
            summary.append(("ファイル情報", "ファイル更新日時", exif_data["_file_modified"].strftime("%Y-%m-%d %H:%M:%S")))
        if "_file_size" in exif_data:
            file_size_mb = exif_data["_file_size"] / 1024 / 1024
            summary.append(("ファイル情報", "ファイルサイズ", f"{file_size_mb:.2f} MB"))
        
        # 撮影日時情報を追加
        for label, value in date_time_info:
            summary.append(("撮影日時", label, value))
        
        # カメラ情報
        camera_tags = [
            ("Make", "メーカー"),
            ("Model", "モデル"),
            ("Software", "ソフトウェア"),
            ("LensModel", "レンズ"),
            ("LensMake", "レンズメーカー")
        ]
        for tag, label in camera_tags:
            if tag in exif_data:
                summary.append(("カメラ情報", label, ExifViewer.format_exif_value(exif_data[tag])))
        
        # 画像情報
        image_tags = [
            ("ImageWidth", "幅"),
            ("ImageLength", "高さ"),
            ("ExifImageWidth", "EXIF幅"),
            ("ExifImageHeight", "EXIF高さ"),
            ("Orientation", "向き"),
            ("XResolution", "X解像度"),
            ("YResolution", "Y解像度"),
            ("ColorSpace", "色空間")
        ]
        for tag, label in image_tags:
            if tag in exif_data:
                summary.append(("画像情報", label, ExifViewer.format_exif_value(exif_data[tag])))
        
        # 撮影設定
        shooting_tags = [
            ("FNumber", "F値"),
            ("ExposureTime", "露出時間"),
            ("ISOSpeedRatings", "ISO感度"),
            ("FocalLength", "焦点距離"),
            ("FocalLengthIn35mmFilm", "35mm換算焦点距離"),
            ("Flash", "フラッシュ"),
            ("WhiteBalance", "ホワイトバランス"),
            ("MeteringMode", "測光モード"),
            ("ExposureMode", "露出モード"),
            ("ExposureProgram", "露出プログラム")
        ]
        for tag, label in shooting_tags:
            if tag in exif_data:
                value = ExifViewer.format_exif_value(exif_data[tag])
                # 露出時間を分数形式に変換
                if tag == "ExposureTime" and isinstance(exif_data[tag], tuple):
                    if exif_data[tag][1] != 0:
                        exposure = exif_data[tag][0] / exif_data[tag][1]
                        if exposure < 1:
                            value = f"1/{int(1/exposure)}秒"
                        else:
                            value = f"{exposure:.1f}秒"
                # F値を分数形式に変換
                elif tag == "FNumber" and isinstance(exif_data[tag], tuple):
                    if exif_data[tag][1] != 0:
                        value = f"f/{exif_data[tag][0] / exif_data[tag][1]:.1f}"
                # 焦点距離をmm形式に変換
                elif tag in ["FocalLength", "FocalLengthIn35mmFilm"] and isinstance(exif_data[tag], tuple):
                    if exif_data[tag][1] != 0:
                        value = f"{exif_data[tag][0] / exif_data[tag][1]:.1f}mm"
                
                summary.append(("撮影設定", label, value))
        
        # GPS情報
        if "GPSInfo" in exif_data and isinstance(exif_data["GPSInfo"], dict):
            gps_coords = ExifViewer.format_gps_coordinates(exif_data["GPSInfo"])
            if gps_coords:
                summary.append(("位置情報", "GPS座標", gps_coords))
        
        return summary
    
    @staticmethod
    def get_all_exif_data(exif_data: Dict) -> List[Tuple[str, str]]:
        """すべてのEXIFデータを取得"""
        if not exif_data or "error" in exif_data:
            return []
        
        all_data = []
        for tag, value in sorted(exif_data.items()):
            formatted_value = ExifViewer.format_exif_value(value)
            all_data.append((tag, formatted_value))
        
        return all_data
    
    @staticmethod
    def format_gps_coordinates(gps_info: Dict) -> Optional[str]:
        """GPS座標を度分秒形式に変換"""
        try:
            lat = gps_info.get("GPSLatitude")
            lat_ref = gps_info.get("GPSLatitudeRef", "N")
            lon = gps_info.get("GPSLongitude")
            lon_ref = gps_info.get("GPSLongitudeRef", "E")
            
            if lat and lon:
                def dms_to_decimal(dms, ref):
                    degrees = dms[0] / dms[1] if dms[1] != 0 else dms[0]
                    minutes = dms[2] / dms[3] if len(dms) > 2 and dms[3] != 0 else 0
                    seconds = dms[4] / dms[5] if len(dms) > 4 and dms[5] != 0 else 0
                    decimal = degrees + minutes / 60.0 + seconds / 3600.0
                    if ref in ["S", "W"]:
                        decimal = -decimal
                    return decimal
                
                lat_decimal = dms_to_decimal(lat, lat_ref)
                lon_decimal = dms_to_decimal(lon, lon_ref)
                
                return f"{lat_decimal:.6f}°{lat_ref}, {lon_decimal:.6f}°{lon_ref}"
        except Exception:
            pass
        
        return None

