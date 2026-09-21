<#
.SYNOPSIS
    Registers VMware Knight as an MCP server for OpenAI Codex on Windows.

.DESCRIPTION
    Windows-only helper. It does not change the Python package or the wizard,
    so macOS/Linux installs are unaffected.

    Compared with `vmware-knight mcp-config install --agent codex`, it handles
    the things that break on Windows:
      * finds vmware-knight.exe (Windows needs the .exe suffix)
      * writes the path as a TOML literal string ('C:\...'), because in a
        "..." string the backslashes become escapes and config.toml stops parsing
      * passes the Windows variables Python needs (USERPROFILE, SYSTEMROOT, ...)
        so the server finds %USERPROFILE%\.vmware-knight\config.yaml and .env
      * backs up config.toml and writes it as UTF-8 without a BOM

    Works in Windows PowerShell 5.1 and PowerShell 7+.

.PARAMETER ExePath
    Full path to vmware-knight.exe. If omitted, the script finds it for you.

.PARAMETER Uninstall
    Removes the vmware-knight entry from Codex's config.toml.

.EXAMPLE
    .\install-codex.ps1
.EXAMPLE
    .\install-codex.ps1 -ExePath "C:\Users\me\.local\bin\vmware-knight.exe"
.EXAMPLE
    .\install-codex.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$ExePath,
    [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'
$ServerName = 'vmware-knight'

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  [X]  $msg" -ForegroundColor Red }

# --- Codex config location ---------------------------------------------------
# Codex reads %CODEX_HOME%\config.toml, defaulting to %USERPROFILE%\.codex.
$CodexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$ConfigPath = Join-Path $CodexHome 'config.toml'

function Read-TextFile($path) {
    if (Test-Path -LiteralPath $path) { return [IO.File]::ReadAllText($path) }
    return ''
}

function Write-TextFileNoBom($path, $text) {
    $enc = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($path, $text, $enc)
}

# Drop [mcp_servers.vmware-knight] and any sub-tables such as
# [mcp_servers.vmware-knight.env], and keep every other line as it is.
function Remove-ServerBlock([string]$text) {
    $lines = $text -split "`r?`n"
    $out = New-Object System.Collections.Generic.List[string]
    $skipping = $false
    $pattern = '^\s*\[\s*mcp_servers\.("?)' + [regex]::Escape($ServerName) + '\1(\.[^\]]*)?\s*\]\s*$'
    foreach ($line in $lines) {
        if ($line -match $pattern) { $skipping = $true; continue }
        if ($skipping -and $line -match '^\s*\[') { $skipping = $false }
        if (-not $skipping) { $out.Add($line) }
    }
    return (($out -join "`r`n").TrimEnd())
}

function Backup-Config {
    if (Test-Path -LiteralPath $ConfigPath) {
        $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
        $bak = "$ConfigPath.bak-$stamp"
        Copy-Item -LiteralPath $ConfigPath -Destination $bak
        Write-Ok "Backup saved: $bak"
    }
}

# --- Uninstall ---------------------------------------------------------------
if ($Uninstall) {
    Write-Step "Removing $ServerName from $ConfigPath"
    if (-not (Test-Path -LiteralPath $ConfigPath)) { Write-Ok 'No Codex config found; nothing to do.'; exit 0 }
    Backup-Config
    $new = Remove-ServerBlock (Read-TextFile $ConfigPath)
    Write-TextFileNoBom $ConfigPath ($new + "`r`n")
    Write-Ok 'Removed. Restart Codex to apply the change.'
    exit 0
}

# --- 1. Locate vmware-knight.exe ---------------------------------------------
Write-Step 'Locating vmware-knight.exe'

if (-not $ExePath) {
    $candidates = @()
    $cmd = Get-Command 'vmware-knight' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { $candidates += $cmd.Source }
    $candidates += @(
        (Join-Path $env:USERPROFILE '.local\bin\vmware-knight.exe'),                        # uv tool install
        (Join-Path $env:APPDATA 'uv\tools\vmware-knight\Scripts\vmware-knight.exe'),        # uv tool venv
        (Join-Path $env:APPDATA 'Python\Scripts\vmware-knight.exe'),                        # pip --user
        (Join-Path $env:USERPROFILE 'pipx\venvs\vmware-knight\Scripts\vmware-knight.exe'),  # pipx venv
        (Join-Path $env:USERPROFILE '.local\pipx\venvs\vmware-knight\Scripts\vmware-knight.exe')
    )
    $ExePath = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
}

if (-not $ExePath -or -not (Test-Path -LiteralPath $ExePath)) {
    Write-Fail 'Could not find vmware-knight.exe.'
    Write-Host '       Install it first, for example:  uv tool install vmware-knight'
    Write-Host '       or pass the path:  .\install-codex.ps1 -ExePath "C:\path\to\vmware-knight.exe"'
    exit 1
}

# If the path has no extension, prefer the .exe next to it.
if ([IO.Path]::GetExtension($ExePath) -eq '' -and (Test-Path -LiteralPath "$ExePath.exe")) {
    $ExePath = "$ExePath.exe"
}
$ExePath = (Resolve-Path -LiteralPath $ExePath).Path
Write-Ok $ExePath

if ($ExePath.Contains("'")) {
    Write-Fail "The path contains a single quote ('), which TOML literal strings cannot hold. Install to a different folder."
    exit 1
}

# --- 2. Smoke-test the executable ---------------------------------------------
Write-Step 'Checking that the executable runs'
try {
    & $ExePath --help *> $null
    if ($LASTEXITCODE -ne 0) { throw "exit code $LASTEXITCODE" }
    Write-Ok 'vmware-knight --help runs'
} catch {
    Write-Fail "vmware-knight did not run: $_"
    exit 1
}

$KnightConfig = Join-Path $env:USERPROFILE '.vmware-knight\config.yaml'
if (Test-Path -LiteralPath $KnightConfig) {
    Write-Ok "Found targets config: $KnightConfig"
} else {
    Write-Warn "No $KnightConfig yet. Run  vmware-knight init  (or  vmware-knight wizard ) to add targets."
}

# --- 3. Build the TOML block --------------------------------------------------
# Literal strings ('...') keep backslashes as they are, so Windows paths parse cleanly.
function TomlLit([string]$s) { return "'" + $s + "'" }

$envPairs = [ordered]@{
    USERPROFILE      = $env:USERPROFILE
    HOMEDRIVE        = $env:HOMEDRIVE
    HOMEPATH         = $env:HOMEPATH
    APPDATA          = $env:APPDATA
    LOCALAPPDATA     = $env:LOCALAPPDATA
    SYSTEMROOT       = $env:SystemRoot
    TEMP             = $env:TEMP
    TMP              = $env:TMP
    PYTHONUTF8       = '1'
    PYTHONIOENCODING = 'utf-8'
}
$envItems = foreach ($k in $envPairs.Keys) {
    $v = $envPairs[$k]
    if ($v -and -not $v.Contains("'")) { "$k = $(TomlLit $v)" }
}

$block = @(
    "[mcp_servers.$ServerName]"
    "command = $(TomlLit $ExePath)"
    'args = ["mcp"]'
    'enabled = true'
    'startup_timeout_sec = 120'
    'tool_timeout_sec = 300'
    ''
    "[mcp_servers.$ServerName.env]"
    $envItems
) -join "`r`n"

# --- 4. Write config.toml -----------------------------------------------------
Write-Step "Writing $ConfigPath"
if (-not (Test-Path -LiteralPath $CodexHome)) { New-Item -ItemType Directory -Path $CodexHome | Out-Null }
Backup-Config

$existing = Remove-ServerBlock (Read-TextFile $ConfigPath)
if ($existing.Length -gt 0) { $content = $existing + "`r`n`r`n" + $block + "`r`n" }
else                        { $content = $block + "`r`n" }
Write-TextFileNoBom $ConfigPath $content
Write-Ok 'Codex MCP entry written'

# --- 5. Verify with the Codex CLI if available --------------------------------
Write-Step 'Verifying with Codex'
$codex = Get-Command 'codex' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($codex) {
    & $codex.Source mcp get $ServerName
    if ($LASTEXITCODE -eq 0) { Write-Ok 'Codex can read the vmware-knight entry' }
    else { Write-Warn 'codex mcp get reported a problem. Check the output above.' }
} else {
    Write-Warn 'Codex CLI not on PATH, so this step was skipped. The Codex app will pick up the change on restart.'
}

Write-Host ''
Write-Host 'Done. Next steps:' -ForegroundColor Green
Write-Host '  1. Fully quit Codex (or the ChatGPT desktop app) and open it again.'
Write-Host '  2. Start a NEW chat. You do not need Full Access for MCP tools.'
Write-Host '  3. Ask:  Use the vmware-knight MCP tool cluster_health_summary on <your-target-tag>'
Write-Host "  To undo:  .\install-codex.ps1 -Uninstall   (backups are next to $ConfigPath)"
