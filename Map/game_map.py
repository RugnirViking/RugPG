import numpy
import numpy as np  # type: ignore
import tcod
from tcod import console
from tcod.console import Console

from Map import tile_types
import colorsys
import random


def scale_lightness(rgb, scale_l):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(l, l * scale_l), s=s)


def scale_saturation(rgb, scale_s):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, l, min(s, s * scale_s))


def scale_lightness_saturation(rgb, scale_l, scale_s):
    # convert rgb to hls
    h, l, s = colorsys.rgb_to_hls(*rgb)
    # manipulate h, l, s values and return as rgb
    return colorsys.hls_to_rgb(h, min(l, l * scale_l), min(s, s * scale_s))


class GameMap:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")
        self.visible = np.full((width, height), fill_value=False, order="F")  # Tiles the player can currently see
        self.explored = np.full((width, height), fill_value=False, order="F")  # Tiles the player has seen before

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console, playerx, playery) -> None:
        """
                Renders the map.

                If a tile is in the "visible" array, then draw it with the "light" colors.
                If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
                Otherwise, the default is "SHROUD".
                """
        tilestorender = np.select(
            condlist=[self.visible, self.explored],
            choicelist=[self.tiles["light"], self.tiles["dark"]],
            default=tile_types.SHROUD
        )
        cost = numpy.ones((self.width, self.height), dtype=numpy.int8)
        dist = numpy.zeros((self.width, self.height), dtype=numpy.int8)
        """To add more light sources we can add more of the below line. For now its just the player. 
            We add a random offset to simulate flickering light"""
        dist[playerx, playery] = -16 + random.uniform(-1.5, 1.5)
        for x in range(self.width):
            for y in range(self.height):
                cost[x, y] = 1 if self.tiles["transparent"][x][y] else 2

        """ Lighting baking """
        tcod.path.dijkstra2d(dist, cost, 2, diagonal=3)
        max_dist = 10000
        lum = 0.5
        for j in range(tilestorender.shape[1]):
            for i in range(tilestorender.shape[0]):
                tile = tilestorender[i, j];
                if self.visible[i, j]:
                    """ For visible tiles we calculate the lighting """
                    fg_t = tile[1]
                    bg_t = tile[2]
                    distn = int(dist[i, j])

                    num = distn
                    # tile[0]=num+48
                    if distn > max_dist:
                        distn = max_dist
                    ##bg_t[0] = max(min(tile[2][0] / 255 - 1 * lum + (distn / -max_dist) * lum), 0) * 255
                    #bg_t[1] = min(255,bg_t[1]*((distn / -32.0) * 0.2)*255.0)/4+bg_t[0]*3/4
                    print((distn / -max_dist) * lum)
                    h, l, s = colorsys.rgb_to_hls(fg_t[0] / 255, fg_t[1] / 255, fg_t[2] / 255)
                    random.seed(i + j)
                    r, g, b = colorsys.hls_to_rgb(h, max(min(1, l - 1 * lum + (distn / -max_dist) * lum), 0), s)
                    if (distn > max_dist):
                        print("oh")
                    tile[1] = [r * 255, g * 255, b * 255]
                    h2, l2, s2 = colorsys.rgb_to_hls(bg_t[0] / 255, bg_t[1] / 255, bg_t[2] / 255)
                    r2, g2, b2 = colorsys.hls_to_rgb(h2, max(min(1, l2 - 1 * lum + (distn / -max_dist) * lum), 0), s2)
                    tile[2] = [r2 * 255, g2 * 255, b2 * 255]
                    tile[2][0] = min(255,tile[2][0]*((distn / -16.0) * 0.4)*255.0)/8+tile[2][0]*7/8
                    tile[2][1] = min(255,tile[2][1]*((distn / -16.0) * 0.4)*255.0)/16+tile[2][1]*15/16

        console.tiles_rgb[0:self.width, 0:self.height] = tilestorender
        """
                we want to make things look spooky
                """
