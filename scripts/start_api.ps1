Param(
    [string]$ApiHost = "127.0.0.1",
    [int]$Port = 8011
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $repoRoot

$venvPath = Join-Path $repoRoot ".venv"
$uvicornPath = Join-Path $venvPath "Scripts\\uvicorn.exe"
$activateScript = Join-Path $venvPath "Scripts\\Activate.ps1"

if (-not (Test-Path $uvicornPath)) {
    Write-Error "uvicorn not found in $uvicornPath. Activate/install the virtualenv first."
    exit 1
}

function Stop-PortProcess {
    param([int]$TargetPort)
    $connections = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $connections) {
        try {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction Stop
            Write-Warning "Stopping process $($proc.ProcessName) (Id=$($proc.Id)) using port $TargetPort."
            Stop-Process -Id $proc.Id -Force
        } catch {
            Write-Warning ("Could not stop process listening on {0}: {1}" -f $TargetPort, $_)
        }
    }
}

Stop-PortProcess -TargetPort $Port

$serverCommand = @"
Set-Location "$repoRoot"
. "$activateScript"
uvicorn main:app --host $ApiHost --port $Port
"@

Write-Host "Starting uvicorn on http://$ApiHost`:$Port ..."
Start-Process powershell.exe -ArgumentList "-NoExit","-Command",$serverCommand
