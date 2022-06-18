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

class CueFileLoader:
    def __init__(self, cue_path):
        self.lines = ''
        self.cue_path = cue_path
        self._load_cue_content()

    def get_content(self):
        return self.lines

    def _load_cue_content(self):
        encodings = [
            'utf-8-sig',
            'utf-8',
            'shift-jis',
            'gb2312',
            'gbk',
        ]

        try:
            import chardet
            with open(self.cue_path, 'rb') as cue_file:
                guessed_charset = chardet.detect(cue_file.read())
                if (guessed_encoding := guessed_charset.get('encoding')) is not None:
                    encodings.insert(0, guessed_encoding)
        except ModuleNotFoundError:
            pass

        for encoding in encodings:
            try:
                with open(self.cue_path, encoding=encoding) as cue_file:
                    self.lines = cue_file.readlines()
                    break
            except UnicodeDecodeError:
                continue
        else:
            raise RuntimeError(f'failed to decode cue file {self.cue_path}')
