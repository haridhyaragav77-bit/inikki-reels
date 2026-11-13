#!/usr/bin/env bash
# Phone preview copy under 2.9 MB, for uploading through the Drive connector (its limit is about 3 MB per call).
# Full-quality reels go to Drive through the Engine (python -m engine.drive), which has no size limit.
# Usage: engine/tools/drive_preview.sh in.mp4 out.mp4
set -e
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
v=$(python3 -c "print(max(250, int((float("${TARGET_MB:-2.9}")*8*1024*1024/float('$d') - 64000)/1000)))")
tmp=$(mktemp -d)
ffmpeg -y -v error -i "$1" -vf "scale=540:960:flags=lanczos,hqdn3d=1.5:1.5:4:4" -c:v libx264 -preset slow -b:v ${v}k -pass 1 -passlogfile $tmp/p -an -f mp4 /dev/null
ffmpeg -y -v error -i "$1" -vf "scale=540:960:flags=lanczos,hqdn3d=1.5:1.5:4:4" -c:v libx264 -preset slow -b:v ${v}k -pass 2 -passlogfile $tmp/p -pix_fmt yuv420p -c:a aac -b:a 64k -movflags +faststart "$2"
rm -rf $tmp
echo "$(stat -c %s "$2") bytes, video ${v} kbps: $2"
