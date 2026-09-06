"""Bounded, cancellation-safe animation degradation."""
import asyncio
import logging

FRAME_LIMITS = (128, 64, 32, 16, 8, 4, 2, 1)

def frame_limits(count):
    count = max(1, min(128, int(count)))
    return [count] + [n for n in FRAME_LIMITS if n < count]

def select_frames(paths, limit):
    if len(paths) <= limit:
        return list(paths)
    if limit == 1:
        return [paths[0]]
    return [paths[round(i * (len(paths)-1)/(limit-1))] for i in range(limit)]

def image_frame_count(source):
    from PIL import Image
    try:
        with Image.open(source) as image:
            return max(1, int(getattr(image, 'n_frames', 1)))
    except Exception:
        return 128

async def run_frame_fallback(count, call):
    limits = frame_limits(count)
    for limit in limits:
        try:
            if len(limits) == 1:
                return await call(limit), limit
            async with asyncio.timeout(60):
                return await call(limit), limit
        except Exception as exc:
            logging.getLogger(__name__).warning('Animation attempt failed; frames=%s error=%s', limit, type(exc).__name__)
            if limit == limits[-1]:
                raise
