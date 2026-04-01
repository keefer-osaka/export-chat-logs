# protoc-java-gen

[English](README.md) | [繁體中文](README.zh-TW.md)

指定バージョンの protoc を使って `.proto` ファイルから Java を生成し、対応するすべてのサブプロジェクトに自動コピーする Claude Code プラグイン。

## 機能

- 固定バージョンの `protoc` を使用（システム PATH に依存しない）
- `src/main/java/proto/<ClassName>.java` を含むすべてのサブプロジェクトを自動検出
- 変更のないファイルをスキップ（上書き前に差分を比較）
- サマリー出力：何件のサブプロジェクトで何ファイルを更新したかを表示

## インストール

```
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install protoc-java-gen@devtools-plugins
```

## 設定

```
/protoc-java-gen:setup
```

設定項目：
| フィールド | 説明 |
|-----------|------|
| `PROTOC_PATH` | `protoc` バイナリのフルパス |
| `PROJECT_ROOT` | プロジェクトルートの絶対パス |
| `PROTO_DIR` | プロジェクトルートからの相対パスで proto サブディレクトリ（デフォルト：`proto`）|
| `PLUGIN_LANG` | 出力言語：`en`、`zh-TW`、または `ja`（デフォルト：`en`）|

設定は `~/.config/devtools-plugins/protoc-java-gen/.env` に保存されます。

## 使い方

`.proto` 拡張子は省略可能：

```
/protoc-java-gen:generate service
/protoc-java-gen:generate service.proto
```

利用可能な proto ファイルを一覧表示：

```
/protoc-java-gen:generate
```

## 動作の仕組み

1. `~/.config/devtools-plugins/protoc-java-gen/.env` から設定を読み込む
2. 指定された `.proto` ファイルから `java_outer_classname` を読み取る
3. `protoc --java_out` を実行し、一時ディレクトリに Java ファイルを生成
4. `PROJECT_ROOT` 内のすべての `*/src/main/java/proto/<ClassName>.java` を検索
5. 各ターゲットを差分比較 — 変更なしはスキップ、変更ありは上書き
6. サマリーを表示

## 動作環境

- macOS / Linux
- `protoc` バイナリ（バージョン任意、パスは setup で設定）
- プロジェクト構成：生成された Java ファイルが `src/main/java/proto/` 以下にあること

## ファイル構成

```
.claude-plugin/
└── plugin.json             # プラグインメタデータ
skills/
├── generate/SKILL.md       # /protoc-java-gen:generate
└── setup/
    ├── SKILL.md            # /protoc-java-gen:setup
    └── questions/          # 設定ウィザードの質問定義
        ├── en.json
        ├── zh-TW.json
        └── ja.json
scripts/
├── generate.sh             # メインの protoc 呼び出しとコピーロジック
├── save-config.sh          # protoc パス + プロジェクトルート + proto ディレクトリ + 言語の書き込み
└── i18n/                   # ロケール文字列
    ├── load.sh                 # i18n ローダー（対応するロケールファイルを読み込む）
    ├── en.sh                   # 英語
    ├── zh_TW.sh                # 繁体字中国語
    └── ja.sh                   # 日本語
```
