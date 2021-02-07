# servGallery
servGallery is a simple server for gallery preview on local network.
It's like `python -m http.server`, but photo centered.

![screenshot](screenshot.png "servGallery screenshot")
## Run server
####Example: share current directory
```bash
curl https://raw.githubusercontent.com/engineering4good/servgallery/master/servgallery.py | python3 -
```

####Example: share _'./'_ directory on  _8080_ port.

Single line:
```bash
curl https://raw.githubusercontent.com/engineering4good/servgallery/master/servgallery.py | python3 - --directory="./" 8080
```
or download 'servgallery.py'
```bash
git clone https://github.com/engineering4good/servgallery.git
```
and run
```bash
python3 servgallery/servgallery.py --directory="./" 8080
```
###Usage
servgallery.py [-h] [--directory DIRECTORY] [port]
- port: server port number [default: 8000]
- directory: shared directory path [default:current directory]

## Use as library
servGallery can be imported from your Python code:
```python
from servgallery import run_server

if __name__ == '__main__':
    run_server(8080, 'images_dir/')
```
## Features
- gallery generation 'ON THE FLY' (NO _'index.html'_ file)
- fullscreen photo and video preview
- support preview of bmp, jpg, jpeg, jfif, png, apng, gif, svg, webp, ico, cur, mp4, avi, webm, ogg, mov, mp3, mpeg, wav, aac file types (depends on browser)
- can share other types of files
- support TIFF images preview (when [imread](https://github.com/luispedro/imread) installed)
- support multi-frame images preview (when [imread](https://github.com/luispedro/imread) installed)
- lazy fetching
- single file server (only _'servgallery.py'_ is necessarily)
## Dependencies
- Python 3
- [imread](https://github.com/luispedro/imread) (optional)
## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
## License
[MIT](https://choosealicense.com/licenses/mit/)