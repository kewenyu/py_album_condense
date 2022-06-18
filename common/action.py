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

from common.config import config
from common.util import PathUtils
from cue.cue_loader import CueFileLoader

from audio_converter.ffmpeg_converter import MP3Converter, OpusConverter, VorbisConverter
from audio_converter.qaac_converter import AACConverter
from audio_converter.exhale_converter import ExhaleConverter
from image_converter.ffmpeg_converter import WebpConverter, JPEGConverter

from audio_converter.ffmpeg_converter import FLACConverter, TrueAudioConverter, WavPackConverter
from audio_converter.qaac_converter import ALACConverter
from audio_converter.tak_converter import TakConverter
from audio_converter.mp4als_converter import ALSConverter
from image_converter.ffmpeg_converter import PNGConverter, WebpLosslessConverter


async def audio_convert(semaphore, file_path, src_path, dst_path):
    audio_codec_handlers = {
        'opus': OpusConverter,
        'aac': AACConverter,
        'usac': ExhaleConverter,
        'vorbis': VorbisConverter,
        'mp3': MP3Converter,
    }

    target_audio_codec = config.get('audio_codec', 'opus')
    audio_codec_handler = audio_codec_handlers.get(target_audio_codec)(semaphore, file_path, src_path, dst_path)

    cue_path = os.path.splitext(file_path)[0] + '.cue'
    if os.path.exists(cue_path):
        await audio_codec_handler.cue_convert()
    else:
        await audio_codec_handler.single_convert()


async def image_convert(semaphore, file_path, src_path, dst_path):
    image_codec_handlers = {
        'webp': WebpConverter,
        'jpeg': JPEGConverter,
    }

    target_image_codec = config.get('scan_format', 'webp')
    image_codec_handler = image_codec_handlers.get(target_image_codec)(semaphore, file_path, src_path, dst_path)
    await image_codec_handler.convert()


async def audio_convert_lossless(semaphore, file_path, src_path, dst_path):
    audio_codec_handlers = {
        'flac': FLACConverter,
        'alac': ALACConverter,
        'tak': TakConverter,
        'wavpack': WavPackConverter,
        'tta': TrueAudioConverter,
        'als': ALSConverter,
    }

    target_audio_codec = config.get('lossless_audio_codec', 'flac')
    audio_codec_handler = audio_codec_handlers.get(target_audio_codec)(semaphore, file_path, src_path, dst_path)
    await audio_codec_handler.single_convert()

    file_path_str, ext = os.path.splitext(file_path)
    cue_path = file_path_str + '.cue'
    if os.path.exists(cue_path):
        lines = CueFileLoader(cue_path).get_content()
        lines = [line.replace(ext, audio_codec_handler.get_ext()) for line in lines]

        dst_cue_path = PathUtils.create_file_path_struct(cue_path, src_path, dst_path, '.cue')
        with open(dst_cue_path, 'w', encoding='utf-8-sig') as cue:
            cue.writelines(lines)


async def image_convert_lossless(semaphore, file_path, src_path, dst_path):
    image_codec_handlers = {
        'webp': WebpLosslessConverter,
        'png': PNGConverter,
    }

    target_image_codec = config.get('lossless_scan_format', 'png')
    image_codec_handler = image_codec_handlers.get(target_image_codec)(semaphore, file_path, src_path, dst_path)
    await image_codec_handler.convert()


async def file_copy(semaphore, file_path, src_path, dst_path):
    new_file_path = os.path.join(dst_path, os.path.relpath(file_path, src_path))

    if os.name == 'nt':
        cmd = f'copy /Y "{file_path}" "{new_file_path}"'
    else:
        cmd = f'cp -f "{file_path}" "{new_file_path}"'

    async with semaphore:
        print(f'copying: {file_path}')

        if not os.path.exists((dir_path := os.path.dirname(new_file_path))):
            os.makedirs(dir_path)

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await process.communicate()
