# local-toastd

- 設定は `settings.toml` に保存されます。
- HTTP の待受ホストは `settings.toml` の `[server].bind_host` で変更できます。

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
  -Body '{"message":"hello from powershell","title":"local-toastd","level":"info"}'
```

curl:

```bash
curl -X POST http://127.0.0.1:8765/notify \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"hello from curl\",\"title\":\"local-toastd\",\"level\":\"info\"}"
```

成功時は `202 Accepted` を返し、通知データは内部キューに積まれます。

`settings.toml` 例:

```toml
[notification]
theme = "dark"
sound_types = { info = "gentle", success = "scratch", warning = "taiko", error = "zangeki" }
position = "top_right"
font_size = 13
duration_seconds = 10.0
max_visible = 10

[server]
bind_host = "127.0.0.1"
port = 8765
```

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

## GitHub Release

GitHub では `v0.2.0` のようなタグを push すると、Actions が Windows 向け release zip を作って GitHub Release を自動生成します。
タグ名の `v` を外した値と `pyproject.toml` の `version` は一致している必要があります。

```powershell
git tag v0.2.0
git push origin v0.2.0
```
