#!/bin/bash
# GNINA dependency completion: cublas, cufft, cusparse from NVIDIA redist
set -u
cd /tmp
BASE=https://developer.download.nvidia.com/compute/cuda/redist
ok=1
fetch() {  # fetch <component> <version>
  local comp=$1 ver=$2
  local name="${comp}-linux-x86_64-${ver}-archive.tar.xz"
  if [ ! -d "/tmp/${comp}-linux-x86_64-${ver}-archive" ]; then
    code=$(curl -sL -w "%{http_code}" --max-time 900 -o "/tmp/${name}" "${BASE}/${comp}/linux-x86_64/${name}")
    echo "HTTP $code for ${name} ($(stat -c%s "/tmp/${name}" 2>/dev/null) bytes)"
    if [ "$code" != "200" ]; then ok=0; rm -f "/tmp/${name}"; return 1; fi
    tar -xJf "/tmp/${name}" -C /tmp
  fi
  return 0
}
fetch cublas 12.8.4.1 || ok=0
fetch cufft 11.3.3.83 || ok=0
fetch cusparse 12.5.4.2 || ok=0

export LD_LIBRARY_PATH=/tmp/cudnn-linux-x86_64-9.7.1.26_cuda12-archive/lib:/tmp/cuda_cudart-linux-x86_64-12.8.90-archive/lib:/tmp/cublas-linux-x86_64-12.8.4.1-archive/lib:/tmp/cufft-linux-x86_64-11.3.3.83-archive/lib:/tmp/cusparse-linux-x86_64-12.5.4.2-archive/lib
echo "== gnina version test =="
/tmp/gnina --version 2>&1 | head -3
