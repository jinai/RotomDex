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


def load_hashes(path):
    global _hashes
    with open(path, "r", encoding="utf-8") as f:
        _hashes = {imagehash.hex_to_hash(key): value for key, value in json.load(f).items()}


def identify(*, im=None, url=None, exact_only=False):
    if im:
        image = _prepare_image(im)
    elif url:
        image = _prepare_image(_download_image(url))
    else:
        raise ValueError

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


def _prepare_image(im, bg_color=(0, 0, 0, 0)):
    """ Source: https://stackoverflow.com/a/53829086/10203343 """
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    background = Image.new(mode="RGBA", size=im.size, color=bg_color)
    composite = Image.composite(im, background, im)
    return composite.crop(composite.getbbox())


def _download_image(url):
    r = requests.get(url)
    if r.status_code == 200:
        return Image.open(io.BytesIO(r.content))


load_hashes(_hashes_path)

if __name__ == '__main__':
    import time
    import os

    start = time.perf_counter()
    print("Test case                      | Best match       | Score* | Result")
    print("-------------------------------+------------------+--------+-------")
    target = os.path.join("data", "test")
    for filename in os.listdir(target):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            image = Image.open(os.path.join(target, filename))
            r = identify(im=image)
            m = r["best_match"]
            score = f"[{m.score}]" if m.score > 0 else f" {m.score}"
            result = "✔" if m.pokemon.name.lower().replace(":", "") in filename.lower() else "Fail"
            print(f"{filename:<30} | {m.pokemon!s:<16} | {score:<6} | {result}")
    print("*Lower is better. A zero means an exact match (same hash).")
    print(f"\nExecuted tests in {time.perf_counter() - start} seconds.")
