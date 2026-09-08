from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from astrbot.api.message_components import Image
from astrbot_plugin_meme_manager.mixins.event_handlers import EventHandlerMixin


@pytest.mark.asyncio
async def test_qq_meme_uses_original_event_and_retains_unknown_delivery(tmp_path):
    path = tmp_path / "prepared.gif"
    path.write_bytes(b"fixture")
    image = Image.fromFileSystem(str(path))
    event = SimpleNamespace(get_platform_name=lambda: "aiocqhttp",
                            send=AsyncMock(side_effect=RuntimeError("delivery unknown")))
    plugin = SimpleNamespace(_ensure_image_send_format=AsyncMock(side_effect=lambda value: value),
                             context=SimpleNamespace(send_message=AsyncMock()))
    plugin._send_meme_image = lambda current, value: EventHandlerMixin._send_meme_image(plugin, current, value)
    prepared = {"images": [image], "temp_files": [str(path)]}
    with pytest.raises(RuntimeError):
        await EventHandlerMixin.compat_send_prepared_message(plugin, event, prepared, send_text=False)
    assert path.is_file()
    plugin.context.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_qq_meme_cleans_temporary_asset_only_after_acknowledgement(tmp_path):
    path = tmp_path / "prepared.gif"
    path.write_bytes(b"fixture")
    image = Image.fromFileSystem(str(path))
    event = SimpleNamespace(get_platform_name=lambda: "aiocqhttp", send=AsyncMock(),
                            _runtime_v2_last_delivery_receipt={"status": "acknowledged"})
    plugin = SimpleNamespace(_ensure_image_send_format=AsyncMock(side_effect=lambda value: value))
    plugin._send_meme_image = lambda current, value: EventHandlerMixin._send_meme_image(plugin, current, value)
    result = await EventHandlerMixin.compat_send_prepared_message(plugin, event, {"images": [image], "temp_files": [str(path)]}, send_text=False)
    assert result["sent_images_count"] == 1
    assert not path.exists()


@pytest.mark.asyncio
async def test_text_only_phase_keeps_deferred_images(tmp_path):
    path = tmp_path / "deferred.gif"
    path.write_bytes(b"fixture")
    event = SimpleNamespace(send=AsyncMock())
    prepared = {"images": [Image.fromFileSystem(str(path))], "temp_files": [str(path)]}
    await EventHandlerMixin.compat_send_prepared_message(SimpleNamespace(), event, prepared, send_images=False)
    assert path.exists()
