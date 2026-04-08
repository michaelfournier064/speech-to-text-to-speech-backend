param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$downloadsDir = Join-Path $repoRoot "tools/downloads"
$toolsDir = Join-Path $repoRoot "tools/bin"
$modelsDir = Join-Path $repoRoot "models"

New-Item -ItemType Directory -Path $downloadsDir -Force | Out-Null
New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
New-Item -ItemType Directory -Path $modelsDir -Force | Out-Null

function Download-IfMissing {
    param(
        [string]$Url,
        [string]$Destination
    )

    if (-not $Force -and (Test-Path $Destination)) {
        Write-Host "Using existing file: $Destination"
        return
    }

    Write-Host "Downloading: $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Destination
}

function Download-WithFallback {
    param(
        [string[]]$Urls,
        [string]$Destination,
        [string]$Label
    )

    if (-not $Force -and (Test-Path $Destination)) {
        Write-Host "Using existing file: $Destination"
        return
    }

    foreach ($url in $Urls) {
        try {
            Write-Host "Downloading $Label from: $url"
            Invoke-WebRequest -Uri $url -OutFile $Destination
            return
        }
        catch {
            if (Test-Path $Destination) {
                Remove-Item -Force $Destination
            }

            Write-Warning "Failed to download $Label from $url"
        }
    }

    throw "Failed to download $Label from all configured sources."
}

function Expand-Zip {
    param(
        [string]$ZipPath,
        [string]$Destination
    )

    if ($Force -and (Test-Path $Destination)) {
        Remove-Item -Recurse -Force $Destination
    }

    if (-not (Test-Path $Destination)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
        Write-Host "Extracting: $ZipPath -> $Destination"
        Expand-Archive -Path $ZipPath -DestinationPath $Destination -Force
    }
    else {
        Write-Host "Using existing extracted directory: $Destination"
    }
}

function Download-Model {
    param(
        [string]$Url,
        [string]$Destination
    )

    if (-not $Force -and (Test-Path $Destination)) {
        Write-Host "Using existing model: $Destination"
        return
    }

    Write-Host "Downloading model: $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Destination
}

# Tool archives (Windows x64)
$ffmpegZip = Join-Path $downloadsDir "ffmpeg-win64.zip"
$whisperZip = Join-Path $downloadsDir "whisper-bin-x64.zip"
$piperZip = Join-Path $downloadsDir "piper_windows_amd64.zip"

Download-WithFallback -Label "ffmpeg" -Destination $ffmpegZip -Urls @(
    "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
)
Download-WithFallback -Label "whisper" -Destination $whisperZip -Urls @(
    "https://github.com/ggml-org/whisper.cpp/releases/download/v1.7.6/whisper-bin-x64.zip",
    "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.1/whisper-bin-x64.zip"
)
Download-WithFallback -Label "piper" -Destination $piperZip -Urls @(
    "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_windows_amd64.zip",
    "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip"
)

Expand-Zip -ZipPath $ffmpegZip -Destination (Join-Path $toolsDir "ffmpeg")
Expand-Zip -ZipPath $whisperZip -Destination (Join-Path $toolsDir "whisper")
Expand-Zip -ZipPath $piperZip -Destination (Join-Path $toolsDir "piper")

# Speech model files
Download-Model -Url "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" -Destination (Join-Path $modelsDir "ggml-base.en.bin")

Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -Destination (Join-Path $modelsDir "en_US-lessac-medium.onnx")
Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -Destination (Join-Path $modelsDir "en_US-lessac-medium.onnx.json")

Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" -Destination (Join-Path $modelsDir "en_US-amy-medium.onnx")
Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" -Destination (Join-Path $modelsDir "en_US-amy-medium.onnx.json")

Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx" -Destination (Join-Path $modelsDir "en_US-ryan-medium.onnx")
Download-Model -Url "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json" -Destination (Join-Path $modelsDir "en_US-ryan-medium.onnx.json")

Write-Host "Runtime assets are ready."
Write-Host "If needed, copy .env.example to .env and run the API."
