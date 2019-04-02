import io
import json
from collections import namedtuple
from operator import itemgetter

import imagehash
import requests
from PIL import Image

from pokemon import Pokemon

_hashes_path = "data/dhash.json"
_hashes = {}
Match = namedtuple("Match", "pokemon score")


def set_hashes(path):
    global _hashes
    with open(path, "r", encoding="utf-8") as f:
        _hashes = {imagehash.hex_to_hash(key): value for key, value in json.load(f).items()}


def identify(arg, exact_only=False):
    if isinstance(arg, str):
        image = _download_image(arg)
    elif isinstance(arg, Image.Image):
        image = _prepare_image(arg)
    else:
        return
    image_hash = imagehash.dhash(image)
    result = {
        "best_match": None,
        "rankings": []
    }
    if image_hash in _hashes:
        result["best_match"] = Match(pokemon=Pokemon.from_name(_hashes[image_hash]), score=0)
    elif not exact_only:
        rankings = [(pokemon_name, image_hash - hash) for hash, pokemon_name in _hashes.items()]
        rankings.sort(key=itemgetter(1))
        name, score = rankings[0]
        result["best_match"] = Match(pokemon=Pokemon.from_name(name), score=score)
        result["rankings"] = rankings
    return result


def _prepare_image(image):
    image = _crop_image(image)
    return _apply_background(image)


def _apply_background(image, color=(255, 255, 255)):
    """ Source: https://stackoverflow.com/a/33507138/10203343 """
    background = Image.new(mode='RGBA', size=image.size, color=color)
    alpha_composite = Image.alpha_composite(background, image)
    return alpha_composite


def _crop_image(image):
    """ Source: https://stackoverflow.com/a/53829086/10203343 """
    black = Image.new(mode='RGBA', size=image.size)
    image = Image.composite(image, black, image)
    return image.crop(image.getbbox())


def _download_image(url):
    r = requests.get(url)
    if r.status_code == 200:
        return Image.open(io.BytesIO(r.content))


set_hashes(_hashes_path)

if __name__ == '__main__':
    import os

    header = "Test case                      | Best match    | Score (lower is better, 0 = exact match)"
    line__ = "-------------------------------+---------------+-----------------------------------------"
    print(f"\n{header}\n{line__}")
    target = os.path.join("data", "test")
    for filename in os.listdir(target):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            print(f"{filename:<30}", end=" | ")
            path = os.path.join(target, filename)
            image = _prepare_image(Image.open(path).convert("RGBA"))
            r = identify(image)
            m = r["best_match"]
            score = f"[{m.score}]" if m.score > 0 else f" {m.score}"
            print(f"{m.pokemon!s:<13} | {score}")
