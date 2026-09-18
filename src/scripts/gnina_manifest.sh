#!/bin/bash
# probe versioned NVIDIA redist manifests and fetch cublas/cufft/cusparse
set -u
for v in 12.8.1 12.8.0 12.6.3 12.4.1; do
  code=$(curl -sL --max-time 60 -w "%{http_code}" "https://developer.download.nvidia.com/compute/cuda/redist/redist-cuda-${v}.json" -o "/tmp/redist-${v}.json")
  size=$(stat -c%s "/tmp/redist-${v}.json" 2>/dev/null)
  echo "manifest ${v}: HTTP ${code} size ${size}"
done
# use the first manifest that parses
for v in 12.8.1 12.8.0 12.6.3 12.4.1; do
  if python3 - <<PYEOF 2>/dev/null
import json
d = json.load(open("/tmp/redist-${v}.json"))
for c in ["cublas", "cufft", "cusparse"]:
    print("https://developer.download.nvidia.com/compute/cuda/redist/" + d[c]["linux-x86_64"]["relative_path"])
PYEOF
  then
    echo "MANIFEST_OK=${v}"
    break
  fi
done
