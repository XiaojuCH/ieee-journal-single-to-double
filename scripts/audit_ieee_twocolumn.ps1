param(
    [Parameter(Mandatory=$true)]
    [string]$TexFile
)

if (-not (Test-Path -LiteralPath $TexFile)) {
    Write-Error "File not found: $TexFile"
    exit 2
}

$text = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath $TexFile))
$issues = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]

function Add-Issue($message) { $script:issues.Add($message) | Out-Null }
function Add-Warning($message) { $script:warnings.Add($message) | Out-Null }

if ($text -notmatch '\\documentclass\[[^\]]*journal[^\]]*twocolumn[^\]]*\]\{IEEEtran\}') {
    Add-Issue "Document class is not IEEEtran journal twocolumn."
}

if ($text -notmatch '\\maketitle') {
    Add-Issue "Missing \maketitle."
}

if ($text -match '\\IEEEauthorblockN|\\IEEEauthorblockA') {
    Add-Issue "Conference-style IEEEauthorblock commands remain in journal mode."
}

if ($text -match '\\begin\{IEEEbiography\}|\\begin\{IEEEbiographynophoto\}|PLACE PHOTO HERE') {
    Add-Issue "Author biography/photo placeholder content remains."
}

if ($text -match '\\hfill\s*\(e-mail|Corresponding author:.*\\hfill') {
    Add-Issue "Potentially unsafe \hfill in author/corresponding-author email text."
}

$singleFigures = [regex]::Matches($text, '(?s)\begin\{figure\}(?:\[[^\]]*\])?.*?\end\{figure\}')
foreach ($figure in $singleFigures) {
    if ($figure.Value -match '\includegraphics\[[^\]]*width\s*=\s*\textwidth') {
        Add-Warning "A single-column figure appears to use width=\textwidth; consider \columnwidth or figure*."
        break
    }
}

if ($text -match 'width\s*=\s*1\.[0-9]+\\textwidth') {
    Add-Warning "Overwide draft graphic/table sizing remains, e.g. width=1.x\textwidth."
}

if ($text -match '\\begin\{figure\}\[H\]|\\begin\{table\}\[H\]') {
    Add-Warning "Pinned [H] floats remain; verify they are intentional in two-column mode."
}

if ($text -match '\\end\{thebibliography\}(?s)\s*(.*?)\\end\{document\}') {
    $tail = $Matches[1].Trim()
    if ($tail.Length -gt 0) {
        Add-Warning "Content remains between \end{thebibliography} and \end{document}."
    }
}

Write-Host "IEEE two-column audit: $TexFile"

if ($issues.Count -eq 0) {
    Write-Host "Fatal/structural issues: none"
} else {
    Write-Host "Fatal/structural issues:"
    foreach ($item in $issues) { Write-Host "  - $item" }
}

if ($warnings.Count -eq 0) {
    Write-Host "Warnings: none"
} else {
    Write-Host "Warnings:"
    foreach ($item in $warnings) { Write-Host "  - $item" }
}

if ($issues.Count -gt 0) { exit 1 }
exit 0
