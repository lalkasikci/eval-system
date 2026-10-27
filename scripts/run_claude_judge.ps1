param(
    [string]$RunJson = "",
    [string]$Out = "outputs/claude_judge",
    [ValidateRange(1, 30)]
    [int]$Limit = 1,
    [switch]$Resume,
    [ValidateRange(1, 5)]
    [int]$RepeatCount = 1,
    [ValidateRange(1, 99)]
    [int]$RepeatStart = 1
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
    for ($offset = 0; $offset -lt $RepeatCount; $offset++) {
        $repeatNumber = $RepeatStart + $offset
        $repeatOut = if ($RepeatCount -gt 1 -or $RepeatStart -ne 1) {
            Join-Path $Out "repeat_$repeatNumber"
        } else {
            $Out
        }
        Write-Host "Claude yargıç tekrarı $repeatNumber/$($RepeatStart + $RepeatCount - 1) -> $repeatOut"
        $arguments = @(
            "-m", "madset_eval", "regrade", $RunJson,
            "--judge-adapter", "examples.claude_judge:judge",
            "--unique-scenarios", "--limit", "$Limit", "--progress", "--out", $repeatOut
        )
        if ($Resume) { $arguments += "--resume" }
        & $python @arguments
        if ($LASTEXITCODE -ne 0) { throw "Claude judge tekrarı $repeatNumber başarısız oldu." }
    }
}
finally {
    Remove-Item Env:ANTHROPIC_API_KEY -ErrorAction SilentlyContinue
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
}
