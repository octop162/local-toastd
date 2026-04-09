# local-toastd

- 設定は `settings.toml` に保存されます。

## ローカル環境

```powershell
uv venv
uv sync --extra dev
uv run local-toastd
```

## 動作確認

PowerShell:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8765/notify `
  -ContentType 'application/json' `
  -Body '{"message":"hello from powershell","title":"local-toastd"}'
```

curl:

```bash
curl -X POST http://127.0.0.1:8765/notify \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"hello from curl\",\"title\":\"local-toastd\"}"
```

成功時は `202 Accepted` を返し、通知データは内部キューに積まれます。

## テスト

```powershell
uv run pytest
```

## フォーマッタ

```powershell
uv run ruff check .
uv run mypy
```

## ビルド

```powershell
.\scripts\build.ps1
```

```powershell
.\scripts\release.ps1 -Version 0.2.0 -SkipChecks
```
