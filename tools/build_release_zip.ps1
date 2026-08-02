param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,
    [string]$Output
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = (Resolve-Path -LiteralPath $SourceRoot).Path

if (-not $Output) {
    $Output = Join-Path $repositoryRoot 'release\FTC02_Korean_LayeredFS.zip'
}
$outputPath = [IO.Path]::GetFullPath($Output)
$outputDirectory = Split-Path -Parent $outputPath
$temporaryPath = Join-Path $outputDirectory 'FTC02_Korean_LayeredFS.building.zip'

$atmosphere = Join-Path $source 'atmosphere'
$licenses = Join-Path $source 'licenses'
foreach ($requiredDirectory in @($atmosphere, $licenses)) {
    if (-not (Test-Path -LiteralPath $requiredDirectory -PathType Container)) {
        throw "필수 배포 폴더가 없습니다: $requiredDirectory"
    }
}

$manifestPath = Join-Path $repositoryRoot 'release\release_manifest.json'
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath |
    ConvertFrom-Json
$expectedRuntimeFiles = [int]$manifest.runtime_files
$titleId = ([string]$manifest.title_id).ToLowerInvariant()
$romfsPrefix = "atmosphere/contents/$titleId/romfs/"

if (-not (Get-Command tar.exe -ErrorAction SilentlyContinue)) {
    throw '표준 / 경로로 ZIP을 만드는 tar.exe를 찾을 수 없습니다.'
}

New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null
if (Test-Path -LiteralPath $temporaryPath -PathType Leaf) {
    Remove-Item -LiteralPath $temporaryPath -Force
}

Push-Location $source
try {
    & tar.exe -a -c -f $temporaryPath atmosphere licenses
    if ($LASTEXITCODE -ne 0) {
        throw "tar.exe ZIP 생성 실패: exit $LASTEXITCODE"
    }
}
finally {
    Pop-Location
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($temporaryPath)
try {
    $entries = @($archive.Entries | Where-Object { -not $_.FullName.EndsWith('/') })
    $nonPosix = @($entries | Where-Object { $_.FullName.Contains('\') })
    if ($nonPosix.Count -ne 0) {
        throw "ZIP 엔트리에 역슬래시 경로가 있습니다: $($nonPosix[0].FullName)"
    }

    $runtimeEntries = @($entries | Where-Object {
        $_.FullName.StartsWith($romfsPrefix)
    })
    if ($runtimeEntries.Count -ne $expectedRuntimeFiles) {
        throw "RomFS 파일 수 불일치: $($runtimeEntries.Count) != $expectedRuntimeFiles"
    }

    $allowedLicenseFiles = @(
        'licenses/FONT_NOTICES.md',
        'licenses/OFL-1.1.txt'
    )
    $unexpected = @($entries | Where-Object {
        -not $_.FullName.StartsWith($romfsPrefix) -and
        $_.FullName -notin $allowedLicenseFiles
    })
    if ($unexpected.Count -ne 0) {
        throw "ZIP에 불필요한 파일이 있습니다: $($unexpected[0].FullName)"
    }

    $sourceFiles = @{}
    foreach ($rootName in @('atmosphere', 'licenses')) {
        $rootPath = Join-Path $source $rootName
        foreach ($file in Get-ChildItem -LiteralPath $rootPath -Recurse -File) {
            $relative = $file.FullName.Substring($source.Length + 1).Replace('\', '/')
            $sourceFiles[$relative] = $file.FullName
        }
    }

    if ($entries.Count -ne $sourceFiles.Count) {
        throw "전체 파일 수 불일치: ZIP $($entries.Count), 원본 $($sourceFiles.Count)"
    }

    foreach ($entry in $entries) {
        if (-not $sourceFiles.ContainsKey($entry.FullName)) {
            throw "원본 배포 폴더에 없는 ZIP 파일입니다: $($entry.FullName)"
        }
        $entryStream = $entry.Open()
        try {
            $entryHash = [Security.Cryptography.SHA256]::Create().ComputeHash($entryStream)
        }
        finally {
            $entryStream.Dispose()
        }
        $sourceHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourceFiles[$entry.FullName]).Hash
        $entryHashText = -join ($entryHash | ForEach-Object { $_.ToString('X2') })
        if ($entryHashText -ne $sourceHash) {
            throw "ZIP 파일 해시 불일치: $($entry.FullName)"
        }
    }
}
finally {
    $archive.Dispose()
}

Move-Item -LiteralPath $temporaryPath -Destination $outputPath -Force
$result = Get-Item -LiteralPath $outputPath
$resultHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash

Write-Output "생성 완료: $outputPath"
Write-Output "RomFS 파일: $expectedRuntimeFiles"
Write-Output "전체 파일: $($sourceFiles.Count)"
Write-Output "크기: $($result.Length)"
Write-Output "SHA256: $resultHash"
