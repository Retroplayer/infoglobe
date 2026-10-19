#!/usr/bin/env bash
set -euo pipefail
# Dependency locations are outside the project checkout; no application files are modified.
python -m venv /workspace/infoglobe-tools
/workspace/infoglobe-tools/bin/pip install cmake==4.4.4 ninja==1.13.2 rp2040-pio-emulator==0.88.0 pyserial==3.5
if [ ! -d /workspace/pico-sdk ]; then
    git clone --depth 1 --branch 2.2.0 https://github.com/raspberrypi/pico-sdk.git /workspace/pico-sdk
fi
test "$(git -C /workspace/pico-sdk rev-parse HEAD)" = a1438dff1d38bd9c65dbd693f0e5db4b9ae91779
git -C /workspace/pico-sdk submodule update --init lib/tinyusb
mkdir -p /workspace/toolchains
if [ ! -x /workspace/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi/bin/arm-none-eabi-gcc ]; then
    curl -fL --retry 2 'https://developer.arm.com/-/media/Files/downloads/gnu/13.3.rel1/binrel/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi.tar.xz' -o /workspace/toolchains/arm.tar.xz
    python - <<'PY'
from pathlib import Path
from hashlib import sha256
p = Path('/workspace/toolchains/arm.tar.xz')
assert sha256(p.read_bytes()).hexdigest() == '95c011cee430e64dd6087c75c800f04b9c49832cc1000127a92a97f9c8d83af4'
PY
    tar -xJf /workspace/toolchains/arm.tar.xz -C /workspace/toolchains
fi
/workspace/infoglobe-tools/bin/cmake -S /workspace/infoglobe/firmware -B /workspace/infoglobe/firmware/build -G Ninja \
    -DCMAKE_MAKE_PROGRAM=/workspace/infoglobe-tools/bin/ninja \
    -DPICO_SDK_PATH=/workspace/pico-sdk -DPICO_BOARD=waveshare_rp2040_zero \
    -DPICO_TOOLCHAIN_PATH=/workspace/toolchains/arm-gnu-toolchain-13.3.rel1-x86_64-arm-none-eabi \
    -DFETCHCONTENT_BASE_DIR=/workspace/pico-tools-cache
/workspace/infoglobe-tools/bin/cmake --build /workspace/infoglobe/firmware/build -j 4
bash /workspace/infoglobe/scripts/test-firmware.sh
