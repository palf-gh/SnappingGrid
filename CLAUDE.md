# SnappingGrid — プロジェクト規約

## 概要

Glyphs 3 用のスナップ可能なグリッドプラグイン。
Bundle ID: `com.palf.SnappingGrid`

## ブランチ戦略

- **`main`**: リリース済みの安定版
- **`develop`**: 開発の統合ブランチ（デフォルトブランチ）
- **`feature/*`**: 機能ごとの開発ブランチ

```
feature/<機能名>  →  PR  →  develop  →  PR  →  main
```

- PR は `--no-ff` でマージしてブランチ履歴を保持する
- `feature/*` ブランチは作業完了後に削除する

## コミット粒度

- 1コミット = 1つの論理的な変更
- コミットメッセージは日本語または英語どちらでも可
- 例: `feat: グリッド描画の初期実装`, `fix: スナップ計算の精度修正`

## プラグイン構造

```
SnappingGrid.glyphsPlugin/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/plugin        # バイナリスタブ（変更不要）
│   └── Resources/
│       ├── plugin.py       # メインロジック
│       ├── en.lproj/Localizable.strings
│       ├── ja.lproj/Localizable.strings
│       ├── zh-Hans.lproj/Localizable.strings
│       └── ko.lproj/Localizable.strings
```

## ローカライズ

- 対応言語: 英語(en)・日本語(ja)・中国語簡体字(zh-Hans)・韓国語(ko)
- `Glyphs.localize({})` を使う（コード内インライン辞書）
- メニュー項目など UI 文字列はすべて4言語を用意する

## 設定永続化

- `Glyphs.defaults['com.palf.SnappingGrid.<key>']` を使う

## テスト方法

```bash
# プラグインをシンボリックリンクで配置
ln -sf "$(pwd)/SnappingGrid.glyphsPlugin" \
  "$HOME/Library/Application Support/Glyphs 3/Plugins/SnappingGrid.glyphsPlugin"
```

Glyphs 3 を再起動して動作確認する。
