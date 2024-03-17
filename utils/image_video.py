from PIL import Image
import requests
from pathlib import Path
import cv2


def download_image(url, filename):
    response = requests.get(url, stream=True)
    response.raise_for_status()

    path = Path(filename)
    with path.open('wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return path


def resize_image(image_path, min_dimension=768, output_path=r".\temp\resized_image.jpg"):
    image = Image.open(image_path)
    original_width, original_height = image.size
    print(f"original height:{original_height}, original width:{original_width}")

    if original_width > min_dimension or original_height > min_dimension:
        print("Resizing image.")
        ratio = min(min_dimension / original_width, min_dimension / original_height)
        new_width = max(min_dimension, int(original_width * ratio))
        new_height = max(min_dimension, int(original_height * ratio))
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        print(f"new height:{new_height}, new width:{new_width}") 
       

    image.save(output_path)

def get_last_frame(video_path, iteration):
    video = cv2.VideoCapture(video_path)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = video.read()
    cv2.waitKey(0)
    cv2.imwrite(f'lastframe_{iteration}.jpg', frame)
    video.release()

def merge_videos(video_paths, image_path, return_to_source=False, end_card=None, add_end_card=False):
    input_files = video_paths
    output_file = "main_video.mp4"

    frames = []
    frame_index = 0  # Keep track of the frame index

    if add_end_card:
        print("Adding end card...")
        for i in range(1, 12):
            resize_image(end_card, "resized_end_card.jpg")
            frames.append(cv2.imread("resized_end_card.jpg"))
            frame_index += 1

    print("Adding original image frames...")
    for i in range(1, 8):
        frames.append(cv2.imread(image_path))
        frame_index += 1
        i+=1

    print("Adding video frames...")
    for input_file in input_files:
        cap = cv2.VideoCapture(input_file)

        # Check if camera opened successfully
        if not cap.isOpened(): 
            print("Error opening video file")

        # Read the video frames into a list, skipping every second frame
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
                frame_index += 1
            else:
                break
                

    if return_to_source:            
        reversed_frames = frames[::-3]
        final_frames = frames[::2] + reversed_frames
    else:
        final_frames = frames

    if add_end_card:
        print("Adding end card...")
        for i in range(1, 36):
            final_frames.append(cv2.imread("resized_end_card.jpg"))
            frame_index += 1
    
    frame_height, frame_width = frames[0].shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_file, fourcc, 20.0, (frame_width, frame_height))

    for frame in final_frames:
        out.write(frame)
    
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def build_video(source_path, iterations, return_to_source=False, end_card=None, add_end_card=False):    
    video_paths = []
    image_path = source_path
    for i in range(iterations):
        resize_image(image_path, f"resized_{i}.jpg")
        generation_id = generate_video(f"resized_{i}.jpg")
        if generation_id:
            retrieve_video(generation_id, i)
            print("Generating last frame...")
            video_paths.append(f"video_{i}.mp4")
            get_last_frame(f"video_{i}.mp4", i)
        image_path = f"lastframe_{i}.jpg"
    merge_videos(video_paths, "resized_0.jpg", return_to_source, end_card, add_end_card)

