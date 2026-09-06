import asyncio
import unittest
from backend.frame_policy import frame_limits, select_frames, run_frame_fallback

class FramePolicyTests(unittest.TestCase):
    def test_limits_and_temporal_coverage(self):
        self.assertEqual(frame_limits(300), [128,64,32,16,8,4,2,1])
        self.assertEqual(frame_limits(10), [10,8,4,2,1])
        self.assertEqual(select_frames(list(range(128)), 4), [0,42,85,127])

    def test_failure_ladder_stops_on_success(self):
        async def run():
            seen=[]
            async def call(limit):
                seen.append(limit)
                if limit>8: raise ValueError('too many images')
                return 'ok'
            self.assertEqual(await run_frame_fallback(128,call), ('ok',8))
            self.assertEqual(seen,[128,64,32,16,8])
        asyncio.run(run())

    def test_all_fail_and_cancellation_propagate(self):
        async def run():
            seen=[]
            async def fail(limit):
                seen.append(limit);raise ValueError('failure')
            with self.assertRaises(ValueError): await run_frame_fallback(4,fail)
            self.assertEqual(seen,[4,2,1])
            async def cancel(limit): raise asyncio.CancelledError()
            with self.assertRaises(asyncio.CancelledError): await run_frame_fallback(128,cancel)
        asyncio.run(run())
