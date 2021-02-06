#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
servGallery is a super simple image gallery server.

Run servgallery.py from the top level of an image
directory like a `python -m http.server` on the localhost.

Imported as a module, use servgallery.run_server(port, your_path)
to do the same for any directory programmatically.

Inspired by imageme (https://github.com/unwitting/imageme).
"""

# Dependencies
import argparse
import html
import io
import json
import math
import os
import socketserver
import sys
import tempfile
import urllib
from enum import Enum
from functools import partial
from glob import glob
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler
from urllib.parse import parse_qs
from urllib.parse import urlparse

import numpy as np

IMREAD_ENABLED = False
IMREAD_NOT_ENABLED_MSG = 'WARNING: \'imread\' module not found, so you won\'t get all the ' \
                         'performance you could out of servGallery. Install imread (' \
                         'https://github.com/luispedro/imread) to enable support.'
try:
    import imread
    IMREAD_ENABLED = True
except ImportError:
    print(IMREAD_NOT_ENABLED_MSG)

ICON = b"\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00 \x00h\x04\x00\x00\x16\x00\x00\x00(\x00\x00\x00\x10\x00\x00" \
       b"\x00 \x00\x00\x00\x01\x00 \x00\x00\x00\x00\x00\x00\x04\x00\x00\x13\x0b\x00\x00\x13\x0b\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe7\xd8+\x00\xe7\xd8+\x11\xe7\xd8+;\xe7\xd8+$" \
       b"\xe7\xd8+\r\xe7\xd8,\x02\xe7\xd8,\x00\xe7\xce,\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe7\xd8+\x00\xe7\xd8+^\xe7\xd8+\xe8" \
       b"\xe7\xd8+\xcf\xe7\xd8+\xc0\xe7\xd8+\xa1\xe7\xd8+y\xe7\xd8+R\xe7\xd8+/\xe7\xd8+\x18\xe7\xd8+\x1e\xe7\xd8+5" \
       b"\xe7\xd8+R\xe7\xd8+r\xe7\xd8+S\xe7\xd8+\x02\xe7\xd8+\x00\xe7\xd8+\x8e\xe7\xd8+\xab\xe7\xd8+N\xe7\xd8+\x8a" \
       b"\xe7\xd8+\xd0\xe7\xd8+\xfc\xe7\xd8+\xfd\xe8\xd8+\xed\xe9\xd8*\xd2\xea\xd9(\xcb\xeb\xd9'\xcc\xeb\xd9(\xc0\xe7" \
       b"\xd8+\xcb\xe7\xd8+\xc6\xe7\xd8+\x14\xe7\xd8+\x06\xe7\xd8+\xb2\xe7\xd8+\xe8\xe8\xd8+\xca\xeb\xd9(\xc8\xeb" \
       b"\xd9'\xbe\xe9\xd8*\xad\xe1\xd61\x95\xd0\xd2B\x81\xb2\xca`u\x89\xbf\x89p_\xb5\xb3u>\xac\xd4s\xb4\xca^O\xe8" \
       b"\xd8*\xe6\xe7\xd8+i\xe7\xd8+\x19\xe7\xd8+\xd4\xe8\xd8+\xe6\xc5\xcfM\\`\xb5\xb2rB\xad\xd0\x820\xa8\xe2\x97)" \
       b"\xa7\xe9\xb1'\xa6\xeb\xc8'\xa6\xeb\xdd(\xa6\xea\xee)\xa7\xe8\xfd(\xa6\xea\xd6\x93\xc2\x808\xe8\xd8*\xda\xe7" \
       b"\xd8+j\xe7\xd8+6\xe7\xd8+\xe9\xe8\xd8*\xe6\xa7\xc7k?&\xa6\xec\xa3*\xa7\xe8\xee+\xa7\xe7\xed+\xa7\xe7\xdb+" \
       b"\xa7\xe7\xf8+\xa7\xe7\xff+\xa7\xe7\xff+\xa7\xe7\xff*\xa7\xe8\xb6\xa9\xc8i\x16\xe7\xd8+\xc3\xe7\xd8+a\xe7" \
       b"\xd8+`\xe7\xd8+\xd8\xe7\xd8+\xd9\xe8\xd8*F\x00\x93\xff\t+\xa5\xe7,+\xa2\xe7'+\xa5\xe7\x18+\xa7\xe7\x91+\xa7" \
       b"\xe7\xfe+\xa7\xe7\xf0+\xa7\xe7\x84+\xa7\xe7k\xdd\xd55\x04\xe7\xd8+\xad\xe7\xd8+\x83\xe7\xd8+\x8f\xe7\xd8+" \
       b"\xad\xe7\xd8+\xbb\xe7\xd8+f\xcb\xdaH\x00+\xeb\xe7\x10+\xe8\xe70+\xf3\xe7\x08+\xa5\xe7\x11+\xa7\xe7\xab+\xa7" \
       b"\xe7\xad+\xa7\xe7\n*\xa7\xe8\x07\xf0\xda#\x00\xe7\xd8+\x91\xe7\xd8+\xa8\xe7\xd8+\xbc\xe7\xd8+~\xe7\xd8+\x9b" \
       b"\xe7\xd8+\x86\xb0\xdcb\x00+\xe5\xe7\x85+\xe5\xe7\xf5+\xe5\xe7[+\xd4\xe7\x00+\xa7\xe7\x1c+\xa7\xe7)+\xa7\xe7" \
       b"\x00?\xac\xd3\x00\xe7\xd8+\x00\xe7\xd8+q\xe7\xd8+\xc8\xe7\xd8+\xe1\xe7\xd8+l\xe7\xd8+\x87\xe7\xd8+\xa5\x00" \
       b"\xff\xff\x00+\xe5\xe7e+\xe5\xe7\xca*\xe5\xe8C+\xe5\xe7\x00\x00\x00\x00\x00\x00\x00\x00\x00\xe7\xd8+\x00\xe7" \
       b"\xff(\x00\xe7\xdb,\x00\xe7\xd8+Z\xe7\xd8+\xe2\xe7\xd8+\xcc\xe7\xd8+\xd5\xe7\xd8+\xe4\xe7\xd8+\xbf\xeb\xd8'" \
       b"\n\x00\xe9\xff\x03K\xe3\xc7\x11\xd4\xd8<\x0e\xe8\xd8+\x1d\xe7\xd8+3\xe7\xd8+N\xe7\xd8+n\xe7\xd8+\x8f\xe7" \
       b"\xd8+\xac\xe7\xd8+\xd0\xe7\xd8+\xe8\xe7\xd8+\x15\xe7\xd8+.\xe7\xd8+v\xe7\xd8+\xdb\xe7\xd8+}\xe7\xd8+\x8f\xe8" \
       b"\xd8+\xac\xe7\xd8+\xc4\xe7\xd8+\xde\xe7\xd8+\xf3\xe7\xd8+\xfe\xe7\xd8+\xec\xe7\xd8+\xce\xe7\xd8+\xe6\xe7\xd8" \
       b"+d\xe7\xd8+1\x00\x00\x00\x00\xe7\xd8+\x00\xe7\xd8+\x1d\xe7\xd8+\xaf\xe7\xd8+\xb3\xe7\xd8+\x94\xe7\xd8+t\xe7" \
       b"\xd8+X\xe7\xd8+h\xe7\xd8+\x90\xe7\xd8+\xb6\xe7\xd8+\xcf\xe7\xd8+\xdd\xe7\xd8+\xbe\xe7\xd8,\x0e\xe7\xd8,\x00" \
       b"\x00\x00\x00\x00\xe7\xd7+\x00\xe7\xd7+\x01\xe7\xd8+\t\xe7\xd8,\x05\xe7\xd7-\x00\xe7\xd7,\x00\x00\x00\x00" \
       b"\x00\xe7\xd8+\x00\xe7\xd8+\x00\xe7\xd8+\x06\xe7\xd8,\x18\xe7\xd8+4\xe7\xd8+,\xe7\xd7,\x01\xe7\xd8+\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\x00\x00\x83\xff\x00\x00\x80\x00\x00\x00\x80\x00\x00\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\x04\x00\x00\x08\x9c\x00\x00\x08\xfc\x00\x00\x00" \
       b"\x00\x00\x00\x00\x00\x00\x00\xc0\x01\x00\x00\xc7\xc1\x00\x00\xff\xff\x00\x00"


class MediaTypes(Enum):
    IMAGE = 1
    VIDEO = 2
    AUDIO = 3


MEDIA_EXTENSIONS = {
    'bmp': MediaTypes.IMAGE,
    'jpg': MediaTypes.IMAGE,
    'jpeg': MediaTypes.IMAGE,
    'jfif': MediaTypes.IMAGE,
    'png': MediaTypes.IMAGE,
    'apng': MediaTypes.IMAGE,
    'tif': MediaTypes.IMAGE,
    'tiff': MediaTypes.IMAGE,
    'gif': MediaTypes.IMAGE,
    'svg': MediaTypes.IMAGE,
    'webp': MediaTypes.IMAGE,
    'ico': MediaTypes.IMAGE,
    'cur': MediaTypes.IMAGE,
    'mp4': MediaTypes.VIDEO,
    'avi': MediaTypes.VIDEO,
    'webm': MediaTypes.VIDEO,
    'ogg': MediaTypes.VIDEO,
    'mov': MediaTypes.VIDEO,
    'mp3': MediaTypes.AUDIO,
    'mpeg': MediaTypes.AUDIO,
    'wav': MediaTypes.AUDIO,
    'aac': MediaTypes.AUDIO,
}

PREPROCESSED_MEDIA_TYPES = ['tiff', 'tif']


def _is_media_file(path, media_type=None):
    if not os.path.isfile(path):
        return False
    name_parts = os.path.basename(path).rsplit('.')
    if len(name_parts) > 1:
        if name_parts[-1].lower() in MEDIA_EXTENSIONS.keys():
            if media_type is not None:
                return media_type == MEDIA_EXTENSIONS.get(name_parts[-1].lower())
            return True
    return False


def _get_thumbnail(image_path, min_height, frame_ind):
    frames = imread.imread_multi(image_path)
    if 0 <= frame_ind < len(frames):
        img = frames[frame_ind]
        shape = img.shape
        subsample = math.floor(shape[0] / min_height)
        if len(shape) == 2:
            return img[::subsample, ::subsample]
        elif len(shape) == 3:
            return img[::subsample, ::subsample, :]
    return None


def _ndimage_to_file(ndimage, target_format):
    if ndimage is None:
        return None
    ndimage = np.asarray(ndimage)
    if ndimage.dtype == np.uint16:
        ndimage = ndimage >> 8
    ndimage = ndimage.astype(np.uint8)
    tmp_file = tempfile.NamedTemporaryFile(suffix='.' + target_format)
    try:
        imread.imwrite(tmp_file.name, ndimage)
    except Exception as e:
        print(e)
    return tmp_file


def _get_n_frames(path):
    try:
        frames = imread.imread_multi(path)
        return len(frames)
    except Exception:
        return 1


def _get_preview(path, min_height, frame_ind=0):
    try:
        ext = path.rsplit('.')[-1].lower()
        if (MEDIA_EXTENSIONS.get(ext) == MediaTypes.IMAGE
                and os.path.isfile(path)):
            if ext in PREPROCESSED_MEDIA_TYPES:
                if not IMREAD_ENABLED:
                    print(IMREAD_NOT_ENABLED_MSG)
                    return open(path, 'rb')
                thumbnail = _get_thumbnail(path, min_height, frame_ind)
                target_format = 'jpg'
                return _ndimage_to_file(thumbnail, target_format)
            else:
                return open(path, 'rb')
    except OSError:
        pass
    return None


class RequestHandler(SimpleHTTPRequestHandler):
    def rest_api(self, method, api_args=None):
        if method == 'list_directory':
            path = self.translate_path(api_args.get('dir', os.path.curdir))
            only_files = 'only_files' in api_args and api_args['only_files'] == "yes"
            if os.path.isdir(path):
                try:
                    dir_list = sorted(os.listdir(path))
                    if only_files:
                        dir_list = [name for name in dir_list if os.path.isfile(os.path.join(path, name))]
                    f = io.BytesIO(json.dumps(dir_list).encode('utf-8'))
                    return f
                except OSError:
                    pass
        elif method == 'count_frames':
            path = self.translate_path(api_args.get('image', os.path.curdir))
            if _is_media_file(path, MediaTypes.IMAGE):
                f = io.BytesIO(json.dumps(_get_n_frames(path)).encode('utf-8'))
                return f

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            directory_items = glob(os.path.join(path, '*'))
        except OSError:
            self.send_error(
                HTTPStatus.NOT_FOUND,
                "No permission to list directory")
            return None
        directory_items.sort(key=lambda a: a.lower())
        dirs_list = [el for el in directory_items if os.path.isdir(el)]
        # media_list = [el for el in directory_items if _is_media_file(el)]
        # others_list = [el for el in directory_items if os.path.isfile(el) and el not in media_list]
        r = []
        try:
            display_path = urllib.parse.unquote(self.path,
                                                errors='surrogatepass')
        except UnicodeDecodeError:
            display_path = urllib.parse.unquote(path)
        display_path = html.escape(display_path, quote=False)
        enc = sys.getfilesystemencoding()
        js_global_vars = 'var MEDIA_EXTENSIONS = ' + str({k: MEDIA_EXTENSIONS[k].name for k in MEDIA_EXTENSIONS}) + ';'
        script = \
            js_global_vars + \
            'function getExtension(filename) {' \
            '   let parts = filename.toLowerCase().split(".");' \
            '   parts = parts.reverse();' \
            '   return parts[0];' \
            '};' \
            'function toggleHelp(){' \
            '    console.log("help");' \
            '    document.getElementById("help_display").classList.toggle("hidden");' \
            '}' \
            'function updateCurrentCounter() {' \
            '    let thumbnails = document.getElementsByClassName("thumbnail");' \
            '    let loaded_media_count = thumbnails.length;' \
            '    let pending_media_count = 0;' \
            '    if (window.hasOwnProperty("media_queue")) {' \
            '       pending_media_count = window.media_queue.length;' \
            '    }' \
            '    let total_count = loaded_media_count + pending_media_count;' \
            '    let current_counter = Array.from(thumbnails).indexOf(window.selected_thumbnail);' \
            '    let current_counter_el = document.getElementById("current_counter");' \
            '    if (current_counter >= 0) {' \
            '        current_counter_el.innerText = (current_counter + 1) + "/" + total_count;' \
            '    } else {' \
            '        current_counter_el.innerText = total_count;' \
            '    }' \
            '};' \
            'function init() {' \
            '   fetch("/api/list_directory/?dir=" + location.pathname + "&only_files=yes")' \
            '       .then((r) => { return r.json(); })' \
            '       .then((data) => {' \
            '           window.non_media_list = data.filter(el => {' \
            '               return !(getExtension(el) in MEDIA_EXTENSIONS);' \
            '           });' \
            '           window.media_queue = data.filter(el => {' \
            '               return getExtension(el) in MEDIA_EXTENSIONS;' \
            '           });' \
            '           updateCurrentCounter();' \
            '           initNonMedia();' \
            '           loadMedia();' \
            '       });' \
            '};' \
            'function initNonMedia() {' \
            '   if (window.hasOwnProperty("non_media_list")) {' \
            '       for (let name of window.non_media_list) {' \
            '           appendNonMediaFile(name);' \
            '       }' \
            '   }' \
            '};' \
            'function appendNonMediaFile(name) {' \
            '   li = document.createElement("li");' \
            '   li.classList.add("dir");' \
            '   link = document.createElement("a");' \
            '   link.href = name;' \
            '   link.innerText = name;' \
            '   li.appendChild(link);' \
            '   document.getElementById("non_media_list").appendChild(li);' \
            '};' \
            'function loadMedia() {' \
            '   if (window.hasOwnProperty("media_queue")) {' \
            '       let n = 8;' \
            '       let queue_length = window.media_queue.length;' \
            '       for (let i = 0; i < Math.min(n, queue_length); ++i) {' \
            '           let name = window.media_queue.shift();' \
            '           appendThumbnail(name);' \
            '       }' \
            '   }' \
            '   /* while not enought elements loaded onscroll will not be called */' \
            '   if(document.scrollingElement.scrollHeight <= document.scrollingElement.clientHeight) {' \
            '       setTimeout(loadMedia, 10000);' \
            '   }' \
            '};' \
            'function onImageError(event) {' \
            '   event.srcElement.src= ' \
            '       "data:image/svg+xml;charset=utf-8,"' \
            '       + "<svg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 100 100\' width=\'100\' height=\'100\'>"' \
            '       + "<rect width=\'100\' height=\'100\' fill=\'yellow\' />"' \
            '       + "<g transform=\'translate(7,7)\'>"' \
            '       + "<text x=\'0\' y=\'0\' font-size=\'8\'>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'>Browser can\'t</tspan>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'>display raw image.</tspan>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'>Please install imread</tspan>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'>(<a href=\'https://github.com/luispedro/imread\'>"' \
            '       + "https://github.com/</a></tspan>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'><a href=\'https://github.com/luispedro/imread\'>"' \
            '       + "luispedro/imread</a>).</tspan>"' \
            '       + "<tspan x=\'0\' dy=\'1.2em\'>$ pip install imread</tspan>"' \
            '       + "</text></g></svg>";' \
            '   event.srcElement.onerror = null;' \
            '};' \
            'function appendThumbnail(filename) {' \
            '   let extension = getExtension(filename);' \
            '   let media_type = MEDIA_EXTENSIONS[extension];' \
            '   let link = document.createElement("a");' \
            '   link.href = filename;' \
            '   switch(media_type) {' \
            '       case "IMAGE": {' \
            '           let img = document.createElement("img");' \
            '           img.classList.add("thumbnail_ui_el");' \
            '           img.src = filename + "?act=thumbnail&frame_ind=0";' \
            '           img.alt = "Browser can\'t display raw image. " ' \
            '                     + "Please install imread (https://github.com/luispedro/imread).";' \
            '           img.onerror = onImageError;' \
            '           link.appendChild(img);' \
            '           fetch("/api/count_frames/?image=" + filename)' \
            '               .then(r => {return r.json(); })' \
            '               .then(data => {' \
            '                  let frames_num = data;' \
            '                  for (let i = 1; i < frames_num; ++i) {' \
            '                      img = document.createElement("img");' \
            '                      img.classList.add("thumbnail_ui_el");' \
            '                      img.src = filename + "?act=thumbnail&frame_ind=" + i;' \
            '                      img.alt = filename;' \
            '                      link.appendChild(img);' \
            '                  }' \
            '               });' \
            '           break;' \
            '       }' \
            '       case "VIDEO": {' \
            '           let video = document.createElement("video");' \
            '           video.classList.add("thumbnail_ui_el");' \
            '           video.innerText = "Your browser does not support the video tag.";' \
            '           video.alt = filename;' \
            '           video.controls = "true";' \
            '           video.preload = "metadata";' \
            '           let source = document.createElement("source");' \
            '           source.src = filename;' \
            '           source.media_type = "video/" + extension;' \
            '           video.appendChild(source);' \
            '           link.appendChild(video);' \
            '           break;' \
            '       }' \
            '       case "AUDIO": {' \
            '           let audio = document.createElement("audio");' \
            '           audio.classList.add("thumbnail_ui_el");' \
            '           audio.innerText = "Your browser does not support the audio tag.";' \
            '           audio.alt = filename;' \
            '           audio.controls = "true";' \
            '           audio.preload = "metadata";' \
            '           let source = document.createElement("source");' \
            '           source.src = filename;' \
            '           source.media_type = "audio/" + extension;' \
            '           audio.appendChild(source);' \
            '           link.appendChild(audio);' \
            '           break;' \
            '       }' \
            '   }' \
            '   let li = document.createElement("li");' \
            '   li.classList.add("thumbnail");' \
            '   li.appendChild(link);' \
            '   document.getElementById("media_list").appendChild(li);' \
            '};' \
            'function loadMediaUncomment() {' \
            '    let n = 8;' \
            '    let l = document.getElementsByClassName("thumbnail");' \
            '    let t = document.createElement("template");' \
            '    Array.from(l)' \
            '        .filter(el => el.firstChild.nodeType === 8)' \
            '        .slice(0, n)' \
            '        .forEach(el => { t.innerHTML = el.firstChild.data;' \
            '                         el.firstChild.replaceWith(t.content);' \
            '                        }' \
            '                 );' \
            '    /* while not enought elements loaded onscroll will not be called */' \
            '    if(document.scrollingElement.scrollHeight <= document.scrollingElement.clientHeight) {' \
            '        setTimeout(loadMedia, 10000);' \
            '    }' \
            '};' \
            'function checkEndOfScroll() {' \
            '    if ((window.innerHeight * 1.5 + window.scrollY) >= document.body.offsetHeight) {' \
            '        loadMedia();' \
            '    }' \
            '};' \
            'window.onscroll = function(ev) {' \
            '   checkEndOfScroll();' \
            '};' \
            'window.onload = function() {' \
            '    updateCurrentCounter();' \
            '    init();' \
            '};' \
            'window.onkeydown = function(event) {' \
            '    switch(event.keyCode) {' \
            '        case 39:' \
            '            if (!event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {' \
            '                event.stopPropagation();' \
            '                previewNext();' \
            '                return false;' \
            '            }' \
            '            break;' \
            '        case 37:' \
            '            if (!event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey) {' \
            '                event.stopPropagation();' \
            '                previewPrevious();' \
            '                return false;' \
            '            }' \
            '            break;' \
            '        case 83:' \
            '            saveCurrent();' \
            '            break;' \
            '        case 72:' \
            '        case 27:' \
            '            toggleHelp();' \
            '            break;' \
            '        case 13:' \
            '            let hovered = document.querySelectorAll(".thumbnail:hover");' \
            '            if (hovered.length > 0) {' \
            '                event.stopPropagation();' \
            '                event.preventDefault();' \
            '                preview(hovered[0]);' \
            '            }' \
            '            break;' \
            '        default:' \
            '             console.log(event); /**/' \
            '    }' \
            '};' \
            'function previewNext() {' \
            '    if (typeof window.selected_thumbnail == "undefined") {' \
            '        let thumbnails = document.getElementsByClassName("thumbnail");' \
            '        if (thumbnails.length > 0) {' \
            '            let first = thumbnails[0];' \
            '            window.selected_thumbnail = first;' \
            '            preview(first);' \
            '        }' \
            '    } else {' \
            '        let current = window.selected_thumbnail;' \
            '        preview(current.nextSibling);' \
            '    }' \
            '};' \
            'function previewPrevious() {' \
            '    if (typeof window.selected_thumbnail != "undefined") {' \
            '        let current = window.selected_thumbnail;' \
            '        preview(current.previousSibling);' \
            '    }' \
            '};' \
            'window.onresize = function () {' \
            '    if (typeof window.selected_thumbnail != "undefined") {' \
            '        window.selected_thumbnail.scrollIntoView();' \
            '    }' \
            '};' \
            'function preview(thumbnail) {' \
            '    if (!thumbnail) {' \
            '        return;' \
            '    }' \
            '    if (typeof window.selected_thumbnail != "undefined") {' \
            '        window.selected_thumbnail.classList.remove("preview_thumbnail");' \
            '    }' \
            '    document.activeElement.blur();' \
            '    thumbnail.classList.add("preview_thumbnail");' \
            '    thumbnail.scrollIntoView();' \
            '    window.selected_thumbnail = thumbnail;' \
            '    updateCurrentCounter();' \
            '    let thumbnail_ui_list = thumbnail.getElementsByClassName("thumbnail_ui_el");' \
            '    if (thumbnail_ui_list.length > 0) {' \
            '        thumbnail_ui_list[0].focus();' \
            '    }' \
            '   checkEndOfScroll();' \
            '};' \
            'function saveCurrent() {' \
            '    if (typeof window.selected_thumbnail != "undefined") {' \
            '        save(window.selected_thumbnail);' \
            '    }' \
            '};' \
            'function save(thumbnail) {' \
            '    let links = selected_thumbnail.getElementsByTagName("a");' \
            '    for (let link of links) {' \
            '        link = link.cloneNode();' \
            '        link.onclick = null;' \
            '        let filename = unescape(link.href.split("/").pop()' \
            '                                .split("?")[0].split("#")[0])' \
            '                       .replace(/[\\/\\\\:*?"<>|]/g,"_");' \
            '        link.setAttribute("download", filename);' \
            '        link.click();' \
            '    }' \
            '};' \
            'function handleThumbnailClick(event) {' \
            '    if (!event.ctrlKey) {' \
            '        event.stopPropagation();' \
            '        event.preventDefault();' \
            '        let thumbnail = event.target.closest(".thumbnail");' \
            '        if (thumbnail) {' \
            '            if (thumbnail.classList.contains("preview_thumbnail")) {' \
            '                thumbnail.classList.remove("preview_thumbnail");' \
            '                thumbnail.scrollIntoView();' \
            '            } else {' \
            '                preview(thumbnail);' \
            '            }' \
            '        }' \
            '    }' \
            '};'

        css = \
            '#help_icon {' \
            '   position: fixed;' \
            '   right: 1em;' \
            '   top: 1em;' \
            '}' \
            '.hidden {' \
            '   display: none;' \
            '}' \
            '#help_display {' \
            '   position: fixed;' \
            '   width: 100%;' \
            '   height: 100%;' \
            '   background: #9999;' \
            '   top: 0px;' \
            '   left: 0px;' \
            '   z-index: 1;' \
            '}' \
            '#help_display > div {' \
            '   display: table;' \
            '   margin: 5em auto;' \
            '   background: whitesmoke;' \
            '   padding: 1em;' \
            '   line-height: 2;' \
            '}' \
            '.shortcut {' \
            '   display: flex;' \
            '   align-items: flex-start;' \
            '}' \
            '.shortcut_descr {' \
            '   padding-right: 30px;' \
            '}' \
            '.shortcut_key {' \
            '   align-items: center;' \
            '   justify-content: center;' \
            '   height: 34px;' \
            '   min-width: 34px;' \
            '   box-sizing: border-box;' \
            '   padding-left: 12px;' \
            '   padding-right: 12px;' \
            '   border: 1px solid #e0e3eb;' \
            '   box-shadow: 0 2px 0 #e0e3eb;' \
            '   border-radius: 6px;' \
            '   color: #131722;' \
            '   margin-left: auto;' \
            '}' \
            '.dir {' \
            '   list-style-media_type: none;' \
            '   display: inline-block;' \
            '   margin: 15px;' \
            '}' \
            '#non_media_list {' \
            '   padding-left: 40px;' \
            '}' \
            '#media_list {' \
            '   text-align:center;' \
            '}' \
            '.thumbnail {' \
            '   display: inline-block;' \
            '   vertical-align: top;' \
            '}' \
            '.thumbnail > a {' \
            '   display: flex;' \
            '   height: 300px;' \
            '   margin: 1vh;' \
            '}' \
            '.preview_thumbnail {' \
            '   width: 100%;' \
            '}' \
            '.preview_thumbnail > a {' \
            '   height: 98vh;' \
            '}' \
            '.thumbnail_ui_el {' \
            '   border-radius: 0.5em;' \
            '   height: 100%;' \
            '   width: 100%;' \
            '   object-fit: contain;' \
            '   background-color: ghostwhite;' \
            '}' \
            '#current_counter {' \
            '   position: fixed;' \
            '   bottom: 0px;' \
            '   right: 0px;' \
            '   background-color: white;' \
            '}'

        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>' % display_path)
        r.append('<style>%s</style>' % css)
        r.append('<script>%s</script>' % script)
        r.append('\n</head><body>\n')
        help_icon = \
            '<a id="help_icon" title="display help" href="javascript:toggleHelp();">' \
            '  <svg viewBox="0 0 22 22" height="2em" width="2em">' \
            '    <circle cx="50%" cy="50%" r="9" stroke="#777" stroke-width="2" fill="transparent" />' \
            '    <text x="50%" y="57%" font-size="16" dominant-baseline="middle" text-anchor="middle" fill="#777">' \
            '      ?</text>' \
            '    Sorry, your browser does not support inline SVG.' \
            '  </svg>' \
            '</a>'
        r.append(help_icon)
        help_display = \
            '<div id="help_display" class="hidden" onclick="toggleHelp()">' \
            '  <div>' \
            '   <h1>Usage</h1>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Next item</span>' \
            '       <span class="shortcut_key" title="right arrow">→</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Previous item</span>' \
            '       <span class="shortcut_key" title="left arrow">←</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Play/pause video</span>' \
            '       <span class="shortcut_key">space</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Open original in new tab</span>' \
            '       <span class="shortcut_key">Ctrl</span> + <span class="shortcut_key">click</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Preview multiple-frame image</span>' \
            '       <span class="shortcut_key">Ctrl</span> + <span class="shortcut_key" title="right arrow">→</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Download current item</span>' \
            '       <span class="shortcut_key">s</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Preview item under cursor</span>' \
            '       <span class="shortcut_key">Enter</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Display/hide help message</span>' \
            '       <span class="shortcut_key">Esc</span>' \
            '   </div>' \
            '   <div class="shortcut">' \
            '       <span class="shortcut_descr">Display/hide help message</span>' \
            '       <span class="shortcut_key">h</span>' \
            '   </div>' \
            '  </div>' \
            '</div>'
        r.append(help_display)
        r.append('<h1>Directory listing for %s</h1>' % display_path)
        r.append('<hr>\n<div id="dirs"><ul>')
        dirs_list.insert(0, "..")
        for fullname in dirs_list:
            name = os.path.basename(fullname)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li class="dir"><a href="%s">%s</a></li>'
                     % (urllib.parse.quote(linkname,
                                           errors='surrogatepass'),
                        html.escape(displayname, quote=False)))
        r.append('</ul></div>\n<hr>\n')

        r.append('<div id="non_media_list"></div>\n')

        r.append('<div onclick="handleThumbnailClick(event)"><ul id="media_list"></ul></div>\n')

        r.append('<p id="current_counter"></p>')
        r.append('</body>\n</html>\n')
        encoded = ''.join(r).encode(enc, 'surrogateescape')
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-media_type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def send_head(self):
        url = urlparse(self.path)
        params = parse_qs(url.query)

        def _get_param_value(name, default, data_type=None):
            param_arr = params.get(name, [])
            if len(param_arr) == 0:
                param = default
            else:
                param = param_arr[0]
            if data_type is not None:
                param = data_type(param)
            return param

        if 'act' in params and len(params['act']) > 0 and params['act'][0] == 'thumbnail':
            min_height = _get_param_value('min_height', 600, int)
            frame_ind = _get_param_value('frame_ind', -1, int)

            path = self.translate_path(self.path)

            f = _get_preview(path, min_height, frame_ind)
            if f is not None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-media_type", "image")
                self.end_headers()
                return f
            else:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                return f
        elif self.path == "/favicon.ico":
            f = io.BytesIO()
            f.write(ICON)
            f.seek(0)
            return f
        elif url.path.startswith('/api/'):
            url_parts = url.path.split('/')
            if len(url_parts) >= 3:
                method = url_parts[2]
                api_args = {n: _get_param_value(n, '') for n in params}
                return self.rest_api(method=method, api_args=api_args)
        return super().send_head()


def run_server(port, dir_path):
    """
    Run the image server. This is blocking. Will handle user KeyboardInterrupt
    and other exceptions appropriately and return control once the server is
    stopped.

    @param {Integer} port - The port number to serve on
    @param {String} dir_path - The directory path (absolute, or relative to CWD)

    @return {None}
    """
    # Configure allow_reuse_address to make re-runs of the script less painful -
    # if this is not True then waiting for the address to be freed after the
    # last run can block a subsequent run
    socketserver.TCPServer.allow_reuse_address = True
    # Create the server instance
    server = socketserver.ThreadingTCPServer(
        ('', port),
        partial(RequestHandler, directory=dir_path)
    )

    print('Your images are at http://127.0.0.1:%d/' % port)
    print('In case you want access server from remote client check firewall rules.')
    # Try to run the server
    try:
        # Run it - this call blocks until the server is killed
        server.serve_forever()
    except KeyboardInterrupt:
        # This is the expected way of the server being killed, since servGallery is
        # intended for ad-hoc running from command line
        print('User interrupted, stopping')
    except Exception as err:
        # Catch everything else - this will handle shutdowns via other signals
        # and faults actually starting the server in the first place
        print(err)
        print('Unhandled exception in server, stopping')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run server with media preview from directory.')
    parser.add_argument('--directory', '-d', default=os.getcwd(),
                        help='Specify alternative directory '
                             '[default:current directory]')
    parser.add_argument('port', action='store',
                        default=8000, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    args = parser.parse_args()

    run_server(args.port, os.path.expanduser(args.directory))
