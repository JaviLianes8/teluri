# Build and upload to PyPI. Run scripts/check.ps1 first.
# The version must not already exist on PyPI; the token is read from a secret store, never git.
$ErrorActionPreference = "Stop"

if (git status --porcelain) { throw "Commit or stash changes before building a release." }
if ($LASTEXITCODE -ne 0) { throw "Could not inspect the working tree." }
$versionLine = Select-String -LiteralPath pyproject.toml -Pattern '^version = "([^"]+)"$'
if (-not $versionLine) { throw "No project version found." }
$version = $versionLine.Matches[0].Groups[1].Value

# Works on both Windows PowerShell 5.1 and pwsh 7 (generic catch, no PS7-only types).
$taken = $true
try {
    Invoke-WebRequest -UseBasicParsing "https://pypi.org/pypi/teluri/$version/json" | Out-Null
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 404) { $taken = $false } else { throw }
}
if ($taken) { throw "teluri $version already exists on PyPI." }
if (Test-Path -LiteralPath dist) { throw "Move the existing dist directory before building." }
& "$PSScriptRoot/check.ps1"
if ($LASTEXITCODE -ne 0) { throw "Quality checks failed." }

$token = $env:PYPI_TOKEN
if (-not $token -and (Test-Path "C:\secrets\pypi-token.txt")) {
    $token = (Get-Content "C:\secrets\pypi-token.txt" -Raw).Trim()
}
if (-not $token) {
    throw "No PyPI token. Set `$env:PYPI_TOKEN or save it to C:\secrets\pypi-token.txt (never commit it)."
}

python -m build
if ($LASTEXITCODE -ne 0) { throw "Build failed." }
python -m twine check dist/*
if ($LASTEXITCODE -ne 0) { throw "Distribution checks failed." }

$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $token
try { python -m twine upload dist/* } finally { Remove-Item Env:\TWINE_PASSWORD -ErrorAction SilentlyContinue }
