#!/usr/bin/env bash

set -euo pipefail

FORCE=0
if [[ "${1:-}" == "--force" || "${1:-}" == "-f" ]]; then
  FORCE=1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOWNLOADS_DIR="$REPO_ROOT/tools/downloads"
TOOLS_DIR="$REPO_ROOT/tools/bin"
MODELS_DIR="$REPO_ROOT/models"

mkdir -p "$DOWNLOADS_DIR" "$TOOLS_DIR" "$MODELS_DIR"

download_with_fallback() {
  local label="$1"
  local destination="$2"
  shift 2

  if [[ "$FORCE" -eq 0 && -f "$destination" ]]; then
    echo "Using existing file: $destination"
    return
  fi

  local url
  for url in "$@"; do
    echo "Downloading $label from: $url"
    if curl -fL --retry 3 --retry-delay 1 "$url" -o "$destination"; then
      return
    fi

    rm -f "$destination"
    echo "Failed to download $label from $url"
  done

  echo "Failed to download $label from all configured sources." >&2
  exit 1
}

extract_archive() {
  local archive_path="$1"
  local destination="$2"

  if [[ "$FORCE" -eq 1 && -d "$destination" ]]; then
    rm -rf "$destination"
  fi

  if [[ -d "$destination" ]]; then
    echo "Using existing extracted directory: $destination"
    return
  fi

  mkdir -p "$destination"
  echo "Extracting: $archive_path -> $destination"

  case "$archive_path" in
    *.tar.gz)
      tar -xzf "$archive_path" -C "$destination"
      ;;
    *.tar.xz)
      tar -xJf "$archive_path" -C "$destination"
      ;;
    *.zip)
      unzip -oq "$archive_path" -d "$destination"
      ;;
    *)
      echo "Unsupported archive format: $archive_path" >&2
      exit 1
      ;;
  esac
}

download_model() {
  local url="$1"
  local destination="$2"

  if [[ "$FORCE" -eq 0 && -f "$destination" ]]; then
    echo "Using existing model: $destination"
    return
  fi

  echo "Downloading model: $url"
  curl -fL --retry 3 --retry-delay 1 "$url" -o "$destination"
}

FFMPEG_ARCHIVE="$DOWNLOADS_DIR/ffmpeg-linux-amd64.tar.xz"
WHISPER_ARCHIVE="$DOWNLOADS_DIR/whisper-bin-x64.tar.gz"
PIPER_ARCHIVE="$DOWNLOADS_DIR/piper-linux-x86_64.tar.gz"

download_with_fallback "ffmpeg" "$FFMPEG_ARCHIVE" \
  "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" \
  "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

download_with_fallback "whisper" "$WHISPER_ARCHIVE" \
  "https://github.com/ggml-org/whisper.cpp/releases/download/v1.8.1/whisper-bin-x64.tar.gz" \
  "https://github.com/ggml-org/whisper.cpp/releases/download/v1.7.6/whisper-bin-x64.tar.gz"

download_with_fallback "piper" "$PIPER_ARCHIVE" \
  "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz" \
  "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"

extract_archive "$FFMPEG_ARCHIVE" "$TOOLS_DIR/ffmpeg"
extract_archive "$WHISPER_ARCHIVE" "$TOOLS_DIR/whisper"
extract_archive "$PIPER_ARCHIVE" "$TOOLS_DIR/piper"

find "$TOOLS_DIR/ffmpeg" -type f -name "ffmpeg" -exec chmod +x {} \;
find "$TOOLS_DIR/whisper" -type f \( -name "whisper-cli" -o -name "whisper" \) -exec chmod +x {} \;
find "$TOOLS_DIR/piper" -type f -name "piper" -exec chmod +x {} \;

download_model "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" "$MODELS_DIR/ggml-base.en.bin"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" "$MODELS_DIR/en_US-lessac-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" "$MODELS_DIR/en_US-lessac-medium.onnx.json"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" "$MODELS_DIR/en_US-amy-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" "$MODELS_DIR/en_US-amy-medium.onnx.json"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx" "$MODELS_DIR/en_US-ryan-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json" "$MODELS_DIR/en_US-ryan-medium.onnx.json"

echo "Runtime assets are ready."
echo "If needed, copy .env.example to .env and run the API."