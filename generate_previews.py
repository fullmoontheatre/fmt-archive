#!/usr/bin/env python3
# generate_previews.py

import os
import sys
import io
from PIL import Image

# Import handlers for different file types with error handling
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None

try:
    from tinytag import TinyTag
except ImportError:
    TinyTag = None

# --- Configuration ---
# You can change these default values
SOURCE_FOLDER = 'objects'    # Use the objects directory by default
SMALL_FOLDER = 'small'       # Subfolder for small previews
THUMB_FOLDER = 'thumbs'      # Subfolder for thumbnail previews
SMALL_SIZE = (800, 800)      # Max dimensions for small previews
THUMB_SIZE = (450, 450)      # Max dimensions for thumbnails

# Supported file extensions (case-insensitive)
IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp'}
PDF_EXTS = {'pdf'}
VIDEO_EXTS = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv'}
AUDIO_EXTS = {'mp3', 'wav', 'flac', 'm4a', 'ogg'}

def save_previews(image, output_basename, small_dir, thumb_dir):
    """
    Saves small and thumbnail versions of a given PIL Image object.

    Args:
        image (PIL.Image.Image): The image to process.
        output_basename (str): The base name for the output files (without extension).
        small_dir (str): The directory to save the small preview.
        thumb_dir (str): The directory to save the thumbnail.
    """
    try:
        # Convert image to RGB mode to ensure compatibility with JPEG format
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Create and save the small preview, maintaining aspect ratio
        img_copy_small = image.copy()
        img_copy_small.thumbnail(SMALL_SIZE)
        small_path = os.path.join(small_dir, f"{output_basename}_sm.jpg")
        img_copy_small.save(small_path, 'JPEG', quality=85)

        # Create and save the thumbnail preview, maintaining aspect ratio
        img_copy_thumb = image.copy()
        img_copy_thumb.thumbnail(THUMB_SIZE)
        thumb_path = os.path.join(thumb_dir, f"{output_basename}_th.jpg")
        img_copy_thumb.save(thumb_path, 'JPEG', quality=80)
        
        print(f"  -> Successfully created previews for {output_basename}")
    except Exception as e:
        print(f"  -> ERROR: Could not save previews for {output_basename}: {e}")

def process_file(filepath, basename, ext, small_dir, thumb_dir):
    """
    Identifies the file type and calls the appropriate handler to generate previews.
    """
    print(f"Processing '{os.path.basename(filepath)}'...")
    
    pil_image = None

    try:
        if ext in IMAGE_EXTS:
            pil_image = Image.open(filepath)
        
        elif ext in PDF_EXTS:
            if not fitz:
                print("  -> SKIPPING: PyMuPDF is not installed. Cannot process PDFs.")
                return
            with fitz.open(filepath) as doc:
                if len(doc) > 0:
                    page = doc.load_page(0)  # Get the first page
                    pix = page.get_pixmap()
                    pil_image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        elif ext in VIDEO_EXTS:
            if not VideoFileClip:
                print("  -> SKIPPING: moviepy is not installed. Cannot process videos.")
                return
            with VideoFileClip(filepath) as clip:
                # Get a frame from 10% into the video for a more representative preview
                capture_time = min(clip.duration * 0.1, 1) # Capture at 10% or 1s, whichever is smaller
                frame = clip.get_frame(capture_time)
                pil_image = Image.fromarray(frame)

        elif ext in AUDIO_EXTS:
            if not TinyTag:
                print("  -> SKIPPING: tinytag is not installed. Cannot process audio files.")
                return
            tag = TinyTag.get(filepath, image=True)
            image_data = tag.get_image()
            if image_data:
                pil_image = Image.open(io.BytesIO(image_data))
            else:
                print(f"  -> SKIPPING: Audio file has no embedded cover art.")
                return
        else:
            print(f"  -> SKIPPING: Unsupported file type '{ext}'.")
            return

        if pil_image:
            save_previews(pil_image, basename, small_dir, thumb_dir)

    except Exception as e:
        print(f"  -> ERROR: Failed to process file: {e}")
    finally:
        if pil_image:
            pil_image.close()

def main():
    """Main function to run the preview generation script."""
    # Determine the source directory from command-line argument or use the default
    source_dir = sys.argv[1] if len(sys.argv) > 1 else SOURCE_FOLDER
    source_dir = os.path.abspath(source_dir)

    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' not found.")
        return

    # Define and create output directories
    small_dir = os.path.join(source_dir, SMALL_FOLDER)
    thumb_dir = os.path.join(source_dir, THUMB_FOLDER)
    os.makedirs(small_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    print(f"Scanning directory: {source_dir}")
    print(f"Saving small previews to: {small_dir}")
    print(f"Saving thumbnails to: {thumb_dir}")
    print("-" * 50)

    # Iterate over all items in the source directory
    for filename in os.listdir(source_dir):
        filepath = os.path.join(source_dir, filename)

        # Skip directories and the script's own output folders
        if not os.path.isfile(filepath) or filename in [SMALL_FOLDER, THUMB_FOLDER]:
            continue

        basename, ext_dot = os.path.splitext(filename)
        ext = ext_dot[1:].lower() if ext_dot else ''

        if not ext:
            continue # Skip files without an extension

        process_file(filepath, basename, ext, small_dir, thumb_dir)

    print("-" * 50)
    print("Processing complete. ✨")

if __name__ == "__main__":
    main()
