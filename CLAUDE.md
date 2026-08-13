# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

MPV media player configuration repository for Windows. Contains Lua scripts, configuration files, OSC themes, and GLSL shaders. No build system required — this is a configuration repository.

## Directory Structure

```
mpv/
├── portable_config/       # Main configuration directory
│   ├── scripts/           # Lua scripts
│   ├── script-opts/       # Script config files (.conf)
│   ├── script-modules/    # Shared Lua modules
│   ├── osc-style/         # On-screen controller themes
│   ├── shaders/           # GLSL video shaders
│   │   ├── Anime4K/       # Anime upscaling shaders
│   │   ├── igv/           # Film grain and enhancement shaders
│   │   └── other/         # Additional shaders
│   ├── files/             # Runtime data (recent.json, danmaku-history.json)
│   ├── mpv.conf           # Main MPV configuration
│   ├── input.conf         # Key bindings and uosc context menu
│   └── MAINTAINER-ONLY-WARNING-upstream-sources.json # Maintainer-only upstream audit sources
├── lua/                   # Lua runtime libraries (socket, ltn12, mime)
├── portable.vs            # VapourSynth script
└── vs-scripts/            # VapourSynth Python scripts
```

## Validation & Testing

```bash
# Test MPV starts without errors
mpv.exe --no-config --script=portable_config/scripts/your-script.lua video-file.mkv

# Check Lua syntax (requires Lua installed)
luac -p portable_config/scripts/your-script.lua

# Debug with log file
mpv.exe --log-file=output.txt video.mkv
```

## Lua Script Conventions

### File Organization
- **Scripts**: `portable_config/scripts/*.lua`
- **Configs**: `portable_config/script-opts/*.conf` (must match script name: `scriptname.lua` → `scriptname.conf`)
- **Modules**: `portable_config/script-modules/`
- **OSC themes**: `portable_config/osc-style/*.lua`

### Standard Pattern
```lua
local msg = require 'mp.msg'
local options = require 'mp.options'

local o = { option1 = 'default' }
options.read_options(o)

mp.add_key_binding('KEY', 'binding-name', callback)
mp.register_script_message('message-name', handler)
```

### Key Requirements
- Use `local` for ALL variables (never global unless module export)
- Use `msg.error/info/warn` — NEVER `print()`
- Use `pcall` for optional dependencies with graceful fallbacks
- UTF-8 encoding with Unix line endings (LF)
- Use `~~/` for mpv config directory paths

### Module Structure (script-modules/)
```lua
local M = {}
function M.public_function() end
return M
```

### Configuration Files (.conf)
```conf
# Comments start with #
option_name=value
```

### Common MPV API Patterns

```lua
-- Property observer with callback
mp.observe_property('time-pos', 'number', function(name, value)
    msg.info('Position: ' .. tostring(value))
end)

-- uosc integration (flash timeline on seek)
mp.commandv('script-message-to', 'uosc', 'flash-timeline')

-- Path expansion for config paths
local config_path = mp.command_native({'expand-path', '~~/script-opts'})
```

## Key Components

### uosc
Main on-screen controller UI. Config via `portable_config/script-opts/uosc.conf`.

**Integration pattern:** Scripts can send messages to uosc for visual feedback:

```lua
mp.commandv('script-message-to', 'uosc', 'flash-elements', 'timeline,speed')
```

**Context menu:** Defined in `input.conf` using `#!` comment syntax:

```conf
alt+s  script-binding uosc/load-subtitles  #! Subtitles > Load
```

### Maintainer-only upstream audit (`MAINTAINER-ONLY-WARNING-upstream-sources.json`)

Scripts are fetched from GitHub using whitelist/blacklist patterns:

```json
{
  "git": "https://github.com/user/repo",
  "whitelist": "%.lua$",
  "blacklist": "LICENSE|README",
  "dest": "~~/scripts"
}
```

Key scripts managed:

- **evafast**: Hybrid seek/fast-forward (rewrite branch)
- **playlistmanager**, **sub-select**, **quality-menu**
- **file-browser**, **autosubsync**, **trakt-scrobble**
- **simple-mpv-webui**, **chapterskip**
- **shaders**: Anime4K, igv collections

### VapourSynth Integration

Bundled Python 3.8 environment with:

- numpy, onnxruntime
- SVPFlow plugins for motion interpolation
- ONNX models in `vs-plugins/models/`

Main script: `portable.vs`

### Shaders

- **Anime4K**: Anime/manga upscaling
- **igv**: Film grain synthesis, debanding, detail enhancement
- **Other**: Joint bilateral filter, pixel clipper

## Common Pitfalls

- Global variables cause conflicts between scripts
- Silent errors — always use `msg.error`
- Hardcoded paths — use `~~/` or `mp.command_native({"expand-path", ...})`
- Script config mismatch — `scriptname.lua` requires `scriptname.conf`
- Missing `pcall` for optional modules breaks scripts when dependencies absent

## Resources

- [MPV Manual](https://mpv.io/manual/master/)
- [MPV Lua Scripting](https://mpv.io/manual/master/#lua-scripting)
- [MPV API Reference](https://mpv.io/manual/master/#list-of-input-properties)
- [uosc Documentation](https://github.com/tomasklaen/uosc)
