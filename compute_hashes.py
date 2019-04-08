import json
import os
import time

import imagehash
from PIL import Image

import rotomdex
import utils


def compute_hashes(*, source_dir, output_dir=None, output_name="dhash.json"):
    start_time = time.perf_counter()
    source_dir = os.path.normpath(source_dir)
    if output_dir is None:
        output_dir = os.path.join(source_dir, '..')
    output_dir = os.path.normpath(output_dir)
    output_path = os.path.join(output_dir, output_name)

    hashes = {}
    pokedex = utils.get_data("pokedex.json")
    success = 0
    alola = 0
    fail = 0

    for filename in sorted(os.listdir(source_dir)):
        if not filename.lower().endswith(".png"):
            continue
        path = os.path.join(source_dir, filename)
        padding = len(source_dir) + 24
        print(f"{path:{padding}} >", end=" ", flush=True)
        try:
            image = rotomdex._prepare_image(Image.open(path))
            hash = imagehash.dhash(image)
            pokemon = pokedex[str(int(filename[:3]))]
            if "alola" in filename.lower():
                pokemon = f"Alolan {pokemon}"
                alola += 1
            hashes[str(hash)] = pokemon
            print(f"{hash} {filename[:3]} {pokemon}")
            success += 1
        except IOError as e:
            print(e)
            fail += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=4, ensure_ascii=False)

    elapsed_time = time.perf_counter() - start_time
    print(
        f"\nHashed {success}/{success + fail} ({success - alola} + {alola} alolan) artworks to '{output_path}' in {elapsed_time:0.02f} seconds.")


if __name__ == '__main__':
    src = os.path.join("data", "art")
    compute_hashes(source_dir=src)
