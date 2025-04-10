from flask import Flask, request, jsonify, send_file
from pytube import YouTube
import os
from io import BytesIO

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    data = request.get_json()
    url = data.get('url')
    
    try:
        yt = YouTube(url)
        video_info = {
            'title': yt.title,
            'thumbnail': yt.thumbnail_url,
            'formats': []
        }

        # Filter for progressive (video+audio) and audio-only formats
        formats = []
        for stream in yt.streams.filter(progressive=True):
            formats.append({
                'itag': stream.itag,
                'mimeType': stream.mime_type,
                'qualityLabel': stream.resolution,
                'fileSize': format_file_size(stream.filesize)
            })

        # Add adaptive formats (video only or audio only)
        for stream in yt.streams.filter(adaptive=True):
            if stream.type == 'video':
                quality = f"{stream.resolution} (video only)"
            else:
                quality = f"{stream.abr} (audio only)"
            
            formats.append({
                'itag': stream.itag,
                'mimeType': stream.mime_type,
                'qualityLabel': quality,
                'fileSize': format_file_size(stream.filesize)
            })

        # Add audio-only formats
        audio_stream = yt.streams.get_audio_only()
        if audio_stream:
            formats.append({
                'itag': audio_stream.itag,
                'mimeType': audio_stream.mime_type,
                'qualityLabel': f"Audio Only ({audio_stream.abr})",
                'fileSize': format_file_size(audio_stream.filesize)
            })

        video_info['formats'] = formats
        return jsonify(video_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    itag = request.args.get('itag')
    
    try:
        yt = YouTube(url)
        stream = yt.streams.get_by_itag(itag)
        
        buffer = BytesIO()
        stream.stream_to_buffer(buffer)
        buffer.seek(0)
        
        filename = f"{yt.title}.{stream.subtype}"
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype=stream.mime_type
        )
    except Exception as e:
        return str(e), 400

def format_file_size(bytes):
    if bytes is None:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

if __name__ == '__main__':
    app.run(debug=True)
