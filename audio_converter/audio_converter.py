#  py_album_condense - a simple tool to compress and condense your album collections
#  Copyright (c) 2022 kewenyu
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import abc
import os
import asyncio
import json

from common.config import config
from cue.cue_parser import CueContentParser
from cue.cue_loader import CueFileLoader


class AudioConverter(metaclass=abc.ABCMeta):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        self.semaphore = semaphore
        self.file_path = file_path
        self.src_path = src_path
        self.dst_path = dst_path

    @abc.abstractmethod
    async def single_convert(self):
        raise NotImplemented

    @abc.abstractmethod
    async def cue_convert(self):
        raise NotImplemented

    @abc.abstractmethod
    def get_ext(self):
        raise NotImplemented

    def _get_cue_tracks(self):
        cue_path = os.path.splitext(self.file_path)[0] + '.cue'
        cue_content = CueFileLoader(cue_path).get_content()
        tracks = CueContentParser(os.path.splitext(os.path.basename(self.file_path))[0], cue_content).get_tracks()
        return tracks


class AudioUtils:
    @staticmethod
    async def get_metadata_by_ffprobe(file_path):
        ffprobe_path = config.get('executable', {}).get('ffprobe', 'ffprobe')
        ffprobe_cmd = f'"{ffprobe_path}" -loglevel error -show_format -of json "{file_path}"'
        ffprobe_process = await asyncio.create_subprocess_shell(
            ffprobe_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        ffprobe_stdout, ffprobe_stderr = await ffprobe_process.communicate()

        src_info = json.loads(ffprobe_stdout)
        metadata = src_info.get('format', {}).get('tags', {})

        return metadata

    @staticmethod
    async def add_metadata_by_ffmpeg(metadata, origin_file_path, new_file_path):
        ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
        ffmpeg_cmd = f'"{ffmpeg_path}" -i "{origin_file_path}" -c copy'
        ffmpeg_cmd += ' ' + ' '.join([f'-metadata "{k}"="{v}"' for k, v in metadata.items()])
        ffmpeg_cmd += f' "{new_file_path}"'
        ffmpeg_process = await asyncio.create_subprocess_shell(ffmpeg_cmd, stderr=asyncio.subprocess.DEVNULL)
        await ffmpeg_process.communicate()
        os.remove(origin_file_path)
