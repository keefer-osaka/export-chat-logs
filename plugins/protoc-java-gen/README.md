# protoc-java-gen

[繁體中文](README.zh-TW.md) | [日本語](README.ja.md)

A Claude Code plugin to generate Java from `.proto` files using a specific protoc version, and automatically copy the output to matching subprojects.

## Features

- Run `protoc` at a pinned version (no system PATH dependency)
- Auto-detect all subprojects containing `src/main/java/proto/<ClassName>.java`
- Skip unchanged files (diff before overwrite)
- Output summary: how many files updated across how many subprojects

## Installation

```
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install protoc-java-gen@devtools-plugins
```

## Setup

```
/protoc-java-gen:setup
```

Configure:
| Setting | Description |
|---------|-------------|
| `PROTOC_PATH` | Full path to the `protoc` binary |
| `PROJECT_ROOT` | Absolute path to your project root |
| `PROTO_DIR` | Proto subdirectory relative to project root (default: `proto`) |
| `PLUGIN_LANG` | Output language: `en`, `zh-TW`, or `ja` (default: `en`) |

Config is saved to `~/.config/devtools-plugins/protoc-java-gen/.env`.

## Usage

The `.proto` extension is optional:

```
/protoc-java-gen:generate service
/protoc-java-gen:generate service.proto
```

List available proto files:

```
/protoc-java-gen:generate
```

## How It Works

1. Reads config from `~/.config/devtools-plugins/protoc-java-gen/.env`
2. Reads `java_outer_classname` from the specified `.proto` file
3. Runs `protoc --java_out` to generate the Java file in a temp directory
4. Searches `PROJECT_ROOT` for all `*/src/main/java/proto/<ClassName>.java`
5. Diffs each target — skips unchanged, overwrites changed
6. Prints a summary

## Requirements

- macOS / Linux
- `protoc` binary (any version, path configured via setup)
- Project layout: generated Java under `src/main/java/proto/`

## File Structure

```
.claude-plugin/
└── plugin.json             # Plugin metadata
skills/
├── generate/SKILL.md       # /protoc-java-gen:generate
└── setup/
    ├── SKILL.md            # /protoc-java-gen:setup
    └── questions/          # Setup wizard question definitions
        ├── en.json
        ├── zh-TW.json
        └── ja.json
scripts/
├── generate.sh             # Main protoc invocation and copy logic
├── save-config.sh          # Write protoc path + project root + proto dir + language
└── i18n/                   # Locale strings
    ├── load.sh                 # i18n loader (sources correct locale file)
    ├── en.sh                   # English
    ├── zh_TW.sh                # Traditional Chinese
    └── ja.sh                   # Japanese
```
