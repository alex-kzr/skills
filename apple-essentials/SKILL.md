---
name: apple-essentials
description: "Apple platform integrations on macOS: Notes (memo CLI), Reminders (remindctl), iMessage (imsg CLI), Find My (AppleScript), and macOS desktop automation (computer_use tool)."
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [Apple, macOS, Notes, Reminders, iMessage, FindMy, AirTag, desktop, automation, messaging]
    absorbed_from: [apple-notes, apple-reminders, findmy, imessage, macos-computer-use]
---

# Apple Essentials — macOS Platform Integrations

Manage Apple services and automate the macOS desktop. All operations require macOS.

---

## Section 1: Apple Notes

Use `memo` to manage Apple Notes from the terminal. Notes sync across all Apple devices via iCloud.

### Prerequisites
```bash
brew install marcoamosano/memo/memo
```

### Common Operations
```bash
# Create a note
memo create "Project Ideas" --body "First idea..."

# Search notes
memo search "keyword"

# List recent notes
memo list --limit 10

# Edit a note
memo edit <note-id> --body "Updated content"
```

---

## Section 2: Apple Reminders

Use `remindctl` to manage Apple Reminders from the terminal. Tasks sync via iCloud.

### Prerequisites
```bash
brew install kevban/remindctl/remindctl
```

### Common Operations
```bash
# Add a reminder
remindctl add "Buy groceries" --list "Shopping"

# List reminders
remindctl list --list "Shopping"

# Complete a reminder
remindctl complete <reminder-id>
```

---

## Section 3: iMessage / SMS

Use `imsg` to read and send iMessage/SMS via macOS Messages.app.

### Prerequisites
```bash
brew install followloft/imsg/imsg
```

### Common Operations
```bash
# Read recent messages
imsg read --limit 20

# Send a message
imsg send "+1234567890" --text "Hello"

# Search messages
imsg search "keyword"
```

---

## Section 4: Find My (Device Tracking)

Track Apple devices and AirTags via FindMy.app. Apple doesn't provide a CLI, so this uses AppleScript to open the app and screen capture to read locations.

### Usage
```applescript
tell application "FindMy" to activate
delay 2
tell application "System Events" to tell process "FindMy"
    -- Navigate UI elements to read device locations
end tell
```

### Limitations
- Requires Full Disk Access for the terminal/agent
- Screen capture needed to parse device locations
- No programmatic API — UI automation only

---

## Section 5: macOS Desktop Automation

Drive the macOS desktop in the background — screenshots, mouse, keyboard, scroll, drag — without stealing the user's cursor, keyboard focus, or Space. Works with any tool-capable model when the `computer_use` tool is available.

### Key Principles
- Actions do NOT move the user's cursor or steal keyboard focus
- Works in a virtual display layer
- Screenshot → analyze → act loop

### Supported Actions
- **Screenshot**: Capture the current screen state
- **Mouse**: Click, double-click, right-click, drag
- **Keyboard**: Type text, press keys, hotkeys
- **Scroll**: Scroll in any direction

### Usage Pattern
1. Take a screenshot to see the current state
2. Identify the target UI element by coordinates
3. Perform the action (click, type, etc.)
4. Take another screenshot to verify the result
