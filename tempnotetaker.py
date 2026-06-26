#!/usr/bin/env python3
"""
TempNoteTaker - macOS menu bar note-taking app.

A filing folder system design app. One tab is 'Today' (blue folder) and
the other is 'Yesterday' (tan folder). Rollover occurs at midnight.
Click outside or press Escape to dismiss.
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

# Setup resource path for py2app or development mode
if "RESOURCEPATH" in os.environ:
    BASE_DIR = Path(os.environ["RESOURCEPATH"])
else:
    BASE_DIR = Path(__file__).parent.resolve()

REF_DIR = BASE_DIR / "Ref"

import objc
from Cocoa import (
    NSAffineTransform,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSButton,
    NSColor,
    NSEvent,
    NSEventMaskKeyDown,
    NSEventMaskLeftMouseDown,
    NSEventMaskRightMouseDown,
    NSEventModifierFlagCommand,
    NSFont,
    NSFontAttributeName,
    NSFontManager,
    NSForegroundColorAttributeName,
    NSGraphicsContext,
    NSImage,
    NSImageInterpolationHigh,
    NSItalicFontMask,
    NSMakePoint,
    NSMakeRect,
    NSMakeSize,
    NSPanel,
    NSScrollView,
    NSStatusBar,
    NSStatusWindowLevel,
    NSTextField,
    NSTextView,
    NSView,
    NSViewWidthSizable,
    NSVariableStatusItemLength,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSObject, NSNotificationCenter, NSString
from PyObjCTools import AppHelper


# --- Constants ---------------------------------------------------------------
COLOR_BLUE = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.27, 0.47, 0.76, 1.0)
COLOR_YESTERDAY_BG = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.12, 0.12, 0.12, 1.0)
COLOR_DARK_TEXT = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.30, 0.27, 0.23, 1.0)
PLACEHOLDER_GREY = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, 1, 0.45)
COLOR_GOLD = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.75, 0.21, 1.0)

PANEL_W = 450
PANEL_H = 600
FOLDER_W = 406
FOLDER_H = PANEL_H
BODY_RADIUS = 16
TAB_W = 44
TAB_H = 96
TAB_RADIUS = 8
TAB_CENTER_X = FOLDER_W / 2

STATUS_W = 30
STATUS_H = 18

NOTES_DIR = Path.home() / "Library" / "Application Support" / "TempNoteTaker"
NOTES_FILE = NOTES_DIR / "notes.txt"
NOTES_JSON_FILE = NOTES_DIR / "notes.json"


def get_dm_mono_font(size, weight_type="regular"):
    font_name = "DMMono-Regular"
    if weight_type == "medium":
        font_name = "DMMono-Medium"
    elif weight_type == "light":
        font_name = "DMMono-Light"
        
    font = NSFont.fontWithName_size_(font_name, size)
    if font:
        return font
        
    font = NSFont.fontWithName_size_("DM Mono", size)
    if font:
        return font
        
    # Fallback to system monospaced
    weight_val = 0.0
    if weight_type == "medium":
        weight_val = 0.23
    elif weight_type == "light":
        weight_val = -0.4
        
    return NSFont.monospacedSystemFontOfSize_weight_(size, weight_val)


# --- Subclasses --------------------------------------------------------------
class KeyablePanel(NSPanel):
    """Borderless panel that can still accept keyboard focus for the editor."""

    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True


class NotchView(NSView):
    """Filing system background view that draws the folder body and vertical tabs."""

    active_tab = "today"
    bg_image = None
    dots_image = None
    yesterday_lines_image = None
    yesterday_gradient_image = None
    today_highlight_image = None
    date_underline_image = None
    disclaimer_image = None

    def drawRect_(self, rect):
        bounds = self.bounds()
        FOLDER_H = bounds.size.height
        
        active_tab = getattr(self, "active_tab", "today")

        # Define coordinates for tabs and folder body
        today_rect = NSMakeRect(FOLDER_W - 10, FOLDER_H - 116, TAB_W + 10, TAB_H)
        yesterday_rect = NSMakeRect(FOLDER_W - 10, FOLDER_H - 216, TAB_W + 10, TAB_H)

        body_rect = NSMakeRect(0, 0, FOLDER_W, FOLDER_H)
        body_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(body_rect, BODY_RADIUS, BODY_RADIUS)

        # 1. Draw Inactive Tab background first (behind body)
        if active_tab == "today":
            # Yesterday is inactive
            COLOR_YESTERDAY_BG.setFill()
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(yesterday_rect, TAB_RADIUS, TAB_RADIUS)
            path.fill()
        else:
            # Today is inactive
            COLOR_BLUE.setFill()
            path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(today_rect, TAB_RADIUS, TAB_RADIUS)
            path.fill()

        # 2. Draw Main Folder Body & Active Tab combined (so backgrounds flow seamlessly)
        context = NSGraphicsContext.currentContext()
        context.saveGraphicsState()

        clip_path = NSBezierPath.bezierPath()
        clip_path.appendBezierPath_(body_path)

        if active_tab == "today":
            active_tab_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(today_rect, TAB_RADIUS, TAB_RADIUS)
            clip_path.appendBezierPath_(active_tab_path)
        else:
            active_tab_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(yesterday_rect, TAB_RADIUS, TAB_RADIUS)
            clip_path.appendBezierPath_(active_tab_path)

        clip_path.addClip()

        if active_tab == "today":
            # Draw gradient background SVG and dotted pattern SVG on top
            if self.bg_image:
                self.bg_image.drawInRect_(NSMakeRect(0, 0, PANEL_W, PANEL_H))
            else:
                COLOR_BLUE.setFill()
                clip_path.fill()

            if self.dots_image:
                self.dots_image.drawInRect_(NSMakeRect(0, 0, PANEL_W, PANEL_H))
        else:
            # Draw gradient background SVG or fallback to solid dark grey
            if self.yesterday_gradient_image:
                self.yesterday_gradient_image.drawInRect_(NSMakeRect(0, 0, PANEL_W, PANEL_H))
            else:
                COLOR_YESTERDAY_BG.setFill()
                clip_path.fill()
            
            if self.yesterday_lines_image:
                self.yesterday_lines_image.drawInRect_(NSMakeRect(0, 0, PANEL_W, PANEL_H))
                
            if self.disclaimer_image:
                context = NSGraphicsContext.currentContext()
                context.saveGraphicsState()
                context.setImageInterpolation_(NSImageInterpolationHigh)
                # Center horizontally inside the folder body (width: 406), y = 12
                disclaimer_rect = NSMakeRect(203 - 308.0 / 2.0, 12, 308.0, 15.0)
                self.disclaimer_image.drawInRect_(disclaimer_rect)
                context.restoreGraphicsState()

        context.restoreGraphicsState()

        # 3. Draw Tab Text (vertical, rotated 90 degrees)
        font_today = get_dm_mono_font(13, "medium" if active_tab == "today" else "regular")
        font_yesterday = get_dm_mono_font(13, "medium" if active_tab == "yesterday" else "regular")

        today_text_color = NSColor.whiteColor() if active_tab == "today" else NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.6)
        yesterday_text_color = NSColor.whiteColor() if active_tab == "yesterday" else NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.6)

        self.draw_vertical_text("today", today_rect, today_text_color, font_today)
        self.draw_vertical_text("yesterday", yesterday_rect, yesterday_text_color, font_yesterday)

        # 4. Draw Today Highlight if active and image is loaded
        if active_tab == "today" and self.today_highlight_image:
            context = NSGraphicsContext.currentContext()
            context.saveGraphicsState()
            context.setImageInterpolation_(NSImageInterpolationHigh)
            cx = FOLDER_W + (today_rect.size.width - 10) / 2.0
            cy = today_rect.origin.y + today_rect.size.height / 2.0
            img_w, img_h = 36.0, 79.0
            highlight_rect = NSMakeRect(cx - img_w / 2.0, cy - img_h / 2.0, img_w, img_h)
            self.today_highlight_image.drawInRect_(highlight_rect)
            context.restoreGraphicsState()

        # 5. Draw Date text and hand-drawn underline at the top right of the folder page
        if active_tab == "today":
            active_date = date.today()
        else:
            active_date = date.today() - timedelta(days=1)
        
        date_str = f"{active_date.strftime('%B')} {active_date.day}".lower()
        base_font = get_dm_mono_font(13, "regular")
        italic_font = NSFontManager.sharedFontManager().convertFont_toHaveTrait_(base_font, NSItalicFontMask)
        
        date_color = COLOR_GOLD if active_tab == "today" else NSColor.whiteColor()
        attrs = {
            NSForegroundColorAttributeName: date_color,
            NSFontAttributeName: italic_font,
        }
        
        ns_date_str = NSString.stringWithString_(date_str)
        date_size = ns_date_str.sizeWithAttributes_(attrs)
        
        # Draw date text aligned to the right margin (matching scroll view width boundaries)
        draw_x = (FOLDER_W - 18) - date_size.width
        draw_y = 572.0
        ns_date_str.drawAtPoint_withAttributes_(NSMakePoint(draw_x, draw_y), attrs)
        
        # Draw underline image centered/aligned under the text
        if self.date_underline_image:
            context = NSGraphicsContext.currentContext()
            context.saveGraphicsState()
            context.setImageInterpolation_(NSImageInterpolationHigh)
            underline_rect = NSMakeRect(draw_x, draw_y - 8, date_size.width, 12)
            self.date_underline_image.drawInRect_(underline_rect)
            context.restoreGraphicsState()

    def draw_vertical_text(self, text, rect, color, font):
        context = NSGraphicsContext.currentContext()
        context.saveGraphicsState()

        cx = FOLDER_W + (rect.size.width - 10) / 2.0
        cy = rect.origin.y + rect.size.height / 2.0

        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(cx, cy)
        transform.rotateByDegrees_(90.0)
        transform.concat()

        attrs = {
            NSForegroundColorAttributeName: color,
            NSFontAttributeName: font,
        }

        title_str = NSString.stringWithString_(text)
        title_size = title_str.sizeWithAttributes_(attrs)

        draw_x = -title_size.width / 2.0
        draw_y = -title_size.height / 2.0
        title_str.drawAtPoint_withAttributes_(NSMakePoint(draw_x, draw_y), attrs)

        context.restoreGraphicsState()


class TabButton(NSButton):
    """Transparent button overlaid on right-side tabs to capture click events."""

    def init_transparent(self):
        self.setBordered_(False)
        self.setTitle_("")
        return self

    def drawRect_(self, rect):
        pass


# --- App delegate ------------------------------------------------------------
class AppDelegate(NSObject):
    status_item = objc.ivar()
    panel = objc.ivar()
    bg_view = objc.ivar()
    text_view = objc.ivar()
    placeholder = objc.ivar()
    today_tab = objc.ivar()
    yesterday_tab = objc.ivar()
    current_tab = objc.ivar()
    global_monitor = objc.ivar()
    local_monitor = objc.ivar()

    def applicationDidFinishLaunching_(self, notification):
        NOTES_DIR.mkdir(parents=True, exist_ok=True)
        self.current_tab = "today"

        # Status bar tab
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self.status_item.button()
        button.setImage_(self._make_tab_icon())
        button.image().setTemplate_(False)
        button.setAction_("togglePanel:")
        button.setTarget_(self)

        # Panel
        rect = NSMakeRect(0, 0, PANEL_W, PANEL_H)
        style = NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel
        self.panel = KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            rect, style, NSBackingStoreBuffered, False
        )
        self.panel.setOpaque_(False)
        self.panel.setBackgroundColor_(NSColor.clearColor())
        self.panel.setHasShadow_(True)
        self.panel.setLevel_(NSStatusWindowLevel)
        self.panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        self.panel.setMovableByWindowBackground_(False)
        self.panel.setHidesOnDeactivate_(False)

        bg = NotchView.alloc().initWithFrame_(rect)
        self.panel.contentView().addSubview_(bg)
        self.bg_view = bg

        # Load custom backgrounds
        ref_dir = REF_DIR
        bg.bg_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "background.svg"))
        bg.dots_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "Dotted pattern.svg"))
        bg.yesterday_lines_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "Yesterday background.svg"))
        bg.yesterday_gradient_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "yesterday gradient.svg"))
        bg.today_highlight_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "today highlight.png"))
        bg.date_underline_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "date underline.png"))
        bg.disclaimer_image = NSImage.alloc().initWithContentsOfFile_(str(ref_dir / "disclaimer.png"))

        # Transparent tab buttons placed over the drawn tabs on the right side
        self.today_tab = TabButton.alloc().initWithFrame_(NSMakeRect(FOLDER_W, FOLDER_H - 116, TAB_W, TAB_H))
        self.today_tab.init_transparent()
        self.today_tab.setTarget_(self)
        self.today_tab.setAction_("switchTab:")
        bg.addSubview_(self.today_tab)

        self.yesterday_tab = TabButton.alloc().initWithFrame_(NSMakeRect(FOLDER_W, FOLDER_H - 216, TAB_W, TAB_H))
        self.yesterday_tab.init_transparent()
        self.yesterday_tab.setTarget_(self)
        self.yesterday_tab.setAction_("switchTab:")
        bg.addSubview_(self.yesterday_tab)

        # Scroll view + text view for the note body
        scroll_rect = NSMakeRect(18, 18, FOLDER_W - 36, FOLDER_H - 54)
        scroll = NSScrollView.alloc().initWithFrame_(scroll_rect)
        scroll.setHasVerticalScroller_(True)
        scroll.setBorderType_(0)
        scroll.setDrawsBackground_(False)
        scroll.setAutohidesScrollers_(True)

        text_rect = NSMakeRect(0, 0, scroll_rect.size.width, scroll_rect.size.height)
        tv = NSTextView.alloc().initWithFrame_(text_rect)
        tv.setBackgroundColor_(NSColor.clearColor())
        tv.setDrawsBackground_(False)
        tv.setTextColor_(NSColor.whiteColor())
        tv.setInsertionPointColor_(NSColor.whiteColor())
        tv.setFont_(get_dm_mono_font(14, "regular"))
        tv.setRichText_(False)
        tv.setAutoresizingMask_(NSViewWidthSizable)
        tv.setMinSize_(NSMakeSize(0, 0))
        tv.setMaxSize_(NSMakeSize(1e9, 1e9))
        tv.setVerticallyResizable_(True)
        tv.setHorizontallyResizable_(False)
        tv.setTextContainerInset_(NSMakeSize(4, 4))
        scroll.setDocumentView_(tv)
        bg.addSubview_(scroll)
        self.text_view = tv

        # Placeholder text overlay aligned with the editor cursor
        ph = NSTextField.alloc().initWithFrame_(
            NSMakeRect(scroll_rect.origin.x + 7,
                       scroll_rect.origin.y + scroll_rect.size.height - 23,
                       scroll_rect.size.width - 14, 22)
        )
        ph.setStringValue_("Type a note…")
        ph.setFont_(get_dm_mono_font(14, "regular"))
        ph.setTextColor_(PLACEHOLDER_GREY)
        ph.setBackgroundColor_(NSColor.clearColor())
        ph.setBezeled_(False)
        ph.setEditable_(False)
        ph.setSelectable_(False)
        ph.setDrawsBackground_(False)
        bg.addSubview_(ph)
        self.placeholder = ph

        self._check_and_transition_date()
        self._refresh_ui_from_data()

        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "textChanged:", "NSTextDidChangeNotification", tv
        )
        NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "dayChanged:", "NSCalendarDayChangedNotification", None
        )

    # --- Actions -----------------------------------------------------------
    def togglePanel_(self, sender):
        if self.panel.isVisible():
            self._hide_panel()
        else:
            self._show_panel()

    togglePanel_ = objc.selector(togglePanel_, signature=b"v@:@")

    def textChanged_(self, note):
        self._save_active_notes()
        self._update_placeholder()

    textChanged_ = objc.selector(textChanged_, signature=b"v@:@")

    def switchTab_(self, sender):
        new_tab = "today" if sender == self.today_tab else "yesterday"
        if self.current_tab == new_tab:
            return

        self._save_active_notes()
        self.current_tab = new_tab

        self._refresh_ui_from_data()
        self.panel.makeFirstResponder_(self.text_view)

    switchTab_ = objc.selector(switchTab_, signature=b"v@:@")

    def dayChanged_(self, notification):
        self._check_and_transition_date()

    dayChanged_ = objc.selector(dayChanged_, signature=b"v@:@")

    # --- Panel management --------------------------------------------------
    def _show_panel(self):
        self._check_and_transition_date()

        button = self.status_item.button()
        button_window = button.window()
        button_bounds = button.bounds()
        win_rect = button.convertRect_toView_(button_bounds, None)
        screen_rect = button_window.convertRectToScreen_(win_rect)

        # Slide the panel so its folder body is positioned under the status item,
        # adding a vertical gap to clear the camera notch and shifting it to the right.
        status_center_x = screen_rect.origin.x + screen_rect.size.width / 2
        x = status_center_x - TAB_CENTER_X + 25
        y = screen_rect.origin.y - PANEL_H - 10
        self.panel.setFrame_display_(NSMakeRect(x, y, PANEL_W, PANEL_H), True)

        NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        self.panel.makeKeyAndOrderFront_(None)
        self.panel.makeFirstResponder_(self.text_view)
        self._update_placeholder()

        self.global_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSEventMaskLeftMouseDown | NSEventMaskRightMouseDown,
            lambda event: self._hide_panel(),
        )

        def key_handler(event):
            if event.keyCode() == 53:
                self._hide_panel()
                return None

            # Intercept Cmd shortcuts for copy/paste/cut/selectAll
            flags = event.modifierFlags()
            if flags & NSEventModifierFlagCommand:
                chars = event.charactersIgnoringModifiers().lower()
                if chars == "c":
                    self.text_view.copy_(self)
                    return None
                elif chars == "v":
                    if self.current_tab == "today":
                        self.text_view.paste_(self)
                    return None
                elif chars == "x":
                    if self.current_tab == "today":
                        self.text_view.cut_(self)
                    return None
                elif chars == "a":
                    self.text_view.selectAll_(self)
                    return None

            return event

        self.local_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
            NSEventMaskKeyDown, key_handler
        )

    def _hide_panel(self):
        self.panel.orderOut_(None)
        if self.global_monitor is not None:
            NSEvent.removeMonitor_(self.global_monitor)
            self.global_monitor = None
        if self.local_monitor is not None:
            NSEvent.removeMonitor_(self.local_monitor)
            self.local_monitor = None

    # --- Helpers -----------------------------------------------------------
    def _make_tab_icon(self):
        ref_dir = REF_DIR
        icon_path = ref_dir / "holdthat.png"
        
        # Load the image
        img = NSImage.alloc().initWithContentsOfFile_(str(icon_path))
        if not img:
            # Fallback to empty image of compact size
            return NSImage.alloc().initWithSize_(NSMakeSize(18, STATUS_H))
            
        # Scale to standard status bar height (16 points), keeping aspect ratio
        size = img.size()
        aspect = size.width / size.height if size.height > 0 else 1.0
        h = 16.0
        w = h * aspect
        
        # Use a compact size for the returned image (e.g., w + 4 points padding)
        img_w = w + 4.0
        img_h = STATUS_H
        
        status_img = NSImage.alloc().initWithSize_(NSMakeSize(img_w, img_h))
        status_img.lockFocus()
        
        # Draw the icon centered
        context = NSGraphicsContext.currentContext()
        context.saveGraphicsState()
        context.setImageInterpolation_(NSImageInterpolationHigh)
        draw_rect = NSMakeRect(2.0, (img_h - h) / 2.0, w, h)
        img.drawInRect_(draw_rect)
        context.restoreGraphicsState()
        
        status_img.unlockFocus()
        status_img.setTemplate_(False)
        return status_img

    def _update_status_bar_icon(self):
        button = self.status_item.button()
        button.setImage_(self._make_tab_icon())

    def _update_placeholder(self):
        empty = len(str(self.text_view.string())) == 0
        self.placeholder.setHidden_(not empty)

    def _load_notes_data(self):
        if NOTES_JSON_FILE.exists():
            try:
                return json.loads(NOTES_JSON_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        data = {
            "today_date": date.today().isoformat(),
            "today_notes": "",
            "yesterday_notes": ""
        }
        if NOTES_FILE.exists():
            try:
                old_notes = NOTES_FILE.read_text(encoding="utf-8")
                data["today_notes"] = old_notes
                NOTES_FILE.unlink(missing_ok=True)
            except Exception:
                pass
        self._save_notes_data(data)
        return data

    def _save_notes_data(self, data):
        try:
            NOTES_JSON_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Error saving notes data: {e}")

    def _save_active_notes(self):
        data = self._load_notes_data()
        current_text = str(self.text_view.string())
        if self.current_tab == "today":
            data["today_notes"] = current_text
        else:
            data["yesterday_notes"] = current_text
        self._save_notes_data(data)

    def _check_and_transition_date(self):
        today = date.today()
        current_date_str = today.isoformat()
        data = self._load_notes_data()
        saved_date_str = data.get("today_date")
        if not saved_date_str:
            data["today_date"] = current_date_str
            self._save_notes_data(data)
            return
        if saved_date_str == current_date_str:
            return
        try:
            saved_date = date.fromisoformat(saved_date_str)
        except ValueError:
            data["today_date"] = current_date_str
            data["today_notes"] = ""
            data["yesterday_notes"] = ""
            self._save_notes_data(data)
            self._refresh_ui_from_data()
            return
        diff = today - saved_date
        if diff == timedelta(days=1):
            data["yesterday_notes"] = data.get("today_notes", "")
            data["today_notes"] = ""
            data["today_date"] = current_date_str
        else:
            data["yesterday_notes"] = ""
            data["today_notes"] = ""
            data["today_date"] = current_date_str
        self._save_notes_data(data)
        self._refresh_ui_from_data()

    def _refresh_ui_from_data(self):
        data = self._load_notes_data()
        scroll = self.text_view.enclosingScrollView() if hasattr(self.text_view, "enclosingScrollView") else None
        if self.current_tab == "today":
            self.text_view.setString_(data.get("today_notes", ""))
            self.placeholder.setStringValue_("Type a note…")
            self.text_view.setEditable_(True)
            self.text_view.setTextColor_(NSColor.whiteColor())
            self.text_view.setInsertionPointColor_(NSColor.whiteColor())
            self.placeholder.setTextColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.45))
            if scroll:
                scroll.setFrame_(NSMakeRect(18, 18, FOLDER_W - 36, FOLDER_H - 54))
        else:
            self.text_view.setString_(
                "\"Forever\" is a rock and roll and pop song recorded by American singer Mariah Carey for her fifth studio album, Daydream (1995). Columbia Records released it to American radio stations for airplay on June 18, 1996, as the album's fifth single. The lyrics, written by Carey, are about one's continued affection despite the end of a romantic relationship. She composed the music and produced the song with Walter Afanasieff. Described by critics as referencing American music of the 1950s and 1960s, \"Forever\" is a doo-wop-influenced sentimental ballad in the form of a waltz. Its composition includes keyboards, guitars, and programming.\n\n"
                "Music critics gave Carey's performance and the composition positive reviews; some viewed the song as unremarkable compared to others on the album. \"Forever\" reached number nine on the Billboard Hot 100 Airplay chart in the US and number 11 on the RPM Hit Tracks list in Canada. In both countries it achieved the most success on adult contemporary stations. The single entered the bottom half of charts in Australia, New Zealand, and the Netherlands. Carey performed \"Forever\" during the 1996 Daydream World Tour; her performance at the Tokyo Dome in Japan was released as the music video. Columbia later included the song on Carey's compilation album Greatest Hits (2001).\n\n"
                "One of their tracks created for Daydream, \"Forever\", is a rock and roll[5] and pop song[6] with elements of doo-wop.[7] It is a sentimental ballad with lyrics about continued affection amidst heartbreak:[8][9] \"Forever / You will always be the only one\".[10] Composed as a waltz[11] that lasts for four minutes and one second,[12] the track follows 12\n"
                "8 time signature and moves at a tempo of 63 beats per minute. Carey's vocal range spans two octaves and three semitones from the low note of E\u266d3 to the high note of F\u266f5.[13] Afanasieff produced \"Forever\" with Carey; she wrote the lyrics herself and the pair composed the music together. He also played the keyboards, provided synth bass, and programmed the drums and rhythm. Dan Shea and Gary Cirimelli added additional programming while Dann Huff played the guitars. Jay Healy and Dana Jon Chappelle engineered the song at Wallyworld and The Hit "
            )
            self.placeholder.setStringValue_("No notes from yesterday.")
            self.text_view.setEditable_(False)
            self.text_view.setTextColor_(NSColor.whiteColor())
            self.text_view.setInsertionPointColor_(NSColor.whiteColor())
            self.placeholder.setTextColor_(NSColor.colorWithCalibratedWhite_alpha_(1.0, 0.35))
            if scroll:
                scroll.setFrame_(NSMakeRect(18, 38, FOLDER_W - 36, FOLDER_H - 74))
            
        self.bg_view.active_tab = self.current_tab
        self.bg_view.setNeedsDisplay_(True)
        self._update_status_bar_icon()
        self._update_placeholder()


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = AppDelegate.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()


if __name__ == "__main__":
    main()
