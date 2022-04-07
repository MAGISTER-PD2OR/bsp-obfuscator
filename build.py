import PyInstaller.__main__
import os
from shutil import copy, make_archive

args = ["src/__main__.py",
        "-p", "src",
        "-n", "BSP-Obfuscator",
        "-F",
        "--distpath", "./dist/BSP-Obfuscator",
        "--icon", "./assets/icon.ico"]

PyInstaller.__main__.run(args)

copy('./assets/compilepal/meta.json', "./dist/BSP-Obfuscator")
copy('./assets/compilepal/parameters.json', "./dist/BSP-Obfuscator")

try:
    os.remove("BSP-Obfuscator.zip")
except OSError:
    pass
make_archive("BSP-Obfuscator", "zip", "dist")
