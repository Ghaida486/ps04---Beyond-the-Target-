"""Local CPU Whisper inference with timestamped segments and workspace-local weights."""
import sys
from pathlib import Path
import json

def main():
    if len(sys.argv) not in (4,5): return 2
    from faster_whisper import WhisperModel, BatchedInferencePipeline
    audio,output,name=sys.argv[1:4]
    task=sys.argv[4] if len(sys.argv)==5 else "transcribe"
    if task not in ("transcribe","translate"): return 2
    root=Path(__file__).resolve().parents[1]
    model=WhisperModel(name,device='cpu',compute_type='int8',download_root=str(root/'data/models'))
    engine=BatchedInferencePipeline(model=model)
    segments,info=engine.transcribe(audio,beam_size=5,batch_size=4,vad_filter=True,task=task)
    result=[{'segment_id':str(i+1),'start_seconds':s.start,'end_seconds':s.end,'text':s.text.strip()} for i,s in enumerate(segments) if s.text.strip()]
    Path(output).with_suffix('.metadata.json').write_text(json.dumps({'provider':'faster-whisper-local','model':name,'task':task,'detected_language':info.language,'language_probability':info.language_probability,'output_language':'en' if task=='translate' else info.language,'translation_requires_original_audio_review':task=='translate'},indent=2)+'\n')
    Path(output).write_text(json.dumps(result,indent=2)+'\n')
    return 0
if __name__=='__main__': sys.exit(main())
