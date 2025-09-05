$archivePath = "all.zip"
$excludedItems = @("venv", "config.txt", ".gitattributes")
$pscpPath = "C:\Program Files\PuTTY\pscp.exe"
$pscpArgs = "all.zip root@172.20.10.5:/root/lte"

if (Test-Path $archivePath) {
    Remove-Item $archivePath -Force
}

$itemsToArchive = Get-ChildItem | Where-Object { $_.Name -notin $excludedItems }
Compress-Archive -Path $itemsToArchive -DestinationPath $archivePath

Start-Process -FilePath $pscpPath -ArgumentList $pscpArgs