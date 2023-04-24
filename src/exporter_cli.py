import argparse
from audio_exporter import AudioExporter 
from logger import logger

def process_input() -> argparse.Namespace:
    # Define the CLI arguments
    parser = argparse.ArgumentParser(description='Download audio from YouTube video and optionally cut it.')
    parser.add_argument('url', type=str, help='the URL of the YouTube video')
    parser.add_argument('--start', type=int, required=False, help='the start time (in seconds) to cut from the audio', default=-1)
    parser.add_argument('--end', type=int, required=False, help='the end time (in seconds) to cut to from the audio')
    parser.add_argument('--full', action='store_true', help='download the full audio without cutting')
    args = parser.parse_args()
    return args

def main():
    args = process_input()
    # your code goes here
    exporter = AudioExporter(logger, 180)
    print(f'Stored result in {exporter.load_and_crop(args.url, args.full, args.start, args.end)}')

if __name__ == '__main__':
    main()
