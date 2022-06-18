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
import argparse

from common.action import audio_convert, image_convert, file_copy


async def dispatcher(src_path, dst_path, worker_num):
    ext_handler = {
        'wav': audio_convert,
        'flac': audio_convert,
        'aiff': audio_convert,
        'ape': audio_convert,
        'tak': audio_convert,
        'tta': audio_convert,
        'wv': audio_convert,
        'alac': audio_convert,

        'png': image_convert,
        'tiff': image_convert,
        'tif': image_convert,
        'bmp': image_convert,

        'jpg': file_copy,
        'jpeg': file_copy,
        'jp2': file_copy,
        'webp': file_copy,
        'heif': file_copy,
        'heic': file_copy,

        'mp3': file_copy,
        'm4a': file_copy,
        'aac': file_copy,
        'ogg': file_copy,
        'opus': file_copy,

        'mkv': file_copy,
        'avi': file_copy,
        'mp4': file_copy,
    }

    semaphore = asyncio.Semaphore(worker_num)
    workers_list = []

    for path, _, file_names in os.walk(src_path):
        for file_name in file_names:
            ext = os.path.splitext(file_name)[1].strip('.')
            handler = ext_handler.get(ext)
            if handler is not None:
                worker = asyncio.create_task(handler(semaphore, os.path.join(path, file_name), src_path, dst_path))
                workers_list.append(worker)
            await asyncio.sleep(0)

    await asyncio.gather(*workers_list)

    print('all done !')


def main():
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-n', '--worker_num', default=4, type=int)
    args_parser.add_argument('src_path')
    args_parser.add_argument('dst_path')
    args = args_parser.parse_args()
    asyncio.run(dispatcher(args.src_path, args.dst_path, args.worker_num))


if __name__ == '__main__':
    main()
