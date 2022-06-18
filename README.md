# PyAlbumCondense

A simple tool to compress and condense your album collections

## Introduction

PyAlbumCondense is simple python script that will convert your album to either lossy or lossless format concurrently 
while preserving its original directory structure and metadata.

### Lossy Album Condense

* lossless audio file will be converted to the specified lossy format
* lossy audio file will be copied to the destination folder
* integrate audio tracks will be converted into seperated tracks according to the cue file
* lossless images (such as scans in png format) will be converted to the specified lossy format
* lossy images (such as scans in jpg format) will be copied to the destination folder
* video will be copied to the destination folder
* all other files will be discarded

### Lossless Album Condense

* lossless audio file will be converted to the specified lossless format
* lossless images (such as scans in bmp format) will be converted to the specified lossless format
* integrate tracks will remain intact while its associated cue file will be modified to accommodate the new format
* all other files will be copied to the destination folder

## Usage

### Command Line

```
python album_condense.py [-h] [-n WORKER_NUM] src_path dst_path
python album_condense_lossless.py [-h] [-n WORKER_NUM] src_path dst_path
```

* -h: print this help
* -n: concurrent workers num

### Config File

see config.json which includes all available parameters.

### Formats and Encoders

#### Lossy Formats

Audio Formats:

| format |     detail     | encoder |    remark    |
|:------:|:--------------:|:-------:|:------------:|
|  opus  |  Xiph's Opus   | ffmpeg  |   default    |
|  aac   |   MPEG-4 AAC   |  qaac   ||
|  usac  |  MPEG-D USAC   | exhale  | experimental |
| vorbis | Xiph's Vorbis  | ffmpeg  ||
|  mp3   | MPEG-1 Layer 3 | ffmpeg  ||

Image Formats:

| format |     detail     | encoder |    remark    |
|:------:|:--------------:|:-------:|:------------:|
|  webp  | Google's WebP  | ffmpeg  |   default    |
|  jpeg  |      JPEG      | ffmpeg  ||

#### Lossless Formats

Audio Formats:

| format  |             detail              | encoder  |         remark          |
|:-------:|:-------------------------------:|:--------:|:-----------------------:|
|  flac   |           Xiph's FLAC           |  ffmpeg  |         default         |
|  alac   |          Apple's ALAC           |   qaac   ||
|   tak   | Tom's lossless Audio Kompressor |   takc   ||
|   als   |           MPEG-4 ALS            | mp4alsRM | experimental, very slow |
|   tta   |            TrueAudio            |  ffmpeg  ||
| wavpack |             WavPack             |  ffmpeg  ||

Image Formats:

| format  |             detail              | encoder  |         remark          |
|:-------:|:-------------------------------:|:--------:|:-----------------------:|
|   png   |    Portable Network Graphics    |  ffmpeg  |         default         |
|  webp   |  Google's WebP, Lossless Mode   |  ffmpeg  ||

## Dependencies

### Python Packages

* chardet (optional)

### External Binaries

* [ffmpeg](https://ffmpeg.org/download.html)
* [exhale](https://gitlab.com/ecodis/exhale/-/releases)
* [qaac](https://github.com/nu774/qaac/releases/) and Apple's CoreAudio
* [takc](http://www.thbeck.de/Tak/Tak.html)
* mp4alsRM
