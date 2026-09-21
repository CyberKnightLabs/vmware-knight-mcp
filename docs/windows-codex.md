# VMware Knight + Codex on Windows

Use this instead of wizard option **7 → Codex** on Windows. macOS and Linux users should keep using the wizard.

## Install (2 steps)

1. Install VMware Knight and add your targets, as usual:

   ```powershell
   uv tool install vmware-knight
   vmware-knight init
   ```

2. Register it with Codex. Either double-click `scripts\windows\install-codex.cmd`, or run:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\windows\install-codex.ps1
   ```

Then fully quit Codex (or the ChatGPT app), reopen it, and start a **new** chat:

```text
Use the vmware-knight MCP tool cluster_health_summary on lab-vcenter
```

You should see `Called vmware-knight.cluster_health_summary(...)`. **Full Access is not needed.** MCP tools run outside the Codex shell sandbox.

## What the script does

It writes this to `%USERPROFILE%\.codex\config.toml`, after backing up the file:

```toml
[mcp_servers.vmware-knight]
command = 'C:\Users\you\.local\bin\vmware-knight.exe'
args = ["mcp"]
enabled = true
startup_timeout_sec = 120
tool_timeout_sec = 300

[mcp_servers.vmware-knight.env]
USERPROFILE = 'C:\Users\you'
SYSTEMROOT = 'C:\WINDOWS'
PYTHONUTF8 = '1'
# ...plus APPDATA, LOCALAPPDATA, TEMP, TMP, HOMEDRIVE, HOMEPATH
```

Why the generic installer fails on Windows:

| Problem | Effect | Fix in the script |
|---|---|---|
| Path written as `"C:\Users\..."` | TOML reads `\U` as an escape, so `config.toml` does not parse and Codex drops the server | Single-quoted literal string `'C:\...'` |
| Default path has no `.exe` | Codex cannot start the server | Finds the real `vmware-knight.exe` |
| Codex passes a minimal environment | Python cannot find `%USERPROFILE%\.vmware-knight` (config and `.env`) | Sets `USERPROFILE`, `SYSTEMROOT` and similar variables explicitly |
| Console code page | Unicode output can crash | `PYTHONUTF8=1` |

When the MCP server does not load, Codex tries to run `vmware-knight` through its shell instead. On Windows, the sandbox blocks that network access. That's why it only seemed to work with Full Access.

## Options

```powershell
.\install-codex.ps1 -ExePath "D:\tools\vmware-knight.exe"   # custom location
.\install-codex.ps1 -Uninstall                               # remove the entry
```

Backups are saved as `config.toml.bak-<timestamp>` next to the config.

## Troubleshooting

```powershell
codex mcp list
codex mcp get vmware-knight
vmware-knight doctor
```

- **"Could not find vmware-knight.exe"**: run `where.exe vmware-knight` and pass that path with `-ExePath`.
- **Server listed but no tools**: run `vmware-knight mcp` by hand. It should wait silently (press Ctrl+C to exit). Any error it prints is the real cause.
- **The `.env` permission line in `doctor` shows "unknown"**: this is expected on NTFS and is not a failure.
