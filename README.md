# SnappingGrid

Glyphs 3 用の、スナップ可能なグリッド表示プラグインです。  
グリッドの表示と、ノード移動時のスナップを提供します。

## Features

- メイングリッドとサブグリッドの表示
- グリッド方式の切り替え（Division / Unit）
- H/V 個別設定と同期設定
- メイン色・サブ色のカスタマイズ
- ノード移動時のスナップ（選択ハンドル連動）
- 英語・日本語・简体中文・한국어 の UI ローカライズ

## Requirements

- macOS
- [Glyphs 3](https://glyphsapp.com/)

## Installation

以下のコマンドでプラグインを Glyphs 3 の Plugins フォルダへシンボリックリンクします。

```bash
ln -sf "$(pwd)/SnappingGrid.glyphsPlugin" \
  "$HOME/Library/Application Support/Glyphs 3/Plugins/SnappingGrid.glyphsPlugin"
```

その後、Glyphs 3 を再起動してください。

## Usage

- `View` メニューから **Show Snapping Grid** を切り替えて表示/非表示
- `Edit` メニューから **Snapping Grid Settings…** を開いて設定変更
- 設定内容:
  - Grid Mode（Division / Unit）
  - Main Grid（H/V, Sync H/V）
  - Sub Grid（subdivision, Sync H/V）
  - Main/Sub Color
  - Enable snap

## Development

- Bundle ID: `com.palf.SnappingGrid`
- Main source: `SnappingGrid.glyphsPlugin/Contents/Resources/plugin.py`

## Licence

このプロジェクトは MIT Licence のもとで公開されています。  
詳細は `LICENSE` を参照してください。
