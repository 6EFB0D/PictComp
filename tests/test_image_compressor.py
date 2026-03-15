# -*- coding: utf-8 -*-
"""
image_compressor モジュールのユニットテスト
"""
import os
import tempfile
import unittest
from PIL import Image

from image_compressor import CompressionSettings, ImageCompressor


def create_test_jpeg(path: str, width: int = 800, height: int = 600, quality: int = 90) -> str:
    """テスト用JPEG画像を作成"""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(path, format="JPEG", quality=quality)
    return path


def create_test_png(path: str, width: int = 400, height: int = 300) -> str:
    """テスト用PNG画像を作成"""
    img = Image.new("RGBA", (width, height), color=(255, 0, 0, 128))
    img.save(path, format="PNG")
    return path


class TestCompressionSettings(unittest.TestCase):
    """CompressionSettings のテスト"""

    def test_default_values(self):
        """デフォルト値の確認"""
        settings = CompressionSettings()
        self.assertEqual(settings.target_size_kb, 300)
        self.assertEqual(settings.jpeg_quality, 85)
        self.assertIsNone(settings.max_dimension)
        self.assertEqual(settings.output_format, "auto")

    def test_to_dict(self):
        """to_dict のテスト"""
        settings = CompressionSettings()
        settings.target_size_kb = 200
        settings.jpeg_quality = 80
        data = settings.to_dict()
        self.assertEqual(data["target_size_kb"], 200)
        self.assertEqual(data["jpeg_quality"], 80)
        self.assertIn("output_format", data)

    def test_from_dict(self):
        """from_dict のテスト"""
        settings = CompressionSettings()
        data = {"target_size_kb": 150, "jpeg_quality": 75, "max_dimension": 1920}
        settings.from_dict(data)
        self.assertEqual(settings.target_size_kb, 150)
        self.assertEqual(settings.jpeg_quality, 75)
        self.assertEqual(settings.max_dimension, 1920)

    def test_roundtrip(self):
        """to_dict / from_dict の往復テスト"""
        original = CompressionSettings()
        original.target_size_kb = 500
        original.max_dimension = 2400
        original.output_format = "webp"
        data = original.to_dict()
        restored = CompressionSettings()
        restored.from_dict(data)
        self.assertEqual(restored.target_size_kb, original.target_size_kb)
        self.assertEqual(restored.max_dimension, original.max_dimension)
        self.assertEqual(restored.output_format, original.output_format)


class TestImageCompressorResize(unittest.TestCase):
    """ImageCompressor.resize_image のテスト"""

    def test_no_resize_when_max_dimension_none(self):
        """max_dimension が None の場合はリサイズしない"""
        settings = CompressionSettings()
        settings.max_dimension = None
        compressor = ImageCompressor(settings)
        img = Image.new("RGB", (800, 600), color="red")
        result = compressor.resize_image(img)
        self.assertEqual(result.size, (800, 600))

    def test_no_resize_when_smaller_than_max(self):
        """画像が max_dimension より小さい場合はリサイズしない"""
        settings = CompressionSettings()
        settings.max_dimension = 1920
        compressor = ImageCompressor(settings)
        img = Image.new("RGB", (800, 600), color="red")
        result = compressor.resize_image(img)
        self.assertEqual(result.size, (800, 600))

    def test_resize_landscape(self):
        """横長画像のリサイズ"""
        settings = CompressionSettings()
        settings.max_dimension = 400
        compressor = ImageCompressor(settings)
        img = Image.new("RGB", (800, 600), color="red")
        result = compressor.resize_image(img)
        self.assertEqual(result.size, (400, 300))

    def test_resize_portrait(self):
        """縦長画像のリサイズ"""
        settings = CompressionSettings()
        settings.max_dimension = 300
        compressor = ImageCompressor(settings)
        img = Image.new("RGB", (600, 800), color="red")
        result = compressor.resize_image(img)
        self.assertEqual(result.size, (225, 300))


