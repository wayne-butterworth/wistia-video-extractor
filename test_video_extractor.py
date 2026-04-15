import os
import tempfile
import unittest
from pathlib import Path

from video_extractor import (
    extract_video_id,
    get_embed_url,
    find_bin_url,
    extract_filename,
    get_unique_filename,
)


class TestVideoExtractor(unittest.TestCase):
    def test_extract_video_id_from_html(self):
        html = '<a href="https://example.com?wvideo=abcd1234">Play</a>'
        self.assertEqual(extract_video_id(html), 'abcd1234')

    def test_get_embed_url(self):
        self.assertEqual(
            get_embed_url('abcd1234'),
            'https://fast.wistia.net/embed/iframe/abcd1234?videoFoam=true',
        )

    def test_find_bin_url_converts_to_mp4(self):
        content = '...https://embed-ssl.wistia.com/deliveries/abcde12345.bin...'
        self.assertEqual(
            find_bin_url(content),
            'https://embed-ssl.wistia.com/deliveries/abcde12345.mp4',
        )

    def test_extract_filename_from_anchor_text(self):
        html = '<p><a href="#">my video.mp4</a></p>'
        self.assertEqual(extract_filename(html), 'my video')

    def test_extract_filename_from_plain_text(self):
        html = 'Download this video: my_video.mp4 now'
        self.assertEqual(extract_filename(html), 'my_video')

    def test_extract_filename_returns_none_when_missing(self):
        html = '<p>No filename here</p>'
        self.assertIsNone(extract_filename(html))

    def test_get_unique_filename_appends_counter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            current_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                Path('video.mp4').write_text('dummy')
                Path('video-1.mp4').write_text('dummy')
                self.assertEqual(get_unique_filename('video'), 'video-2')
                self.assertEqual(get_unique_filename('video.mp4'), 'video-2')
            finally:
                os.chdir(current_dir)


if __name__ == '__main__':
    unittest.main()
