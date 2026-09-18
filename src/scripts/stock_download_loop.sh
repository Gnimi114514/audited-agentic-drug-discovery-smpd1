#!/bin/bash
# robust ZINC stock downloader: 6 attempts, resume, 504-garbage cleanup
TARGET=/mnt/c/Users/Gnimi/.zcode/workspace/default/cognition-drug-discovery/aizynth_models/zinc_stock.hdf5
URL="https://zenodo.org/api/records/11430881/files/zinc_stock.hdf5/content"
MIN=1339000000

for i in 1 2 3 4 5 6; do
  curl -sL --max-time 2400 -C - -o "$TARGET" "$URL"
  sz=$(stat -c%s "$TARGET" 2>/dev/null || echo 0)
  head4=$(head -c 4 "$TARGET" 2>/dev/null)
  echo "attempt $i: size=$sz head=$head4"
  if [ "$sz" -gt "$MIN" ]; then
    echo "COMPLETE"
    break
  fi
  # 504 garbage (html) -> remove and restart clean
  if [ "$head4" = "<htm" ] || [ "$sz" -lt 10000 ]; then
    rm -f "$TARGET"
    echo "cleaned partial/garbage"
  fi
  sleep 60
done
ls -la "$TARGET"
