# Script to add Git bin directory to system PATH
# Run this script as Administrator

$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
$gitBinPath = "C:\Program Files\Git\bin"

if ($currentPath -notlike "*$gitBinPath*") {
    $newPath = $currentPath + ";" + $gitBinPath
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "Machine")
    Write-Host "Successfully added $gitBinPath to system PATH" -ForegroundColor Green
    Write-Host "Please restart your terminal for changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "$gitBinPath is already in system PATH" -ForegroundColor Green
}

# Verify
Write-Host "`nCurrent system PATH entries for Git:" -ForegroundColor Cyan
[System.Environment]::GetEnvironmentVariable("Path", "Machine") -split ';' | Where-Object { $_ -like "*Git*" } | ForEach-Object { Write-Host "  $_" }

