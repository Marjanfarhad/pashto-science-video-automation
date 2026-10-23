from pathlib import Path
import asyncio, json, math, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'video-pilot-output'
OUT.mkdir(exist_ok=True)
FF=imageio_ffmpeg.get_ffmpeg_exe()
SCRIPT=''
SCENES=[]

def frame(i,title,lines,kind):
    im=Image.new('RGB',(1080,1920)); d=ImageDraw.Draw(im)
    for y in range(1920):
        t=y/1920; d.line((0,y,1080,y),fill=(int(9+8*t),int(26+24*t),int(55+35*t)))
    d.rounded_rectangle((70,90,1010,105),radius=7,fill='#45d9e8')
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',30)
    d.text((80,145),'SCIENCE / PS',font=font,fill='#8eaeca')
    if kind=='spectrum':
        d.ellipse((400,640,680,920),fill='#fff3c0')
        for j,c in enumerate(['#f88383','#ffb765','#ffe28c','#83e3a7','#63b8ff','#b0a1f9']):
            d.line((220,990+j*32,860,990+j*32),fill=c,width=22)
    elif kind in ('scatter','eye'):
        for j in range(15):
            x=240+(j%5)*150; y=700+(j//5)*150
            d.ellipse((x-10,y-10,x+10,y+10),fill='#b1d3e2')
        d.line((110,850,970,850),fill='#ff9c8c',width=7)
        for a in range(0,360,45):
            r=math.radians(a)
            d.line((540,850,540+330*math.cos(r),850+330*math.sin(r)),fill='#69beff',width=9)
        if kind=='eye':
            d.ellipse((390,1120,690,1240),outline='#d6edff',width=8)
            d.ellipse((502,1140,578,1220),fill='#69beff')
    else:
        d.rounded_rectangle((130,630,950,1140),radius=55,fill='#2472b8')
        d.ellipse((690,690,825,825),fill='#fff0b0')
        for x,y in [(270,900),(330,875),(390,905),(620,1020),(680,990),(745,1020)]:
            d.ellipse((x-75,y-45,x+75,y+45),fill='#dcefff')
    d.text((80,1770),'Science explainer',font=font,fill='#9cb7cf')
    d.text((925,1770),f'{i+1}/5',font=font,fill='#45d9e8')
    im.save(OUT/f'scene-{i+1}.png')

def run(args):
    p=subprocess.run(args,capture_output=True,text=True)
    if p.returncode: raise RuntimeError(p.stderr[-2000:])
    return p

async def audio():
    import edge_tts
    await edge_tts.Communicate(SCRIPT,'ps-AF-GulNawazNeural').save(str(OUT/'narration.mp3'))

def main():
    if '--frames-only' in sys.argv:
        for i,s in enumerate(SCENES): frame(i,*s)
        return
    probe=run([FF,'-i',str(OUT/'narration.mp3'),'-f','null','-'])
    m=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',probe.stderr)
    if not m: raise RuntimeError('Cannot measure narration')
    duration=int(m[1])*3600+int(m[2])*60+float(m[3]); factor=duration/52
    if not 0.67<=factor<=1.5: raise RuntimeError('Narration needs editing before rendering')
    for i in range(5):
        run([FF,'-y','-loop','1','-i',str(OUT/f'scene-{i+1}.png'),'-t','10.4','-r','24','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p',str(OUT/f'clip-{i+1}.mp4')])
    listing=OUT/'clips.txt'
    listing.write_text('\n'.join("file 'clip-"+str(i+1)+".mp4'" for i in range(5)),encoding='utf-8')
    run([FF,'-y','-f','concat','-safe','0','-i',str(listing),'-i',str(OUT/'narration.mp3'),'-filter:a',f'atempo={factor:.6f}','-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-t','52','-movflags','+faststart',str(OUT/'pashto-science-pilot.mp4')])
    (OUT/'run-result.json').write_text(json.dumps({'state':'ReadyForReview','width':1080,'height':1920,'target_duration_seconds':52,'narration_original_seconds':duration,'published':False,'limitations':['Scene summaries, not word-synchronized subtitles.','Native speaker review required.']},indent=2),encoding='utf-8')
