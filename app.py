#!/bin/env python3 -u
import string
import functools
import logging
import traceback
import sys
import keen
from flask import Flask, Blueprint, current_app, jsonify, request, redirect, abort , render_template , Response 
import os
import subprocess

#import youtube_dl
#from youtube_dl.version import __version__ as youtube_dl_version
# export KEEN_PROJECT_ID=61d32c19ab0d2a7bed25cc19 
#        export KEEN_MASTER_KEY=298E7321CF8B88E3963DC24D15E57305671E33CEA9EE67F1A83486B91C1A8E94 
#        export KEEN_WRITE_KEY=9d48a02eb2345f78203f44acf4dd125eb399d9da23950da725c4e85e071898a7b4476bdf37590153947278deddcf5448001413570a77521b6ee7bc9f1cfcb3cffccc732021e2503dbc40924726154a70490a1d667a667f6e7f42ba1c10ebf3b5 
#        export KEEN_READ_KEY=fda51f112a6666c38c39ee2c69337c7916e67aac2e954a3832981cf30b876e37a8bbad1d5c41912daf6cdcdf0f372705b84f40ba439e1888bfc1a90cad8815e2a0d7ad7bbc884d601bc2129c5a118dcbf0b9196549267deb89c25eb661302bb2 
keen.project_id = "5eef2174a3bca1362c746f4f"
keen.write_key = "94773595c8b58bb1d74763d2b6b1494797e4375e3f67a404c4d213b0446249e7cc365aef4c1f99cca4afc41ccece857d3c519a997b0588ce8758972da63e3427096eaa5870102c08c7bba844aa42f7daf9aaf53da9ad429d95c75aaaf98c3bdd"
keen.read_key = "393804892345abdd3becf711f0edba58deccc5668d7aa359336333051c221bd1fccf14a341472b57f9f14e765eee4a5efd93ad05072082578585d69ffc4191e184785b57a485fbc1801bbd0a97f6f5b355d0274a869a084d2fce7cca645e7c2f"

#"fda51f112a6666c38c39ee2c69337c7916e67aac2e954a3832981cf30b876e37a8bbad1d5c41912daf6cdcdf0f372705b84f40ba439e1888bfc1a90cad8815e2a0d7ad7bbc884d601bc2129c5a118dcbf0b9196549267deb89c25eb661302bb2"


import yt_dlp as youtube_dl 
from yt_dlp import YoutubeDL
from yt_dlp.version import __version__ as youtube_dl_version

from .version import __version__

p = ""

if not hasattr(sys.stderr, 'isatty'):
    # In GAE it's not defined and we must monkeypatch
    sys.stderr.isatty = lambda: False


class SimpleYDL(youtube_dl.YoutubeDL):
    def __init__(self, *args, **kargs):
        super(SimpleYDL, self).__init__(*args, **kargs)
        self.add_default_info_extractors()


def get_videos(url, extra_params):
    '''
    Get a list with a dict for every video founded
    '''
    ydl_params = {
        'username': "b0hal", 
        'password': "yeah12ha" , 
#        'add-metadata': True,
#        'embed-thumbnail': True,
        'sublang': "deDE",
        'subslang': "de-DE",
        'extractorargs': "crunchyroll:language=jaJp,hardsub=deDE",
        'flatplaylist': True,
#        'format': 'b[language=ger]+b[language=jap]/bv[ext=mp4]',
        'flatvideos': True,
        'cleaninfojson': True,
        'cachedir': False,
        'logger': current_app.logger.getChild('yt_dlp'),
    }
#        'format': 'bv[height=1080][ext=m4v]+ba[ext=m4a]/22/bv[height=480][ext=m4v]+ba[ext=m4a]/18/best[ext=mp4]/b[language=ger]+b[language=jap]/b[language=jap]/bv*+ba/b',

#        'netrc': True,
#    ydl_params = {
#        'format': 'best',
#        'cachedir': False,
#        'logger': current_app.logger.getChild('yt_dlp'),
#    }

    ydl_params.update(extra_params)
    ydl = SimpleYDL(ydl_params)
    res = ydl.extract_info(url, download=False)
    return res

def flatten_result_orig(result):
    r_type = result.get('_type', 'video')
    if r_type == 'video':
        videos = [result]
    elif r_type == 'playlist':
        videos = []
        for entry in result['entries']:
            videos.extend(flatten_result(entry))
    elif r_type == 'compat_list':
        videos = []
        for r in result['entries']:
            videos.extend(flatten_result(r))
    return videos

def flatten_result(result):
    r_type = result.get('_type', 'video')
    if r_type == 'video':
        videos = [result]
    elif r_type == 'playlist':
        videos = []
        for entry in result['entries']:
            entry["formats"] = []
            videos.extend(flatten_result(r))
#            videos.extend(flatten_result(entry))
    elif r_type == 'compat_list':
        videos = []
        for r in result['entries']:
            r["formats"] = []
            videos.extend(flatten_result(r))
    return videos


api = Blueprint('api', __name__)


def route_api(subpath, *args, **kargs):
    return api.route('/api/' + subpath, *args, **kargs)


def set_access_control(f):
    @functools.wraps(f)
    def wrapper(*args, **kargs):
        response = f(*args, **kargs)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    return wrapper


@api.errorhandler(youtube_dl.utils.DownloadError)
@api.errorhandler(youtube_dl.utils.ExtractorError)
def handle_youtube_dl_error(error):
    logging.error(traceback.format_exc())
    result = jsonify({'error': str(error)})
    result.status_code = 500
    return result


