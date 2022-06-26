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

import re


class CueContentParser:
    def __init__(self, file_name, content):
        self.content = content
        self.state = 'global'
        self.global_metadata = {
            'title': file_name,
        }
        self.tracks = []
        self._parse_cue_file()

    def get_tracks(self):
        return self.tracks

    def _parse_cue_file(self):
        matchers = {
            'rem': re.compile(r'\s*REM\s+(.+?)\s+(.+)'),
            'performer': re.compile(r'\s*PERFORMER\s+(.+)'),
            'title': re.compile(r'\s*TITLE\s+(.+)'),
            'songwriter': re.compile(r'\s*SONGWRITER\s+(.+)'),
            'file': re.compile(r'\s*FILE.+'),
            'catalog': re.compile(r'\s*CATALOG\s+(.+)'),
            'isrc': re.compile(r'\s*ISRC\s+(.+)'),
            'track': re.compile(r'\s*TRACK\s+(\d+?)\s+.+'),
            'index': re.compile(r'\s*INDEX\s+(\d+?)\s+(.+)'),
        }

        for line in self.content:
            for match, regex in matchers.items():
                if (group := regex.match(line)) is not None:
                    handler = getattr(self, f'_{self.state}_{match}', None)
                    if handler is None:
                        raise RuntimeError(f'failed to parse cue file: no handler _{self.state}_{match}')
                    else:
                        handler(group)
                        break

    def _global_rem(self, group):
        self.global_metadata[group.group(1).strip().strip('"').lower()] = group.group(2).strip().strip('"')

    def _global_file(self, _):
        self.state = 'track'

    def _global_catalog(self, group):
        self.global_metadata['catalog'] = group.group(1).strip().strip('"')

    def _global_performer(self, group):
        self.global_metadata['performer'] = group.group(1).strip().strip('"')

    def _global_songwriter(self, group):
        self.global_metadata['songwriter'] = group.group(1).strip().strip('"')

    def _global_title(self, group):
        self.global_metadata['album'] = group.group(1).strip().strip('"')

    def _track_performer(self, group):
        self.tracks[-1].setdefault('metadata', {})['performer'] = group.group(1).strip().strip('"')

    def _track_title(self, group):
        illegal_chars = r'\/:*?"<>|'
        title = group.group(1).strip().strip('"')
        for c in illegal_chars:
            title = title.replace(c, '_')
        self.tracks[-1]['title'] = title
        self.tracks[-1].setdefault('metadata', {})['title'] = group.group(1).strip().strip('"')

    def _track_songwriter(self, group):
        self.tracks[-1].setdefault('metadata', {})['songwriter'] = group.group(1).strip().strip('"')

    def _track_isrc(self, group):
        self.tracks[-1].setdefault('metadata', {})['isrc'] = group.group(1).strip().strip('"')

    def _track_rem(self, group):
        self.tracks[-1].setdefault('metadata', {})[group.group(1).strip().strip('"').lower()] = group.group(
            2).strip().strip('"')

    def _track_track(self, group):
        idx = int(group.group(1))
        self.tracks.append({
            'idx': idx,
            'start_time': '',
            'end_time': '',
            'metadata': self.global_metadata.copy(),
        })
        self.tracks[-1]['metadata']['track'] = idx
        self.tracks[-1]['metadata']['title'] = f"{self.tracks[-1]['metadata']['title']} {idx:02d}"
        self.tracks[-1]['title'] = self.tracks[-1]['metadata']['title']

        if (track_idx := int(group.group(1))) != (track_num := len(self.tracks)):
            raise RuntimeError(f'inconsistent track number: track_idx: {track_idx}, track_nums: {track_num}')

    def _track_index(self, group):
        if group.group(1) != '01':
            return

        minute, second, frame = [int(t) for t in group.group(2).split(':')]
        timestamp = f'{minute // 60}:{minute % 60:02d}:{second:02d}.{int(frame * (1 / 75) * 1000):03d}'

        self.tracks[-1]['start_time'] = timestamp
        if len(self.tracks) > 1:
            self.tracks[-2]['end_time'] = timestamp
