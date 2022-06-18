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
import asyncio

from audio_converter.audio_converter import AudioConverter, AudioUtils
from common.config import config
from common.util import PathUtils


class TakConverter(AudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    async def single_convert(self):
        ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
        takc_path = config.get('executable', {}).get('takc', 'takc')
        tak_preset = config.get('tak_config', {}).get('preset', 'p4m')

        async with self.semaphore:
            print(f'converting to TAK: {self.file_path}')

            new_file_path = PathUtils.create_file_path_struct(self.file_path, self.src_path, self.dst_path, '.tak')
            metadata = await AudioUtils.get_metadata_by_ffprobe(self.file_path)

            ffmpeg_cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" -f wav -'
            takc_cmd = f'"{takc_path}" -e -ihs -silent -md5 -overwrite -{tak_preset}'
            takc_cmd += ' ' + ' '.join([f'-tt "{k}"="{v}"' for k, v in metadata.items()])
            takc_cmd += f' - "{new_file_path}"'

            pipe_reader, pipe_writer = os.pipe()

            ffmpeg_process = await asyncio.create_subprocess_shell(
                ffmpeg_cmd,
                stdout=pipe_writer,
                stderr=asyncio.subprocess.DEVNULL
            )
            os.close(pipe_writer)

            takc_process = await asyncio.create_subprocess_shell(
                takc_cmd,
                stdin=pipe_reader,
            )
            os.close(pipe_reader)

            await takc_process.communicate()
            await ffmpeg_process.communicate()

    async def cue_convert(self):
        sub_workers_list = []
        ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
        takc_path = config.get('executable', {}).get('takc', 'takc')
        tak_preset = config.get('tak_config', {}).get('preset', 'p4m')

        async with self.semaphore:
            new_file_dir = PathUtils.create_dir_path_struct(self.file_path, self.src_path, self.dst_path)
            tracks = self._get_cue_tracks()

            for track in tracks:
                out_track_name = f'{track["idx"]:02d}. {track["title"]}.tak'
                out_track_path = os.path.join(new_file_dir, out_track_name)

                ffmpeg_cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" -ss {track["start_time"]}'
                if track.get('end_time'):
                    ffmpeg_cmd += f' -to {track["end_time"]}'
                ffmpeg_cmd += ' -f wav -'

                takc_cmd = f'"{takc_path}" -e -ihs -silent -md5 -overwrite -{tak_preset}'
                takc_cmd += ' ' + ' '.join([f'-tt "{k}"="{v}"' for k, v in track['metadata'].items()])
                takc_cmd += f' - "{out_track_path}"'

                async def track_task(f_cmd, t_cmd, idx):
                    async with self.semaphore:
                        print(f'converting to TAK: {self.file_path}, track {idx:02d}')

                        pipe_reader, pipe_writer = os.pipe()

                        ffmpeg_process = await asyncio.create_subprocess_shell(
                            f_cmd,
                            stderr=asyncio.subprocess.DEVNULL,
                            stdout=pipe_writer
                        )
                        os.close(pipe_writer)

                        takc_process = await asyncio.create_subprocess_shell(
                            t_cmd,
                            stdin=pipe_reader,
                        )
                        os.close(pipe_reader)

                        await takc_process.communicate()
                        await ffmpeg_process.communicate()

                sub_worker = asyncio.create_task(track_task(ffmpeg_cmd, takc_cmd, track["idx"]))
                sub_workers_list.append(sub_worker)

        await asyncio.gather(*sub_workers_list)

    def get_ext(self):
        return '.tak'
