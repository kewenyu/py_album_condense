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

import os
import abc
import asyncio

from audio_converter.audio_converter import AudioConverter
from common.config import config
from common.util import PathUtils


class FFMPEGAudioConverter(AudioConverter, metaclass=abc.ABCMeta):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    async def single_convert(self):
        async with self.semaphore:
            print(f'converting to {self._get_format_name()}: {self.file_path}')

            new_file_path = PathUtils.create_file_path_struct(
                self.file_path, self.src_path, self.dst_path, self._get_ext()
            )
            ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
            cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" {self._get_parameter()} "{new_file_path}"'

            process = await asyncio.create_subprocess_shell(cmd, stderr=asyncio.subprocess.DEVNULL)
            await process.communicate()

    async def cue_convert(self):
        sub_workers_list = []

        async with self.semaphore:
            new_file_dir = PathUtils.create_dir_path_struct(self.file_path, self.src_path, self.dst_path)

            tracks = self._get_cue_tracks()
            for track in tracks:
                out_track_name = f'{track["idx"]:02d}. {track["title"]}{self._get_ext()}'
                out_track_path = os.path.join(new_file_dir, out_track_name)

                ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
                ffmpeg_cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" -ss {track["start_time"]}'
                if track.get('end_time'):
                    ffmpeg_cmd += f' -to {track["end_time"]}'
                ffmpeg_cmd += ' ' + ' '.join([f'-metadata "{k}"="{v}"' for k, v in track['metadata'].items()])
                ffmpeg_cmd += f' {self._get_parameter()} "{out_track_path}"'

                async def track_task(cmd, idx):
                    async with self.semaphore:
                        print(f'converting to {self._get_format_name()}: {self.file_path}, track {idx:02d}')
                        process = await asyncio.create_subprocess_shell(cmd, stderr=asyncio.subprocess.DEVNULL)
                        await process.communicate()

                sub_worker = asyncio.create_task(track_task(ffmpeg_cmd, track["idx"]))
                sub_workers_list.append(sub_worker)

        await asyncio.gather(*sub_workers_list)

    def get_ext(self):
        return self._get_ext()

    @abc.abstractmethod
    def _get_ext(self):
        raise NotImplemented

    @abc.abstractmethod
    def _get_format_name(self):
        raise NotImplemented

    @abc.abstractmethod
    def _get_parameter(self):
        raise NotImplemented


class OpusConverter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.opus'

    def _get_format_name(self):
        return 'OPUS'

    def _get_parameter(self):
        bitrate = config.get('opus_config', {}).get('bitrate', 128)
        return f'-c:a libopus -b:a {bitrate}k'


class MP3Converter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.mp3'

    def _get_format_name(self):
        return 'MP3'

    def _get_parameter(self):
        bitrate = config.get('mp3_config', {}).get('bitrate', 320)
        is_joint = config.get('mp3_config', {}).get('joint', True)
        return f'-c:a libmp3lame -b:a {bitrate}k -joint_stereo {is_joint}'


class VorbisConverter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.ogg'

    def _get_format_name(self):
        return 'Vorbis'

    def _get_parameter(self):
        bitrate = config.get('vorbis_config', {}).get('bitrate', 320)
        return f'-c:a libvorbis -b:a {bitrate}k'


class FLACConverter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.flac'

    def _get_format_name(self):
        return 'FLAC'

    def _get_parameter(self):
        compression_level = config.get('flac_config', {}).get('compression_level', 8)
        return f'-c:a flac -compression_level {compression_level}'


class TrueAudioConverter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.tta'

    def _get_format_name(self):
        return 'TrueAudio'

    def _get_parameter(self):
        return '-c:a tta'


class WavPackConverter(FFMPEGAudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.wv'

    def _get_format_name(self):
        return 'WavPack'

    def _get_parameter(self):
        compression_level = config.get('wavpack_config', {}).get('compression_level', 6)
        return f'-c:a wavpack -compression_level {compression_level}'
