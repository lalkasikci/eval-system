param(
    [string]$RunJson = "",
    [string]$Out = "outputs/claude_judge"
)

$ErrorActionPreference = "Stop"
$bundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$python = if (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { "python" }
if ([string]::IsNullOrWhiteSpace($RunJson)) {
    $latest = Get-ChildItem -LiteralPath "outputs/demo/runs" -Filter "v3_dev_*.json" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) { throw "Önce python -m madset_eval demo --out outputs/demo komutunu çalıştırın." }
    $RunJson = $latest.FullName
}

$secret = Read-Host "Claude API anahtarı (ekranda görünmez)" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    & $python -m madset_eval regrade $RunJson `
        --judge-adapter examples.claude_judge:judge `
        --out $Out
    if ($LASTEXITCODE -ne 0) { throw "Claude judge çalışması başarısız oldu." }
}
finally {
    Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
}
