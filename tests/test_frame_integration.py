import asyncio
from PIL import Image
from backend import semantic_caption as caption

def test_real_gif_cap_and_caption_degradation(tmp_path, monkeypatch):
    path=tmp_path/'sample.gif'
    frames=[Image.new('RGB',(8,8),(i,0,0)) for i in range(140)]
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=30)
    paths,temporary=caption.prepare_visual_inputs(path)
    try:
        assert len(paths)==128
    finally:
        from pathlib import Path
        for p in temporary:Path(p).unlink()
    seen=[]
    async def once(*args, _max_frames, **kwargs):
        seen.append(_max_frames)
        if _max_frames>8:raise ValueError('request too large')
        return {'caption':'ok'}
    monkeypatch.setattr(caption,'_generate_caption_once',once)
    result=asyncio.run(caption.generate_caption(object(),path,'test'))
    assert result['sampled_frames']==8
    assert seen==[128,64,32,16,8]
