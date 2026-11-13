#!/usr/bin/env bash
# Phone preview copy under 10 MB (for Drive rehearsal/): 720x1280, bitrate sized to the reel's length.
# Usage: engine/tools/phone_preview.sh in.mp4 out.mp4
set -e
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$1")
kbps=$(python3 -c "print(int(min(2600, (9.2*8*1024)/float('$d') - 130)))")
ffmpeg -y -v error -i "$1" -vf scale=720:1280:flags=lanczos -c:v libx264 -preset slow -b:v ${kbps}k -maxrate ${kbps}k -bufsize $((kbps*2))k -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$2"
ls -la "$2" | awk '{print $5, $9}'
