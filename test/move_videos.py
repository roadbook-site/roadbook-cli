import shutil
import glob
import os

# Define source and destination
# Windows usually has Downloads in user profile
src_dir = os.path.join(os.environ['USERPROFILE'], 'Downloads')
dst_dir = os.path.abspath("videos")

if not os.path.exists(dst_dir):
    os.makedirs(dst_dir)

# Find files
pattern = os.path.join(src_dir, "jimeng_video_*.mp4")
files = glob.glob(pattern)

print(f"Searching in: {pattern}")
print(f"Found {len(files)} videos.")

# Move files
for f in files:
    try:
        basename = os.path.basename(f)
        dst_path = os.path.join(dst_dir, basename)
        shutil.move(f, dst_path)
        print(f"Moved: {basename}")
    except Exception as e:
        print(f"Error moving {f}: {e}")
