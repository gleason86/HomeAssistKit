# sync-push.ps1
# Push local Home Assistant config to Raspberry Pi
# Usage: .\sync-push.ps1 [-DryRun] [-NoBackup] [-Restart]

param(
    [switch]$DryRun,
    [switch]$NoBackup,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

# Configuration
$PI_HOST = "david@192.168.1.110"
$PI_CONFIG_PATH = "/opt/homeassistant/config"
$LOCAL_CONFIG_PATH = ".\homeassistant-config"
$BACKUP_DIR = "/opt/homeassistant/backups"
$HA_CONTAINER = "homeassistant"

# Files/directories to exclude from sync (never push these)
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
    "*.pem",
    "*.key",
    "*.key.bak",
    # HACS frontend builds
    "custom_components/hacs/hacs_frontend/frontend_es5/",
    "custom_components/hacs/hacs_frontend/frontend_latest/",
    "custom_components/hacs/hacs_frontend/static/"
)

Write-Host "=== Home Assistant Config Sync (PUSH) ===" -ForegroundColor Cyan
Write-Host "Source: $LOCAL_CONFIG_PATH"
Write-Host "Destination: $PI_HOST`:$PI_CONFIG_PATH"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] No files will be modified" -ForegroundColor Yellow
    Write-Host ""
}

# Create backup on Pi before pushing
if (-not $NoBackup -and -not $DryRun) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "config_backup_$timestamp.tar.gz"

    Write-Host "Creating backup on Pi: $backupName" -ForegroundColor Yellow
    ssh $PI_HOST "mkdir -p $BACKUP_DIR && cd $PI_CONFIG_PATH && tar -czf $BACKUP_DIR/$backupName --exclude='*.db*' --exclude='.storage' --exclude='deps' --exclude='tts' --exclude='*.log*' ."

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Backup created: $BACKUP_DIR/$backupName" -ForegroundColor Green
    }
    else {
        Write-Host "Warning: Backup may have failed" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Check if rsync is available
$rsyncAvailable = $null -ne (Get-Command rsync -ErrorAction SilentlyContinue)

if ($rsyncAvailable) {
    Write-Host "Using rsync for sync..." -ForegroundColor Green

    $excludeArgs = ($EXCLUDES | ForEach-Object { "--exclude='$_'" }) -join " "
    $dryRunArg = if ($DryRun) { "--dry-run" } else { "" }

    $cmd = "rsync -avz $dryRunArg $excludeArgs `"$LOCAL_CONFIG_PATH/`" `"$PI_HOST`:$PI_CONFIG_PATH/`""
    Write-Host "Running: $cmd" -ForegroundColor DarkGray
    Invoke-Expression $cmd
}
else {
    Write-Host "rsync not found. Using scp (less efficient)..." -ForegroundColor Yellow
    Write-Host "Tip: Install Git Bash or WSL for rsync support" -ForegroundColor DarkGray
    Write-Host ""

    if ($DryRun) {
        Write-Host "[DRY RUN] Would push the following:" -ForegroundColor Yellow
        Get-ChildItem $LOCAL_CONFIG_PATH -Recurse | Select-Object FullName
    }
    else {
        # Push main config files
        $configFiles = @(
            "configuration.yaml",
            "automations.yaml",
            "scenes.yaml",
            "scripts.yaml"
        )

        foreach ($file in $configFiles) {
            $localFile = Join-Path $LOCAL_CONFIG_PATH $file
            if (Test-Path $localFile) {
                Write-Host "Pushing $file..." -ForegroundColor Gray
                scp "$localFile" "${PI_HOST}:${PI_CONFIG_PATH}/"
            }
        }

        # Push secrets.yaml if it exists locally
        $secretsFile = Join-Path $LOCAL_CONFIG_PATH "secrets.yaml"
        if (Test-Path $secretsFile) {
            Write-Host "Pushing secrets.yaml..." -ForegroundColor Gray
            scp "$secretsFile" "${PI_HOST}:${PI_CONFIG_PATH}/"
        }

        # Push blueprints directory
        $blueprintsDir = Join-Path $LOCAL_CONFIG_PATH "blueprints"
        if (Test-Path $blueprintsDir) {
            Write-Host "Pushing blueprints/..." -ForegroundColor Gray
            scp -r "$blueprintsDir" "${PI_HOST}:${PI_CONFIG_PATH}/"
        }

        # Note: custom_components should typically be managed via HACS, not manual sync
        Write-Host ""
        Write-Host "Note: custom_components not pushed (manage via HACS)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Push complete ===" -ForegroundColor Green

# Optionally restart Home Assistant
if ($Restart -and -not $DryRun) {
    Write-Host ""
    Write-Host "Restarting Home Assistant container..." -ForegroundColor Yellow
    ssh $PI_HOST "docker restart $HA_CONTAINER"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "Home Assistant restarted. It may take a minute to come back online." -ForegroundColor Green
    }
    else {
        Write-Host "Warning: Restart may have failed" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "To validate config before restart, run:" -ForegroundColor DarkGray
Write-Host "  ssh $PI_HOST `"docker exec $HA_CONTAINER python -m homeassistant --script check_config -c /config`"" -ForegroundColor DarkGray
