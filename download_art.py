import os
import time

import requests
from requests.utils import quote

import utils


def get_urls():
    start = time.perf_counter()
    pokedex = utils.get_data("pokedex.json")
    urls = []
    success = 0
    fail = 0
    alola = 0
    for i in range(1, len(pokedex) + 1):
        pokemon = pokedex[str(i)]
        print_prefix = f"{str(i).zfill(3)} {pokemon}"
        pokemon = quote(pokemon)
        if i == 29:
            pokemon += "♀"
        elif i == 32:
            pokemon += "♂"
        api_url = f"https://bulbapedia.bulbagarden.net/w/api.php?action=parse&format=json&page={pokemon}_(Pokémon)"
        r = requests.get(api_url)
        if r.status_code == 200:
            lst = utils.extract_urls(r.text)
            if lst:
                url = lst[2]
                image_url = "https://" + url[:url.rfind("/")].replace("/thumb/", "/")
                urls.append(image_url)
                print(f"{print_prefix:<20} > {image_url}")
                success += 1

                for url in lst:
                    if pokemon.replace(" ", "_") + "-Alola" in url:
                        image_url = "https://" + url[:url.rfind("/")].replace("/thumb/", "/")
                        urls.append(image_url)
                        print_prefix += "-alola"
                        print(f"{print_prefix:<20} > {image_url}")
                        alola += 1
                        break
            else:
                print(f"{print_prefix:<20} > Could not find a URL")
                fail += 1
        else:
            print(f"{print_prefix:<20} > {r.status_code} {r.reason}")
            fail += 1
    elapsed_time = time.perf_counter() - start
    print(
        f"\nFound {success + alola}/{success + fail + alola} ({success} + {alola}) URLs in {elapsed_time:0.02f} seconds.\n")
    return urls


def download_art(*, urls, target_dir):
    start = time.clock()
    target_dir = os.path.normpath(target_dir)
    try:
        os.makedirs(target_dir)
        print(f"Created directory : '{target_dir}'")
    except OSError:
        pass
    success = 0
    fail = 0
    for url in urls:
        url = url.strip()
        print(f"{url:<64}", end=" ", flush=True)
        r = requests.get(url)
        if r.status_code == 200:
            path = os.path.join(target_dir, utils.get_filename_from_url(url))
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"{r.status_code} {r.reason}  > {path}")
            success += 1
        else:
            print(f"{r.status_code} {r.reason}")
            fail += 1
    exec_time = time.clock() - start
    print(f"\nDownloaded {success}/{success + fail} artworks to '{target_dir}' in {exec_time:0.02f} seconds.\n")


if __name__ == '__main__':
    urls = get_urls()
    path = os.path.join("data", "bulbagarden_urls.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(urls))
    target = os.path.join("data", "art2")
    download_art(urls=urls, target_dir=target)
