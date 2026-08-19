import os
import sys
import subprocess
from PIL import Image


def create_ico():
    """Convert icon.png to icon.ico if it exists"""
    if os.path.exists('icon.png'):
        print("Converting icon.png to icon.ico...")
        img = Image.open('icon.png')
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        return 'icon.ico'
    return None


def build():
    """Build lightweight standalone executable using Nuitka."""
    icon_path = create_ico()

    cmd = [
        sys.executable, '-m', 'nuitka',
        '--standalone',
        '--onefile',
        '--windows-console-mode=disable',
        '--enable-plugin=tk-inter',
        '--include-package=customtkinter',
        '--include-package-data=customtkinter',
        '--include-package=darkdetect',
        '--include-package=PIL',
        '--include-package=requests',
        '--include-package=bs4',
        '--include-package=pygments',
        '--include-package=src',
        '--output-filename=StackOverflowGUI.exe',
        'main.py'
    ]

    if icon_path and os.path.exists(icon_path):
        cmd.append(f'--windows-icon-from-ico={icon_path}')

    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)


if __name__ == '__main__':
    build()
