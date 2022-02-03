"""Handles the rendering of libtcod's tilesets.

Using this module you can render a console to an SDL :any:`Texture` directly, letting you have full control over how
conoles are displayed.
This includes rendering multiple tilesets in a single frame and rendering consoles on top of each other.

Example::

    tileset = tcod.tileset.load_tilsheet("dejavu16x16_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)
    console = tcod.Console(20, 8)
    console.print(0, 0, "Hello World")
    sdl_window = tcod.sdl.video.new_window(
        console.width * tileset.tile_width,
        console.height * tileset.tile_height,
        flags=tcod.lib.SDL_WINDOW_RESIZABLE,
    )
    sdl_renderer = tcod.sdl.render.new_renderer(sdl_window, target_textures=True)
    atlas = tcod.render.SDLTilesetAtlas(sdl_renderer, tileset)
    console_render = tcod.render.SDLConsoleRender(atlas)
    while True:
        sdl_renderer.copy(console_render.render(console))
        sdl_renderer.present()
        for event in tcod.event.wait():
            if isinstance(event, tcod.event.Quit):
                raise SystemExit()

.. versionadded:: 13.4
"""

from __future__ import annotations

from typing import Optional

import tcod.console
import tcod.sdl.render
import tcod.tileset
from tcod._internal import _check, _check_p
from tcod.loader import ffi, lib


class SDLTilesetAtlas:
    """Prepares a tileset for rendering using SDL."""

    def __init__(self, renderer: tcod.sdl.render.Renderer, tileset: tcod.tileset.Tileset) -> None:
        self._renderer = renderer
        self.tileset = tileset
        self.p = ffi.gc(_check_p(lib.TCOD_sdl2_atlas_new(renderer.p, tileset._tileset_p)), lib.TCOD_sdl2_atlas_delete)


class SDLConsoleRender:
    """Holds an internal cache console and texture which are used to optimized console rendering."""

    def __init__(self, atlas: SDLTilesetAtlas) -> None:
        self._atlas = atlas
        self._renderer = atlas._renderer
        self._cache_console: Optional[tcod.console.Console] = None
        self._texture: Optional[tcod.sdl.render.Texture] = None

    def render(self, console: tcod.console.Console) -> tcod.sdl.render.Texture:
        """Render a console to a cached Texture and then return the Texture.

        You should not draw onto the returned Texture as only changed parts of it will be updated on the next call.

        This function requires the SDL renderer to have target texture support.
        It will also change the SDL target texture for the duration of the call.
        """
        if self._cache_console and (
            self._cache_console.width != console.width or self._cache_console.height != console.height
        ):
            self._cache_console = None
            self._texture = None
        if self._cache_console is None or self._texture is None:
            self._cache_console = tcod.console.Console(console.width, console.height)
            self._texture = self._renderer.new_texture(
                self._atlas.tileset.tile_width * console.width,
                self._atlas.tileset.tile_height * console.height,
                format=int(lib.SDL_PIXELFORMAT_RGBA32),
                access=int(lib.SDL_TEXTUREACCESS_TARGET),
            )

        with self._renderer.set_render_target(self._texture):
            _check(
                lib.TCOD_sdl2_render_texture(
                    self._atlas.p, console.console_c, self._cache_console.console_c, self._texture.p
                )
            )
        return self._texture
