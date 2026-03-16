import os
import requests

video_urls = [
    "https://v3-artist.vlabvod.com/ea7673e75a7754ae6f1c46ddb7f005d9/69b7c14b/video/tos/cn/tos-cn-v-148450/o41bDf2eOE6EEsteFQTAFCi2IlDWkOB0mBKEbJ/?a=4066&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&br=6903&bt=6903&cs=0&ds=12&ft=5QYTUxhhe6BMyqaLp9VJD12Nzj&mime_type=video_mp4&qs=0&rc=ZDU5ZWlkNjtkN2llZjg2NUBpM3hwZnU5cmllOTczNDM7M0A0YC9hNi8yNjAxLjAwYTMuYSNuLjYuMmRrYW9hLS1kNC9zcw%3D%3D&btag=80000e00008000&dy_q=1773646646&feature_id=04b16e464b574158bb99cac30ccb1f5e&l=202603161537264D597797BDFF66935E64",
    "https://v3-artist.vlabvod.com/394fc919fbb67a47fb11e467ee69eb16/69b7c14b/video/tos/cn/tos-cn-v-148450/oM8IY37sABktFCx20riigFEiBS8JQvefHEBpIp/?a=4066&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&br=6748&bt=6748&cs=0&ds=12&ft=5QYTUxhhe6BMyqaLp9VJD12Nzj&mime_type=video_mp4&qs=0&rc=aGk1ZGU2ZGc3ZjNlOTVlNUBpanVxZXY5cnk8OTczNDM7M0AtLTEtYTAtNi4xMzNeNGI2YSNpMC1yMmRjL29hLS1kNC9zcw%3D%3D&btag=80000e00008000&dy_q=1773646646&feature_id=04b16e464b574158bb99cac30ccb1f5e&l=202603161537264D597797BDFF66935E64",
    "https://v3-artist.vlabvod.com/e7002ed9d70ae0344fb63c7db752286d/69b7c14b/video/tos/cn/tos-cn-v-148450/owgGccb27KEFBEusMhvhaXETwiIusiQI1QZwz/?a=4066&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&br=6677&bt=6677&cs=0&ds=12&ft=5QYTUxhhe6BMyqaLp9VJD12Nzj&mime_type=video_mp4&qs=0&rc=OGk0NDdlOWZmN2loPDc2aEBpM3V0ZW05cmo4OTczNDM7M0BiLl9jYDU2NV8xMl8tMDQzYSNibS0yMmRrbW9hLS1kNC9zcw%3D%3D&btag=80000e00008000&dy_q=1773646646&feature_id=04b16e464b574158bb99cac30ccb1f5e&l=202603161537264D597797BDFF66935E64",
    "https://v3-artist.vlabvod.com/536d86df49149c89362c7747d3ad7b40/69b7c14b/video/tos/cn/tos-cn-v-148450/oggIGEkWpAV2hYKwSDBnlpftFgOQCIfBxH9dsO/?a=4066&ch=0&cr=0&dr=0&er=0&cd=0%7C0%7C0%7C0&br=6806&bt=6806&cs=0&ds=12&ft=5QYTUxhhe6BMyqaLp9VJD12Nzj&mime_type=video_mp4&qs=0&rc=ZzVnNmU5NWZoMzRpODY0ZEBpamZmaXI5cjU3OTczNDM7M0BeXjA1X2I1NTQxLmJgYjY1YSMwM2k0MmRrNG9hLS1kNC9zcw%3D%3D&btag=80000e00008000&dy_q=1773646646&feature_id=04b16e464b574158bb99cac30ccb1f5e&l=202603161537264D597797BDFF66935E64"
]

output_dir = "videos"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"Downloading {len(video_urls)} videos to {output_dir}...")

for i, url in enumerate(video_urls):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        filename = os.path.join(output_dir, f"video_{i+1}.mp4")
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download video {i+1}: {e}")

print("Download complete.")
