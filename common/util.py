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


class PathUtils:
    @staticmethod
    def create_dir_path_struct(file_path, src_path, dst_path):
        file_dir = os.path.dirname(file_path)
        new_file_dir = os.path.join(
            dst_path,
            os.path.relpath(file_dir, src_path),
            os.path.splitext(os.path.basename(file_path))[0]
        )
        if not os.path.exists(new_file_dir):
            os.makedirs(new_file_dir)
        return new_file_dir

    @staticmethod
    def create_file_path_struct(file_path, src_path, dst_path, ext):
        new_file_name = os.path.splitext(file_path)[0] + ext
        new_file_path = os.path.join(dst_path, os.path.relpath(new_file_name, src_path))
        if not os.path.exists((dir_path := os.path.dirname(new_file_path))):
            os.makedirs(dir_path)
        return new_file_path
