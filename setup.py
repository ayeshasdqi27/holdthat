from setuptools import setup

APP = ['tempnotetaker.py']
DATA_FILES = [
    ('Ref', [
        'Ref/background.svg',
        'Ref/Dotted pattern.svg',
        'Ref/Yesterday background.svg',
        'Ref/yesterday gradient.svg',
        'Ref/today highlight.png',
        'Ref/date underline.png',
        'Ref/disclaimer.png',
        'Ref/holdthat.png',
    ])
]
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'LSUIElement': True,  # Keep the app as a background agent (no Dock icon)
        'CFBundleIdentifier': 'com.ayesha.TempNoteTaker',
        'CFBundleName': 'TempNoteTaker',
        'CFBundleDisplayName': 'Today Notes',
        'CFBundleVersion': '1',
        'CFBundleShortVersionString': '1.0',
    },
    'iconfile': 'Ref/AppIcon.icns',
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
