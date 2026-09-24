# sync-pull.ps1
# Pull Home Assistant config from Raspberry Pi to local repository
# Usage: .\sync-pull.ps1 [-DryRun]

param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Configuration
$PI_HOST = "david@192.168.1.110"
$PI_CONFIG_PATH = "/opt/homeassistant/config"
$LOCAL_CONFIG_PATH = ".\homeassistant-config"

# Files/directories to exclude from sync
$EXCLUDES = @(
    "*.db",
    "*.db-shm",
    "*.db-wal",
    ".storage/",
    ".cloud/",
    "deps/",
    "tts/",
    "*.log",
    "*.log.*",
    ".HA_VERSION",
    ".ha_run.lock",
    "__pycache__/",
    # HACS frontend builds (large, can be regenerated)
    "custom_components/hacs/hacs_frontend/frontend_es5/",
    "custom_components/hacs/hacs_frontend/frontend_latest/",
    "custom_components/hacs/hacs_frontend/static/"
)

Write-Host "=== Home Assistant Config Sync (PULL) ===" -ForegroundColor Cyan
Write-Host "Source: $PI_HOST`:$PI_CONFIG_PATH"
Write-Host "Destination: $LOCAL_CONFIG_PATH"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] No files will be modified" -ForegroundColor Yellow
    Write-Host ""
}

# Build exclude arguments for scp/rsync
# Since Windows doesn't have rsync by default, we use scp with manual exclusion
# For better sync, consider installing rsync via WSL or Git Bash

# Check if rsync is available (Git Bash, WSL, etc.)
$rsyncAvailable = $null -ne (Get-Command rsync -ErrorAction SilentlyContinue)

if ($rsyncAvailable) {
    Write-Host "Using rsync for sync..." -ForegroundColor Green
    
    $excludeArgs = ($EXCLUDES | ForEach-Object { "--exclude='$_'" }) -join " "
    $dryRunArg = if ($DryRun) { "--dry-run" } else { "" }
    
    $cmd = "rsync -avz --delete $dryRunArg $excludeArgs `"$PI_HOST`:$PI_CONFIG_PATH/`" `"$LOCAL_CONFIG_PATH/`""
    Write-Host "Running: $cmd" -ForegroundColor DarkGray
    Invoke-Expression $cmd
} else {
    Write-Host "rsync not found. Using scp (less efficient, no delete sync)..." -ForegroundColor Yellow
    Write-Host "Tip: Install Git Bash or WSL for rsync support" -ForegroundColor DarkGray
    Write-Host ""
    
    if ($DryRun) {
        Write-Host "[DRY RUN] Would copy the following:" -ForegroundColor Yellow
        ssh $PI_HOST "ls -la $PI_CONFIG_PATH/"
    } else {
        # Pull main config files
        $configFiles = @(
            "configuration.yaml",
            "automations.yaml",
            "scenes.yaml",
            "scripts.yaml",
            "secrets.yaml"
        )
        
        foreach ($file in $configFiles) {
            Write-Host "Pulling $file..." -ForegroundColor Gray
            scp "${PI_HOST}:${PI_CONFIG_PATH}/${file}" "$LOCAL_CONFIG_PATH/" 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Warning: $file not found or failed to copy" -ForegroundColor Yellow
            }
        }
        
        # Pull directories
        $configDirs = @(
            "blueprints",
            "custom_components"
        )
        
        foreach ($dir in $configDirs) {
            Write-Host "Pulling $dir/..." -ForegroundColor Gray
            scp -r "${PI_HOST}:${PI_CONFIG_PATH}/${dir}" "$LOCAL_CONFIG_PATH/" 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Warning: $dir not found or failed to copy" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
Write-Host "=== Sync complete ===" -ForegroundColor Green