class TestImageCompressorDetermineFormat(unittest.TestCase):
    """ImageCompressor.determine_output_format のテスト"""

    def test_auto_jpeg_from_jpg(self):
        """auto で .jpg 入力 → jpg 出力"""
        settings = CompressionSettings()
        settings.output_format = "auto"
        compressor = ImageCompressor(settings)
        self.assertEqual(compressor.determine_output_format("/path/to/image.jpg", ".jpg"), "jpg")

    def test_auto_jpeg_from_heic(self):
        """auto で .heic 入力 → jpg 出力"""
        settings = CompressionSettings()
        settings.output_format = "auto"
        compressor = ImageCompressor(settings)
        self.assertEqual(compressor.determine_output_format("/path/to/image.heic", ".heic"), "jpg")

    def test_auto_png_from_png(self):
        """auto で .png 入力 → png 出力"""
        settings = CompressionSettings()
        settings.output_format = "auto"
        compressor = ImageCompressor(settings)
        self.assertEqual(compressor.determine_output_format("/path/to/image.png", ".png"), "png")

    def test_explicit_format(self):
        """明示的な出力形式指定"""
        settings = CompressionSettings()
        settings.output_format = "webp"
        compressor = ImageCompressor(settings)
        self.assertEqual(compressor.determine_output_format("/path/to/image.jpg", ".jpg"), "webp")


class TestImageCompressorCompress(unittest.TestCase):
    """ImageCompressor.compress_image のテスト"""

    def setUp(self):
        """各テストの前処理"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """各テストの後処理"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_compress_jpeg_success(self):
        """JPEG圧縮の成功"""
        input_path = os.path.join(self.temp_dir, "test.jpg")
        output_path = os.path.join(self.temp_dir, "output.jpg")
        create_test_jpeg(input_path, width=800, height=600)

        settings = CompressionSettings()
        settings.output_format = "jpg"
        settings.jpeg_quality = 85
        compressor = ImageCompressor(settings)

        success, result = compressor.compress_image(input_path, output_path)

        self.assertTrue(success)
        self.assertEqual(result["format"], "jpg")
        self.assertGreater(result["input_size"], 0)
        self.assertGreater(result["output_size"], 0)
        self.assertIn("output_path", result)
        self.assertTrue(os.path.exists(result["output_path"]))

    def test_compress_png_success(self):
        """PNG圧縮の成功"""
        input_path = os.path.join(self.temp_dir, "test.png")
        output_path = os.path.join(self.temp_dir, "output.png")
        create_test_png(input_path, width=400, height=300)

        settings = CompressionSettings()
        settings.output_format = "png"
        compressor = ImageCompressor(settings)

        success, result = compressor.compress_image(input_path, output_path)

        self.assertTrue(success)
        self.assertEqual(result["format"], "png")
        self.assertGreater(result["input_size"], 0)
        self.assertGreater(result["output_size"], 0)

    def test_compress_nonexistent_file(self):
        """存在しないファイルの圧縮"""
        settings = CompressionSettings()
        compressor = ImageCompressor(settings)
        output_path = os.path.join(self.temp_dir, "output.jpg")

        success, result = compressor.compress_image("/nonexistent/path/image.jpg", output_path)

        self.assertFalse(success)
        self.assertIsNotNone(result["error"])

    def test_compress_with_resize(self):
        """リサイズ付き圧縮"""
        input_path = os.path.join(self.temp_dir, "test.jpg")
        output_path = os.path.join(self.temp_dir, "output.jpg")
        create_test_jpeg(input_path, width=1600, height=1200)

        settings = CompressionSettings()
        settings.output_format = "jpg"
        settings.max_dimension = 400
        compressor = ImageCompressor(settings)

        success, result = compressor.compress_image(input_path, output_path)

        self.assertTrue(success)
        # 出力画像のサイズを確認
        from PIL import Image
        output_img = Image.open(result["output_path"])
        self.assertLessEqual(max(output_img.size), 400)


if __name__ == "__main__":
    unittest.main()
