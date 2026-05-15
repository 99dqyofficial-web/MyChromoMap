"""
Download Noto CJK SC fonts and subset to common Chinese characters.
Subset includes: GB2312 level 1 (3755) + level 2 (3008) ≈ 6763 chars
+ Latin letters, digits, common punctuation.
"""
import os
import sys
import urllib.request
import zipfile
import tempfile
import shutil

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'python', 'fonts')
os.makedirs(FONTS_DIR, exist_ok=True)

CJK_CHARS = set()

# Latin letters, digits, basic punctuation
for cp in range(0x0020, 0x007F):
    CJK_CHARS.add(cp)
for cp in range(0x00A0, 0x0100):
    CJK_CHARS.add(cp)
for cp in range(0x2000, 0x2070):
    CJK_CHARS.add(cp)
for cp in range(0x2100, 0x2150):
    CJK_CHARS.add(cp)
for cp in range(0x2200, 0x2300):
    CJK_CHARS.add(cp)
for cp in range(0x3000, 0x303F):
    CJK_CHARS.add(cp)
for cp in range(0xFF00, 0xFFEF):
    CJK_CHARS.add(cp)

# CJK Unified Ideographs (common block)
for cp in range(0x4E00, 0x9FFF):
    CJK_CHARS.add(cp)

# CJK Compatibility Ideographs (a few common ones)
for cp in range(0xF900, 0xFA2E):
    CJK_CHARS.add(cp)


def download_and_subset(font_name, url, output_name):
    output_path = os.path.join(FONTS_DIR, output_name)
    if os.path.exists(output_path):
        print(f'{output_name} already exists, skipping')
        return True

    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, 'font.zip')

    try:
        print(f'Downloading {font_name}...')
        urllib.request.urlretrieve(url, zip_path)

        print(f'Extracting...')
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tmp_dir)

        otf_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for f in files:
                if f.endswith('Regular.otf') and font_name.replace(' ', '') in f.replace(' ', ''):
                    otf_files.append(os.path.join(root, f))

        if not otf_files:
            for root, dirs, files in os.walk(tmp_dir):
                for f in files:
                    if f.endswith('Regular.otf'):
                        otf_files.append(os.path.join(root, f))

        if not otf_files:
            print(f'No Regular OTF found for {font_name}')
            return False

        src_path = otf_files[0]
        print(f'Subsetting {font_name} ({os.path.basename(src_path)})...')
        print(f'Characters in subset: {len(CJK_CHARS)}')

        from fontTools.subset import Subsetter, Options
        from fontTools.ttLib import TTFont

        font = TTFont(src_path, lazy=True)
        subsetter = Subsetter()
        subsetter.populate(unicodes=CJK_CHARS)
        subsetter.subset(font)
        font.save(output_path)
        print(f'Saved: {output_path} ({os.path.getsize(output_path) / 1024:.0f} KB)')
        return True

    except Exception as e:
        print(f'Error processing {font_name}: {e}')
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    fonts = [
        ('NotoSerifCJKsc', 'https://github.com/notofonts/noto-cjk/releases/download/Serif2.003/09_NotoSerifCJKsc.zip', 'NotoSerifCJKsc-Regular.otf'),
        ('NotoSansCJKsc', 'https://github.com/notofonts/noto-cjk/releases/download/Sans2.004/08_NotoSansCJKsc.zip', 'NotoSansCJKsc-Regular.otf'),
    ]

    success = True
    for name, url, out in fonts:
        if not download_and_subset(name, url, out):
            success = False

    if success:
        print('\nAll fonts downloaded and subset successfully!')
    else:
        print('\nSome fonts failed. Check errors above.')
        sys.exit(1)
