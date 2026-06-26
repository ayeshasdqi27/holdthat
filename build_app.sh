#!/bin/bash
# Builds TempNoteTaker into a standalone macOS App and packages it into a styled DMG.
set -e

# Change directory to script location
cd "$(dirname "$0")"

# 1. Clean previous build artifacts
echo "Cleaning up old build artifacts..."
rm -rf build dist TempNoteTaker.app

# 2. Ensure py2app is installed in the user Python environment
if ! python3 -c "import py2app" &>/dev/null; then
    echo "py2app is not installed. Installing it via pip..."
    python3 -m pip install --user py2app
fi

# 3. Build standalone .app bundle
echo "Building standalone application bundle..."
python3 setup.py py2app

# Verify bundle was created
if [ ! -d "dist/TempNoteTaker.app" ]; then
    echo "Error: Build failed. dist/TempNoteTaker.app not found."
    exit 1
fi
echo "✓ Standalone TempNoteTaker.app built successfully."

# 4. Apply ad-hoc code signature (required for Apple Silicon Macs)
echo "Applying ad-hoc code-signing to the bundle..."
codesign --force --deep --sign - dist/TempNoteTaker.app
echo "✓ Code signing complete."

# 5. Create Styled DMG installer package
echo "Assembling DMG package..."
DMG_STAGE="dist/dmg_stage"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"

# Copy the app to stage
cp -R dist/TempNoteTaker.app "$DMG_STAGE/"

# Create symlink to /Applications for easy drag-and-drop
ln -s /Applications "$DMG_STAGE/Applications"

# Add installation helper instructions file
cat << 'EOF' > "$DMG_STAGE/How to Install.txt"
To install and run Today Notes (TempNoteTaker):

1. Drag the "Today Notes" app icon into your "Applications" folder.
2. Open your "Applications" folder in Finder.
3. Instead of double-clicking, RIGHT-CLICK (or Control-Click) the "Today Notes" app icon and choose "Open".
4. A dialog will pop up stating that macOS cannot verify the developer. Click "Open" to confirm and launch the app.

This bypasses macOS Gatekeeper since the app is distributed directly outside the Mac App Store. You only need to perform this Right-Click -> Open step once.
EOF

# Create a temporary read-write disk image
echo "Creating temporary read-write disk image..."
TEMP_DMG="dist/pack.temp.dmg"
rm -f "$TEMP_DMG"
hdiutil create -srcfolder "$DMG_STAGE" -volname "Today Notes" -fs HFS+ -format UDRW -ov "$TEMP_DMG"

# Mount the temporary disk image (default location, which will be /Volumes/Today Notes)
echo "Mounting temporary disk image..."
device=$(hdiutil attach "$TEMP_DMG" -readwrite -noverify -noautoopen | egrep '^/dev/' | head -n 1 | awk '{print $1}')
sleep 2

# Copy custom background image to disk image (under hidden folder)
echo "Setting custom background image..."
mkdir -p "/Volumes/Today Notes/.background"
cp Ref/dmg_background.png "/Volumes/Today Notes/.background/background.png"

# Run AppleScript to layout DMG window beautifully in Finder
echo "Styling DMG Finder window..."
osascript -e '
tell application "Finder"
    tell disk "Today Notes"
        open
        delay 1
        set the_window to container window
        set current view of the_window to icon view
        set toolbar visible of the_window to false
        set statusbar visible of the_window to false
        set bounds of the_window to {100, 100, 700, 500} -- width 600, height 400
        set theViewOptions to icon view options of the_window
        set icon size of theViewOptions to 96
        set arrangement of theViewOptions to not arranged
        set background picture of theViewOptions to file ".background:background.png"
        delay 1
        set position of item "TempNoteTaker.app" to {150, 200}
        set position of item "Applications" to {450, 200}
        set position of item "How to Install.txt" to {300, 310}
        delay 2
        close
    end tell
end tell
' || echo "Warning: Finder layout configuration skipped (can occur in headless or locked sessions)."

# Unmount the temporary disk image using the device node
echo "Unmounting temporary disk image..."
hdiutil detach "$device"

# Convert the read-write disk image into the final compressed DMG
echo "Converting to compressed read-only DMG (dist/hold-that.dmg)..."
rm -f dist/hold-that.dmg
hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o dist/hold-that.dmg

# Clean up staging and temporary files
rm -rf "$DMG_STAGE"
rm -f "$TEMP_DMG"

echo "✓ Packaging complete! Generated a styled dist/hold-that.dmg"
