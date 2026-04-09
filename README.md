# local-toastd

`PySide6` でトレイ常駐しつつ、`Flask` で受けたローカル HTTP 通知を処理するための小さなデーモンです。

現時点では次まで実装済みです。

- トレイ常駐アプリの骨組み
- トレイから開ける設定画面
- `POST /notify` による通知受付
- payload 検証
- 通知マネージャによる表示待ち/表示中管理
- 右上に積み上がるカスタム通知 UI
- フェードイン/アウトと通知音
- テーマ、サウンドタイプ、ポート、持続時間、スタック数の保存
- `level` ごとの見た目差分

設定は `settings.toml` に保存されます。
開発実行時はプロジェクト直下、Nuitka などで配布時は実行ファイルの隣を使います。

## Setup

```powershell
uv venv
uv sync
```

## Run

```powershell
uv run local-toastd
```

起動するとメインウィンドウは出さず、システムトレイに常駐します。
設定はトレイメニューの `Settings...` から開けます。
ポート番号の変更は保存後、再起動時に反映されます。

## Send A Notification

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8765/notify `
  -ContentType 'application/json' `
  -Body '{"message":"hello from powershell","title":"local-toastd"}'
```

成功時は `202 Accepted` を返し、通知データは内部キューに積まれます。

## Run Tests

```powershell
uv run pytest
```

## Lint And Type Check

```powershell
uv run ruff check .
uv run mypy
```
