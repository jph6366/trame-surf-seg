from surf_seg.app.core import MyTrameApp
import pytest

async def test_app():
    app = MyTrameApp()
    await app.server.start()
    assert app.state.trame__title == "surf-seg"