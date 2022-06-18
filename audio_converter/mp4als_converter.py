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


class ALSConverter(AudioConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    async def single_convert(self):
        ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
        mp4als_path = config.get('executable', {}).get('mp4als', 'mp4als')

        async with self.semaphore:
            print(f'converting to ALS: {self.file_path}')
            new_file_path = PathUtils.create_file_path_struct(self.file_path, self.src_path, self.dst_path, '.mp4')
            tmp_wav_file_path = os.path.join(
                os.path.dirname(new_file_path),
                f'_tmp_{os.path.basename(new_file_path)}.wav'
            )
            tmp_mp4_file_path = os.path.join(os.path.dirname(new_file_path), f'_tmp_{os.path.basename(new_file_path)}')

            ffmpeg_cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" "{tmp_wav_file_path}"'
            ffmpeg_process = await asyncio.create_subprocess_shell(
                ffmpeg_cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await ffmpeg_process.communicate()

            mp4als_cmd = f'"{mp4als_path}" -7 -r-1 -MP4 "{tmp_wav_file_path}" "{tmp_mp4_file_path}"'
            mp4als_process = await asyncio.create_subprocess_shell(
                mp4als_cmd,
                stderr=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.DEVNULL,
            )
            await mp4als_process.communicate()

            metadata = await AudioUtils.get_metadata_by_ffprobe(self.file_path)
            await AudioUtils.add_metadata_by_ffmpeg(metadata, tmp_mp4_file_path, new_file_path)
            os.rename(new_file_path, os.path.splitext(new_file_path)[0] + '.m4a')
            os.remove(tmp_wav_file_path)

    async def cue_convert(self):
        sub_workers_list = []
        ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
        mp4als_path = config.get('executable', {}).get('mp4als', 'mp4als')

        async with self.semaphore:
            new_file_dir = PathUtils.create_dir_path_struct(self.file_path, self.src_path, self.dst_path)
            tracks = self._get_cue_tracks()

            for track in tracks:
                out_track_name = f'{track["idx"]:02d}. {track["title"]}.mp4'
                out_track_path = os.path.join(new_file_dir, out_track_name)
                tmp_wav_track_path = os.path.join(
                    os.path.dirname(out_track_path),
                    f'_tmp_{os.path.basename(out_track_path)}.wav'
                )
                tmp_mp4_track_path = os.path.join(
                    os.path.dirname(out_track_path),
                    f'_tmp_{os.path.basename(out_track_path)}'
                )

                ffmpeg_cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" -ss {track["start_time"]}'
                if track.get('end_time'):
                    ffmpeg_cmd += f' -to {track["end_time"]}'
                ffmpeg_cmd += f' "{tmp_wav_track_path}"'

                mp4als_cmd = f'"{mp4als_path}" -7 -r-1 -MP4 "{tmp_wav_track_path}" "{tmp_mp4_track_path}"'

                async def track_task(f_cmd, m_cmd, metadata, t_path, o_path, idx):
                    async with self.semaphore:
                        print(f'converting to ALS: {self.file_path}, track {idx:02d}')

                        ffmpeg_process = await asyncio.create_subprocess_shell(
                            f_cmd,
                            stderr=asyncio.subprocess.DEVNULL,
                            stdout=asyncio.subprocess.DEVNULL
                        )
                        await ffmpeg_process.communicate()

                        mp4als_process = await asyncio.create_subprocess_shell(
                            m_cmd,
                            stderr=asyncio.subprocess.DEVNULL,
                            stdout=asyncio.subprocess.DEVNULL,
                        )
                        await mp4als_process.communicate()

                        await AudioUtils.add_metadata_by_ffmpeg(metadata, t_path, o_path)
                        os.rename(o_path, os.path.splitext(o_path)[0] + '.m4a')
                        os.remove(t_path)

                sub_worker = asyncio.create_task(
                    track_task(
                        ffmpeg_cmd, mp4als_cmd, track['metadata'], tmp_mp4_track_path, out_track_path, track["idx"]
                    )
                )
                sub_workers_list.append(sub_worker)

        await asyncio.gather(*sub_workers_list)

    def get_ext(self):
        return '.m4a'