class WrongParameterTypeError(ValueError):
    def __init__(self, value, type, parameter):
        message = '"{}" expects a {}, got "{}"'.format(parameter, type, value)
        super(WrongParameterTypeError, self).__init__(message)


@api.errorhandler(WrongParameterTypeError)
def handle_wrong_parameter(error):
    logging.error(traceback.format_exc())
    result = jsonify({'error': str(error)})
    result.status_code = 400
    return result


@api.before_request
def block_on_user_agent():
    user_agent = request.user_agent.string
    forbidden_uas = current_app.config.get('FORBIDDEN_USER_AGENTS', [])
    if user_agent in forbidden_uas:
        abort(429)


def query_bool(value, name, default=None):
    if value is None:
        return default
    value = value.lower()
    if value == 'true':
        return True
    elif value == 'false':
        return False
    else:
        raise WrongParameterTypeError(value, 'bool', name)


ALLOWED_EXTRA_PARAMS = {
#    'format': str,
    'playliststart': int,
    'playlistend': int,
    'playlist_items': str,
    'playlistreverse': bool,
    'matchtitle': str,
    'username': str,
    'password': str,
    'rejecttitle': str,
    'language': str,
    'matchfilters': str,
    'writesubtitles': bool,
    'flatplaylist': bool,
    'extractorargs': str,
    'flatvideos': bool,
    'writeautomaticsub': bool,
    'allsubtitles': bool,
    'subtitlesformat': str,
    'minfilesize': str,
    'subtitleslangs': list,
}



def get_result():
    url = request.args['url']
    extra_params = {}
    for k, v in request.args.items():
        if k in ALLOWED_EXTRA_PARAMS:
            convertf = ALLOWED_EXTRA_PARAMS[k]
            if convertf == bool:
                convertf = lambda x: query_bool(x, k)
            elif convertf == list:
                convertf = lambda x: x.split(',')
            extra_params[k] = convertf(v)
    return get_videos(url, extra_params)


@route_api('info')
@set_access_control
def info():
    url = request.args['url']
    result = get_result()
    tresult = result
    key = 'info'
    extractor = 'generic'
    if query_bool(request.args.get('flatten'), 'flatten', False):
        tresult = flatten_result(result)
    else:
        tresult = flatten_result(result)
        extractor = tresult[0]['extractor'] 
        fresult = tresult[0]['formats'][-1]
        tresult[0]['formats'] = fresult 
        key = 'videos'
    result = {
        'orig_url': url,
        'url': "https://ytdl-api.forward.pw/api/play?url=" + url,
        'key': tresult,
        'keen': {
          'addons': [{
      	   'name': 'keen:url_parser',
      	   'input': {
         	'url': 'url'
      	   },
      	   'output': 'parsed_url'}]
	  }
    }
#    keen.add_event("ytapi", result)
    keen.add_event(extractor, result)
    return jsonify(result)

@route_api('play')
def play():
    result = flatten_result_orig(get_result())
    
#    result = get_result()
    return redirect(result[0]['url'])


#@route_api('play')
#def play():
#    result = flatten_result(get_result())
#    tresult = flatten_result(get_result())
#    fresult = tresult[0]['formats'][-1]
#tresult[0]['formats'][-1]
#    return redirect(fresult)


#@route_api('dl')
#def dl():
    #result = flatten_result(get_result())
    #cmd = 'ffmpeg -c:v h264 -i "'+result[0]['url']+'" - -movflags frag_keyframe+empty_moov -vf scale=640:-1 -f mp4 -'
    #p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    #return Response(p.stdout, mimetype='video/mp4'

@route_api('extractors')
@set_access_control
def list_extractors():
    ie_list = [{
        'name': ie.IE_NAME,
        'working': ie.working(),
    } for ie in youtube_dl.gen_extractors()]
    return jsonify(extractors=ie_list)


@route_api('version')
@set_access_control
def version():
    result = {
        'youtube-dl': youtube_dl_version,
        'youtube-dl-api-server': __version__,
    }
    return jsonify(result)


app = Flask(__name__)
app.register_blueprint(api)
app.config.from_pyfile('../application.cfg', silent=True)
app._static_folder = '/static'
app.template_folder = '/templates'
#p = subprocess.Popen('echo test ', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

#@app.route('/')
#def index():
    #url = request.args['url']
    #return render_template('index.html')
    #cmd = 'ffmpeg -c:v h264 -i - -movflags frag_keyframe+empty_moov -vf scale=640:-1 -f mp4 -'
    #p = subprocess.Popen('echo '+ url + ' | ' + cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

@app.route('/video.mp4')
def video_stream():
    url = request.args['url']
#    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    def generate():
        cmd = 'ffmpeg -c:v h264 -i ' + url +' -movflags frag_keyframe+empty_moov -vf scale=640:-1 -f mp4 -'
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)       
        for data in iter(p.stdout.readline, b''):
            yield data
    return Response(generate(), mimetype='video/mp4')

#@app.route('/video.mp4')
#def video_stream():
    #url = request.args['url']
    #def generate():
        #cmd = 'echo ffmpeg -c:v h264 -i ' + url +' -movflags frag_keyframe+empty_moov -vf scale=640:-1 -f mp4 -'
        #p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)       
        #for data in iter(p.stdout.readline, b''):
            #yield data
    #return Response(generate(), mimetype='video/mp4')



if __name__ == '__main__':
    app.run()
