from flask import Flask, request, send_file, after_this_request
import os
from uuid import uuid4
import sys
from gtts import gTTS
import shutil
import io

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = f'{BASE_DIR}/output'
ffmpeg = 'ffmpeg' if sys.platform == 'win32' else './ffmpeg'
# standard_params = '-hide_banner -loglevel error -stats -v quiet -y'
standard_params = ''
max_length = 250
max_image_size = 5 * 1024 * 1024 # 5MB
speed = 1.4

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    try:
        uuid = uuid4()
        current_dir = f'{OUTPUT_DIR}/{uuid}'
        os.makedirs(current_dir)
        if not 'image' in request.files: return 'Image not found', 400
        image_file = request.files['image']
        if not 'text' in request.form: return 'Text not found', 400

        text = request.form['text']
        if len(text) > max_length: return 'Text too long', 400
        srt_file = f"{current_dir}/{uuid}.srt"
        with open(srt_file, "w") as f: f.write(f"1\n00:00:00,000 --> 00:00:30,000\n{text}")

        image_path = f'{current_dir}/{uuid}.png'
        image_file.save(image_path)
        output_image_file = f'{current_dir}/{uuid}_cropped.png'

        os.system(f"""{ffmpeg} {standard_params} -i {image_path} -filter_complex "[0:v]crop=in_h*0.5625:in_h,scale=720x1280[out]" -map "[out]" -preset ultrafast {output_image_file}""")
        

        tts = gTTS(text=text, lang='en', tld='us')
        audio_file = f'{current_dir}/{uuid}.mp3'
        output_audio_file = f'{current_dir}/{uuid}_output.mp3'
        tts.save(audio_file)
        os.system(f"""{ffmpeg} {standard_params} -i {audio_file} -filter:a "atempo={speed}" -c:a libmp3lame -preset ultrafast "{output_audio_file}" """)
        

        video_file = f'{current_dir}/{uuid}.mp4'
        srt_file = srt_file.replace("\\", "/\\").replace(":", "\\\\:")
        os.system(f"""{ffmpeg} {standard_params} -loop 1 -i "{output_image_file}" -i "{output_audio_file}" -filter_complex "[0:v]subtitles={srt_file}:force_style='FontSize=16,PrimaryColour=&Hffffff,Alignment=10'[out]" -map "[out]" -map 1:a -c:v libx264 -c:a copy -shortest -fflags shortest -max_interleave_delta 100M -tune stillimage -preset ultrafast -pix_fmt yuv420p {video_file}""")
        
        return_data = io.BytesIO()
        with open(video_file, 'rb') as f: return_data.write(f.read())
        return_data.seek(0)
        shutil.rmtree(current_dir)
        return send_file(return_data, mimetype='video/mp4', as_attachment=True, download_name=f'{uuid}.mp4')

    except Exception as e:
        print(e)
        return 'Error', 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')
