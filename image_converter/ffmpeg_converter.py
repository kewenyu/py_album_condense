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
import asyncio

from image_converter.image_converter import ImageConverter
from common.config import config
from common.util import PathUtils


class FFMPEGImageConverter(ImageConverter, metaclass=abc.ABCMeta):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    async def convert(self):
        async with self.semaphore:
            print(f'converting to {self._get_format_name()}: {self.file_path}')

            new_file_path = PathUtils.create_file_path_struct(
                self.file_path, self.src_path, self.dst_path, self._get_ext()
            )
            ffmpeg_path = config.get('executable', {}).get('ffmpeg', 'ffmpeg')
            cmd = f'"{ffmpeg_path}" -y -i "{self.file_path}" {self._get_parameter()} "{new_file_path}"'

            process = await asyncio.create_subprocess_shell(cmd, stderr=asyncio.subprocess.DEVNULL)
            await process.communicate()

    @abc.abstractmethod
    def _get_ext(self):
        raise NotImplemented

    @abc.abstractmethod
    def _get_format_name(self):
        raise NotImplemented

    @abc.abstractmethod
    def _get_parameter(self):
        raise NotImplemented


class WebpConverter(FFMPEGImageConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.webp'

    def _get_format_name(self):
        return 'WebP'

    def _get_parameter(self):
        quality = config.get('webp_config', {}).get('quality', 78)
        return f'-quality {quality}'


class JPEGConverter(FFMPEGImageConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.jpg'

    def _get_format_name(self):
        return 'JPEG'

    def _get_parameter(self):
        qscale = config.get('jpeg_config', {}).get('qscale', 2)
        return f'-qscale {qscale}'


class WebpLosslessConverter(FFMPEGImageConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.webp'

    def _get_format_name(self):
        return 'WebP'

    def _get_parameter(self):
        return f'-lossless 1'


class PNGConverter(FFMPEGImageConverter):
    def __init__(self, semaphore, file_path, src_path, dst_path):
        super().__init__(semaphore, file_path, src_path, dst_path)

    def _get_ext(self):
        return '.png'

    def _get_format_name(self):
        return 'PNG'

    def _get_parameter(self):
        compression_level = config.get('png_config', {}).get('compression_level', 100)
        return f'-compression_level {compression_level}'
