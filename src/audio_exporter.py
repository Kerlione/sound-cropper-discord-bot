import re
import os
import json
import uuid
import pytube
import requests
import sys
from bs4 import BeautifulSoup
from moviepy.audio.io.AudioFileClip import AudioFileClip
import urllib.request
from logging import Logger


class AgeRestrictedError(Exception):
    """Exception in case YouTube video is age restricted."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class AudioExporter():
    """Class for extracting the audio from YouTube 
    and Coub and cropping it to an mp3 of custom duration"""

    def __init__(self, logger: Logger, max_allowed_duration: int):
        self.logger = logger
        self.max_allowed_duration = max_allowed_duration
        self.folder_name_regex = re.compile(r'[^\w\-_. ]')
        self.youtube_url_regex = re.compile(
            r'^(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu.be/)([\w-]{11})(?:\S+)?$'
        )
        self.coub_url_regex = re.compile(
            r"^(?:https?://)?(?:www\.)?coub\.com/view/([a-zA-Z0-9]+)$")

    def _normalize_folder_name(self, folder_name: str):
        # Replace any invalid characters with underscores
        folder_name = self.folder_name_regex.sub('_', folder_name)

        # Remove leading/trailing whitespace
        folder_name = folder_name.strip()

        # Remove any consecutive underscores
        folder_name = re.sub('_{2,}', '_', folder_name)

        if sys.platform.startswith('win'):
            # Limit folder name to 255 characters (max allowed by NTFS file system)
            folder_name = folder_name[:255]

        return folder_name

    def _validate_youtube_url(self, url: str) -> bool:
        self.logger.info(f"Checking if '{url}' is a valid YouTube URL")
        match = self.youtube_url_regex.match(url)
        if match:
            return True
        else:
            return False

    def _validate_against_allowed_duration(self, duration: int):
        self.logger.info(
            f"Validating that requested clip duration ({duration}) does not exceed allowed ({self.max_allowed_duration})"
        )
        if duration > self.max_allowed_duration:
            raise Exception(
                f"Clip duration exceeds allowed max duration: '{self.max_allowed_duration}'"
            )

    def _validate_coub_url(self, url: str) -> bool:
        self.logger.info(f"Checking if '{url}' is a valid Coub URL")
        if self.coub_url_regex.match(url):
            return True
        else:
            return False

    def _get_coub_video_id(self, url: str) -> str:
        self.logger.info(f"Get Coub video id from URL: '{url}'")
        match = self.coub_url_regex.match(url)

        if match:
            video_id = match.group(1)
            self.logger.info(f"Extracted video ID is {video_id}")
            return video_id
        else:
            raise ValueError('Failed to get video id from Coub URL')

    def _download_coub_video(self, url) -> str:
        # Send a GET request to the URL
        response = urllib.request.urlopen(url)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response, 'html.parser')
        html = soup.prettify()
        # Find the video element and extract the source URL
        video_element = soup.find(id='coubPageCoubJson')
        if video_element is None:
            raise ValueError('No video element found')
        coub_details = json.loads(video_element.text)
        audio_url = coub_details["file_versions"]['html5']['audio']['high'][
            'url']  # type: ignore
        self.logger.info(f"Extracted audio url for coub: '{audio_url}'")
        video_id = self._get_coub_video_id(url)
        # create a folder with the video title
        folder_name = self._normalize_folder_name(video_id)
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        file_name = f"{video_id}.mp4"
        download_path = os.path.join(folder_name, file_name)
        self.logger.info(f"storing downloaded video as {file_name}")

        if audio_url is None:
            raise ValueError('Audio URL was not extracted')

        response = requests.get(audio_url)
        with open(download_path, 'wb') as f:
            f.write(response.content)

        return download_path

    def _download_youtube_video(self, url: str) -> str:
        # Create a YouTube object using the video URL
        youtube = pytube.YouTube(url)

        if youtube.age_restricted:
            self.logger.error(f"YouTube video ({url}) is age-restricted")
            raise AgeRestrictedError(
                'The video is age restricted and cannot be downloaded')

        title = youtube.title

        self.logger.info(f"Working with video '{title}'")

        # create a folder with the video title
        folder_name = self._normalize_folder_name(youtube.video_id)
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        audio_stream = youtube.streams.filter(only_audio=True).first()

        # check if video download was successful
        if audio_stream is None:
            raise ValueError('No audio stream found for video')

        # Get the audio stream of the YouTube video
        self.logger.info(
            f"Downloading audio of YouTube video into {folder_name}")
        return audio_stream.download(folder_name, f"{youtube.video_id}.mp4")

    def load_and_crop(self,
                      url: str,
                      full: bool,
                      start: int = -1,
                      end: int = -1) -> str:
        if not full:
            if start <= -1:
                prefix = '' if start == -1 else 'non-negative'
                raise ValueError(f"{prefix} start value is required")

        downloaded_file_path = ''

        if self._validate_youtube_url(url):
            downloaded_file_path = self._download_youtube_video(url)
        else:
            if self._validate_coub_url(url):
                downloaded_file_path = self._download_coub_video(url)

        if not downloaded_file_path:
            raise ValueError('Failed to download video')

        self.logger.info(
            f"Working with downloaded file '{downloaded_file_path}'")

        # use moviepy to extract the audio from the video and optionally clip it
        audio_clip = AudioFileClip(downloaded_file_path)

        if full:
            pass  # use full audio
        else:
            audio_clip = self.validate_and_get_subclip(audio_clip, start, end)

        self._validate_against_allowed_duration(audio_clip.duration)

        output_path = os.path.join(f"{uuid.uuid4()}.mp3")

        self.logger.info(f"Storing mp3 as {output_path}")
        audio_clip.write_audiofile(output_path)

        # delete the original video file
        audio_clip.close()
        self.logger.info(f"Removed {audio_clip.filename}")

        os.remove(downloaded_file_path)
        return output_path
        
    def validate_and_get_subclip(self, audio_clip: AudioFileClip, start: int, end: int) -> AudioFileClip:
        if start >= audio_clip.duration:
            raise ValueError(
                'start value is more or equal to duration of clip which doesn\'t make sense'
            )
        if not end:
            self.logger.debug(
                f"No --end value received. Setting it to the video duration: {audio_clip.duration}"
            )
            end = audio_clip.duration
        else:
            if start >= end:
                raise ValueError('end value must be more than start value')
            if end > audio_clip.duration:
                self.logger.warn(
                    f"Clip duration is less than requested end time. Falling back to duration '{audio_clip.duration}'"
                )
                end = audio_clip.duration
        self.logger.info(f"Creating a subclip [{start};{end}]")
        audio_clip = audio_clip.subclip(start, end)
        return audio_clip