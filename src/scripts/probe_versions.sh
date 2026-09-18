#!/bin/bash
# probe NVIDIA redist component versions with HEAD requests
BASE=https://developer.download.nvidia.com/compute/cuda/redist
probe() { # component ver...
  local comp=$1; shift
  for ver in "$@"; do
    local name="${comp}-linux-x86_64-${ver}-archive.tar.xz"
    local code=$(curl -sIL --max-time 30 -o /dev/null -w "%{http_code}" "${BASE}/${comp}/linux-x86_64/${name}")
    echo "${comp} ${ver} -> ${code}"
  done
}
probe cublas 12.8.4.1 12.8.3.14 12.8.3.8 12.6.4.1 12.6.3.3 12.5.3.2 12.4.5.8
probe cufft 11.3.3.83 11.3.3.41 11.3.2.82 11.2.1.3 11.3.0.80
probe cusparse 12.5.7.53 12.5.4.2 12.5.3.2 12.5.1.3 12.3.1.166
