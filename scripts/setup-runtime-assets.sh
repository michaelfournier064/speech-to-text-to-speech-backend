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

ensure_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command not found: $cmd" >&2
    exit 1
  fi
}

ensure_whisper_cli() {
  local whisper_root="$TOOLS_DIR/whisper"
  local whisper_cli="$whisper_root/whisper-cli"

  if [[ "$FORCE" -eq 0 && -x "$whisper_cli" ]]; then
    echo "Using existing whisper-cli: $whisper_cli"
    return
  fi

  ensure_command cmake
  ensure_command make
  ensure_command g++

  rm -rf "$whisper_root"
  mkdir -p "$whisper_root"

  local whisper_src_archive="$DOWNLOADS_DIR/whisper-source.tar.gz"
  download_with_fallback "whisper source" "$whisper_src_archive" \
    "https://github.com/ggml-org/whisper.cpp/archive/refs/tags/v1.8.4.tar.gz" \
    "https://github.com/ggml-org/whisper.cpp/archive/refs/tags/v1.8.3.tar.gz"

  local src_parent="$whisper_root/src"
  mkdir -p "$src_parent"
  tar -xzf "$whisper_src_archive" -C "$src_parent"

  local src_dir
  src_dir="$(find "$src_parent" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
  if [[ -z "$src_dir" ]]; then
    echo "Could not locate extracted whisper.cpp source directory." >&2
    exit 1
  fi

  local build_dir="$whisper_root/build"
  cmake -S "$src_dir" -B "$build_dir" -DCMAKE_BUILD_TYPE=Release
  cmake --build "$build_dir" --config Release -j "$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)"

  local built_cli
  built_cli="$(find "$build_dir" -type f -name whisper-cli | head -n 1)"
  if [[ -z "$built_cli" ]]; then
    echo "whisper-cli was not produced by the build." >&2
    exit 1
  fi

  cp "$built_cli" "$whisper_cli"
  chmod +x "$whisper_cli"
  echo "Built whisper-cli at: $whisper_cli"
}

FFMPEG_ARCHIVE="$DOWNLOADS_DIR/ffmpeg-linux-amd64.tar.xz"
PIPER_ARCHIVE="$DOWNLOADS_DIR/piper-linux-x86_64.tar.gz"

download_with_fallback "ffmpeg" "$FFMPEG_ARCHIVE" \
  "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz" \
  "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

download_with_fallback "piper" "$PIPER_ARCHIVE" \
  "https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz" \
  "https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz"

extract_archive "$FFMPEG_ARCHIVE" "$TOOLS_DIR/ffmpeg"
extract_archive "$PIPER_ARCHIVE" "$TOOLS_DIR/piper"
ensure_whisper_cli

find "$TOOLS_DIR/ffmpeg" -type f -name "ffmpeg" -exec chmod +x {} \;
find "$TOOLS_DIR/piper" -type f -name "piper" -exec chmod +x {} \;

FFMPEG_BIN="$(find "$TOOLS_DIR/ffmpeg" -type f -name ffmpeg | head -n 1 || true)"
if [[ -n "$FFMPEG_BIN" ]]; then
  if [[ "$FFMPEG_BIN" != "$TOOLS_DIR/ffmpeg/ffmpeg" ]]; then
    ln -sfn "$FFMPEG_BIN" "$TOOLS_DIR/ffmpeg/ffmpeg"
  fi
fi

PIPER_BIN="$(find "$TOOLS_DIR/piper" -type f -name piper | head -n 1 || true)"
if [[ -n "$PIPER_BIN" ]]; then
  if [[ ! -x "$PIPER_BIN" ]]; then
    chmod +x "$PIPER_BIN"
  fi

  # Keep a stable Linux path regardless of the archive's internal folder layout.
  ln -sfn "$PIPER_BIN" "$TOOLS_DIR/piper/piper-bin"
fi

download_model "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" "$MODELS_DIR/ggml-base.en.bin"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" "$MODELS_DIR/en_US-lessac-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" "$MODELS_DIR/en_US-lessac-medium.onnx.json"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx" "$MODELS_DIR/en_US-amy-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json" "$MODELS_DIR/en_US-amy-medium.onnx.json"

download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx" "$MODELS_DIR/en_US-ryan-medium.onnx"
download_model "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json" "$MODELS_DIR/en_US-ryan-medium.onnx.json"

echo "Runtime assets are ready."
echo "If needed, copy .env.example to .env and run the API."