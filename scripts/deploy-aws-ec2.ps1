[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PublicIp,

    [Parameter(Mandatory = $true)]
    [string]$KeyPath,

    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$SshUser = "ubuntu",
    [string]$Branch = "main",
    [string]$RemoteRepoDir = "/opt/earthwork_dashboard",
    [string]$RemoteDataDir = "/opt/earthwork-data"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $KeyPath)) {
    throw "KeyPath not found: $KeyPath"
}

$ssh = Get-Command ssh -ErrorAction Stop

$remote = "$SshUser@$PublicIp"
$sshArgs = @(
    "-i", $KeyPath,
    "-o", "StrictHostKeyChecking=accept-new",
    $remote
)

# Remote bash script (single shot). Uses sudo docker to avoid needing docker group re-login.
$remoteScript = @'
set -euo pipefail

echo "==> OS info"
uname -a || true

echo "==> Install packages (docker, git, curl)"
sudo apt update
sudo apt install -y docker.io git curl

echo "==> Prepare folders"
sudo mkdir -p "{REMOTE_DATA_DIR}"
sudo mkdir -p "{REMOTE_REPO_DIR}"
sudo chown -R "$USER:$USER" "{REMOTE_REPO_DIR}"

echo "==> Clone or update repo"
if [ ! -d "{REMOTE_REPO_DIR}/.git" ]; then
  rm -rf "{REMOTE_REPO_DIR}"/*
  git clone --branch "{BRANCH}" --single-branch "{REPO_URL}" "{REMOTE_REPO_DIR}"
else
  cd "{REMOTE_REPO_DIR}"
  git fetch --all --prune
  git reset --hard "origin/{BRANCH}"
fi

echo "==> Build image"
cd "{REMOTE_REPO_DIR}/earthwork_dashboard"
sudo docker build -t earthwork-dashboard .

echo "==> Run container"
sudo docker rm -f earthwork 2>/dev/null || true
sudo docker run -d --name earthwork --restart unless-stopped \
  -p 8080:8080 \
  -v "{REMOTE_DATA_DIR}:/app/data" \
  earthwork-dashboard

echo "==> Health check (from EC2)"
sudo docker ps --filter name=earthwork
curl -I --max-time 10 http://127.0.0.1:8080/ | head -n 1 || true

echo "==> DONE"
echo "Open: http://{PUBLIC_IP}:8080/"
echo "Fuel: http://{PUBLIC_IP}:8080/fuel"
'@

$remoteScript = $remoteScript.Replace("{PUBLIC_IP}", $PublicIp)
$remoteScript = $remoteScript.Replace("{REPO_URL}", $RepoUrl)
$remoteScript = $remoteScript.Replace("{BRANCH}", $Branch)
$remoteScript = $remoteScript.Replace("{REMOTE_REPO_DIR}", $RemoteRepoDir)
$remoteScript = $remoteScript.Replace("{REMOTE_DATA_DIR}", $RemoteDataDir)

Write-Host "Connecting to $remote ..."
Write-Host "Remote repo dir: $RemoteRepoDir"
Write-Host "Remote data dir: $RemoteDataDir"

# Use a here-string passed to bash -lc
$command = "bash -lc " + [System.Management.Automation.Language.CodeGeneration]::QuoteArgument($remoteScript)

& $ssh.Source @sshArgs $command
