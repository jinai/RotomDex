import argparse
import datetime
import enum
import json
import os
import re

from discord.ext import commands

import pokemon
import urlmarker


def get_data(filename):
    with open(os.path.join("data", filename), "r", encoding="utf-8") as f:
        return json.load(f)


def extract_urls(text):
    return re.findall(urlmarker.URL_REGEX, text)


def get_filename_from_url(url):
    if url.find('/'):
        return url.rsplit('/', 1)[1]


def get_timestamp(*, fmt="%H:%M:%S", wrap=lambda ts: f"[{ts}]"):
    return wrap(datetime.datetime.now().strftime(fmt))


class CategoryConverter(commands.Converter):
    async def convert(self, ctx, argument):
        if argument.isdigit():
            return pokemon.Category(int(argument))
        else:
            return pokemon.Category[argument.title()]


class BaseEnum(enum.Enum):
    @classmethod
    def names(cls):
        return [x.name for x in cls]

    @classmethod
    def values(cls):
        return [x.value for x in cls]

    def to_dict(self):
        return {"name": self.name, "value": self.value}


class OrderedEnum(BaseEnum):
    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented

    def __gt__(self, other):
        if self.__class__ is other.__class__:
            return self.value > other.value
        return NotImplemented

    def __le__(self, other):
        if self.__class__ is other.__class__:
            return self.value <= other.value
        return NotImplemented

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)
