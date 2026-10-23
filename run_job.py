from pathlib import Path
import importlib.util, os, re, sys, json, subprocess, asyncio
ROOT=Path(__file__).resolve().parent

def load_job(job_id):
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}',job_id): raise ValueError('Invalid job ID')
    data=json.loads((ROOT/'jobs'/(job_id+'.json')).read_text(encoding='utf-8'))
    if data.get('status')!='ApprovedForProduction': raise ValueError('Job not approved')
    if not isinstance(data.get('script'),str) or not 50<=len(data['script'])<=5000: raise ValueError('Invalid script')
    if not data.get('source_url','').startswith('https://'): raise ValueError('Evidence URL required')
    if len(data.get('scenes',[]))!=5: raise ValueError('Five scenes required')
    for scene in data['scenes']:
        if len(scene)!=3 or scene[2] not in {'sky','spectrum','scatter','eye'}: raise ValueError('Invalid scene')
        if not isinstance(scene[0],str) or not isinstance(scene[1],list) or not 1<=len(scene[1])<=2: raise ValueError('Invalid captions')
        if any(not isinstance(x,str) or len(x)>90 for x in [scene[0],*scene[1]]): raise ValueError('Caption too long')
    return data

def run(job_id):
    data=load_job(job_id)
    spec=importlib.util.spec_from_file_location('renderer',ROOT/'renderer.py')
    renderer=importlib.util.module_from_spec(spec); spec.loader.exec_module(renderer)
    renderer.SCRIPT=data['script']; renderer.SCENES=data['scenes']
    renderer.OUT=ROOT/'video-pilot-output'; renderer.OUT.mkdir(exist_ok=True)
    if (renderer.OUT/'pashto-science-pilot.mp4').exists(): raise RuntimeError('Existing output; use fresh workspace')
    sys.argv=['renderer','--frames-only','--native-text']; renderer.main()
    scene_path=renderer.OUT/'scene-data.json'
    scene_path.write_text(json.dumps([{'Title':s[0],'Lines':s[1]} for s in data['scenes']],ensure_ascii=False),encoding='utf-8')
    subprocess.run(['pwsh','-NoProfile','-File',str(ROOT/'render_pashto_text.ps1'),'-SceneDataPath',str(scene_path)],check=True)
    asyncio.run(asyncio.wait_for(renderer.audio(),timeout=180))
    sys.argv=['renderer','--render-existing']; renderer.main()
    video=renderer.OUT/'pashto-science-pilot.mp4'
    subprocess.run([renderer.FF,'-v','error','-i',str(video),'-f','null','-'],check=True)
    p=renderer.OUT/'run-result.json'; result=json.loads(p.read_text(encoding='utf-8'))
    result.update(job_id=job_id,source=data['source_url'],published=False,state='ReadyForReview')
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ReadyForReview; TikTok not connected.')
if __name__=='__main__': run(os.environ.get('JOB_ID','pilot-001'))
