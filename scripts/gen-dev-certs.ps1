# Generate self-signed TLS certificates for local HTTPS testing.
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$CertDir = Join-Path $Root "docker\certs"
New-Item -ItemType Directory -Force -Path $CertDir | Out-Null

$Subject = "/CN=localhost/O=Knowledge Chatbot Dev/C=US"
& openssl req -x509 -nodes -days 365 -newkey rsa:2048 `
  -keyout (Join-Path $CertDir "privkey.pem") `
  -out (Join-Path $CertDir "fullchain.pem") `
  -subj $Subject

Write-Host "Wrote $CertDir\fullchain.pem and $CertDir\privkey.pem"
