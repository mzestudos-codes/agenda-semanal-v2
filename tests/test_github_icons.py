import io
import unittest
from PIL import Image
from app.github_icons import validate_png, validate_company, GitHubIconError, icon_names

class IconManagementTests(unittest.TestCase):
    def png(self,size=(119,50)):
        out=io.BytesIO();Image.new('RGBA',size,(0,0,0,0)).save(out,'PNG');return out.getvalue()
    def test_valid_png(self):validate_png(self.png())
    def test_invalid_size(self):
        with self.assertRaisesRegex(GitHubIconError,'119 × 50'):validate_png(self.png((120,50)))
    def test_invalid_bytes(self):
        with self.assertRaises(GitHubIconError):validate_png(b'not png')
    def test_traversal(self):
        for name in ('../abc','a/b','CON','x\\y',''):
            with self.subTest(name=name),self.assertRaises(GitHubIconError):validate_company(name)
    def test_names_exclude_internal_icons(self):
        idx={'icones/abc.png':('Icones/abc.png','hash'),'icones/mz/x.png':('Icones/MZ/x.png','hash')}
        self.assertEqual(icon_names(idx),['abc'])
if __name__=='__main__':unittest.main()
