import os
import shlex

import crayons
import discord
from discord.ext import commands
from discord.utils import oauth_url

import pokemon
import rotomdex
import utils

bot = commands.Bot(command_prefix='_', case_insensitive=True)
bot.owner_id = 92469090249089024
pokecord_id = 365975655608745985
spawn_text = "A wild pokémon has appeared!"
alert_channels = {}
alert_servers = set()
identify_channels = {}
identify_servers = set()


def owner_or_has_permissions(**perms):
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        permissions = ctx.channel.permissions_for(ctx.author)
        missing = [perm for perm, value in perms.items() if getattr(permissions, perm, None) != value]
        if not missing:
            return True
        raise commands.MissingPermissions(missing)

    return commands.check(predicate)


@bot.before_invoke
async def log_command(ctx):
    if ctx.invoked_subcommand:
        return
    ts = crayons.white(utils.get_timestamp(), bold=True)
    msg = crayons.green(ctx.message.content.replace(ctx.prefix, "", 1), bold=True)
    chan = crayons.magenta(f"#{ctx.channel}", bold=True)
    guild = crayons.magenta(f"({ctx.guild})")
    user = crayons.yellow(f"{ctx.author}", bold=True)
    print(f"{ts} {msg!s} in {chan} {guild} by {user}")


def log_pokemon(match, message):
    p = match.pokemon
    ts = crayons.white(utils.get_timestamp(), bold=True)
    cat = crayons.cyan(p.category, bold=True)
    name = crayons.green(str(p))
    score = crayons.red(f"[{match.score}]", bold=True)
    chan = crayons.magenta(f"#{message.channel}", bold=True)
    guild = crayons.magenta(f"({message.guild})")
    print(f"{ts} {cat} {name} {score} (#{str(p.id).zfill(3)} {p.generation}) in {chan} {guild}")


@bot.listen("on_message")
async def gotta_catch_em_all(message):
    if message.author.id == pokecord_id and message.embeds and spawn_text.lower() in message.embeds[0].title.lower():
        chan = message.channel
        if chan in identify_channels or chan in alert_channels:
            identify_category = identify_channels.get(chan)
            role, alert_category = alert_channels.get(chan, (None, None))
            result = rotomdex.identify(url=message.embeds[0].image.url)
            match = result["best_match"]
            p = match.pokemon
            article = "an" if p.category == pokemon.Category.Uncommon else "a"
            identification = f"A wild **{p}** has appeared! It's {article} **{p.category}** Pokémon."

            is_mentionable = role.mentionable
            pinged = False
            if chan in identify_channels:
                if chan in alert_channels and p.category >= alert_category:
                    await chan.trigger_typing()
                    log_pokemon(match, message)
                    if not is_mentionable:
                        try:
                            await role.edit(mentionable=True)
                            pinged = True
                        except discord.Forbidden:
                            pass
                    await chan.send(f"{role.mention} {identification}")
                elif p.category >= identify_category:
                    await chan.trigger_typing()
                    await chan.send(identification)
            elif p.category >= alert_category:
                await chan.trigger_typing()
                log_pokemon(match, message)
                if not is_mentionable:
                    try:
                        await role.edit(mentionable=True)
                        pinged = True
                    except discord.Forbidden:
                        pass
                await chan.send(f"{role.mention} {identification}")

            if not is_mentionable and pinged:
                await role.edit(mentionable=False)


@bot.group(aliases=["warn", "ping"])
async def alert(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.invoke(bot.get_command("alert info"))


@alert.command(name="info")
async def alert_info(ctx):
    if ctx.channel not in alert_channels:
        msg = f"Alerts are disabled in {ctx.channel.mention}."
    else:
        role, category = alert_channels[ctx.channel]
        msg = f"Alerts in {ctx.channel.mention}: **@{role}** will be pinged for **{category}+** Pokémon."
    await ctx.send(msg)


@alert.command(name="enable", aliases=["on"])
@owner_or_has_permissions(manage_guild=True)
async def alert_enable(ctx, *, message=""):
    parser = utils.NoExitParser()
    parser.add_argument("role")
    parser.add_argument("-c", "--category", default="Mythical", type=pokemon.Category.parse)
    parser.add_argument("-s", "--server", action="store_true")
    parser.add_argument("-o", "--override", action="store_true")
    try:
        args = parser.parse_args(shlex.split(message))
        args.role = await commands.RoleConverter().convert(ctx, args.role)
    except ValueError:
        usage = f"`{ctx.prefix}alert (enable|on) <role> [-c | --category <category>] [-s | --server] [-o | --override]`"
        await ctx.send(f"**Usage:** {usage}")
    except KeyError as e:
        await ctx.send(f"Unknown category: {e}. Valid categories are: `{' | '.join(pokemon.Category.names())}`")
    else:
        if args.server:
            already_exists = 0
            for channel in ctx.guild.text_channels:
                if channel in alert_channels:
                    already_exists += 1
                    if args.override:
                        alert_channels[channel] = (args.role, args.category)
                else:
                    alert_channels[channel] = (args.role, args.category)
            alert_servers.add(ctx.guild)
            ack = f"Enabled alerts in all channels: **@{args.role}** will be pinged for **{args.category}+** Pokémon."
            if already_exists > 0:
                ack += f"\n{already_exists} channels already had alerts on and have been "
                if args.override:
                    ack += f"overridden."
                else:
                    ack += f"skipped. Use `-o | --override` to override them."
        else:
            alert_channels[ctx.channel] = (args.role, args.category)
            ack = f"Enabled alerts in {ctx.channel.mention}: **@{args.role}** will be pinged for **{args.category}+** Pokémon."
        await ctx.send(ack)


@alert.command(name="disable", aliases=["off"])
@owner_or_has_permissions(manage_guild=True)
async def alert_disable(ctx, *, message=""):
    parser = utils.NoExitParser()
    parser.add_argument("-s", "--server", action="store_true")
    args, unknown = parser.parse_known_args(shlex.split(message))
    if args.server:
        for channel in ctx.guild.text_channels:
            if channel in alert_channels:
                del alert_channels[channel]
        alert_servers.discard(ctx.guild)
        ack = f"Disabled alerts in all channels."
    else:
        if ctx.channel in alert_channels:
            del alert_channels[ctx.channel]
            alert_servers.discard(ctx.guild)
            ack = f"Disabled alerts in {ctx.channel.mention}"
        else:
            ack = f"Alerts are already disabled in {ctx.channel.mention}"
    await ctx.send(ack)


@bot.group(aliases=["id"])
async def identify(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.invoke(bot.get_command("identify info"))


@identify.command(name="info")
async def identify_info(ctx):
    if ctx.channel not in identify_channels:
        msg = f"Identification is disabled in {ctx.channel.mention}."
    else:
        category = identify_channels[ctx.channel]
        msg = f"Identification is enabled in {ctx.channel.mention} for **{category}+** Pokémon."
    await ctx.send(msg)


@identify.command(name="enable", aliases=["on"])
@owner_or_has_permissions(manage_guild=True)
async def identify_enable(ctx, *, message=""):
    parser = utils.NoExitParser()
    parser.add_argument("-c", "--category", default="Common", type=pokemon.Category.parse)
    parser.add_argument("-s", "--server", action="store_true")
    parser.add_argument("-o", "--override", action="store_true")
    try:
        args = parser.parse_args(shlex.split(message))
    except ValueError:
        usage = f"`{ctx.prefix}identify (enable|on) [-c | --category <category>] [-s | --server] [-o | --override]`"
        await ctx.send(f"**Usage:** {usage}")
    except KeyError as e:
        await ctx.send(f"Unknown category: {e}. Valid categories are: `{' | '.join(pokemon.Category.names())}`")
    else:
        if args.server:
            already_exists = 0
            for channel in ctx.guild.text_channels:
                if channel in identify_channels:
                    already_exists += 1
                    if args.override:
                        identify_channels[channel] = args.category
                else:
                    identify_channels[channel] = args.category
            identify_servers.add(ctx.guild)
            ack = f"Enabled identification in all channels for **{args.category}+** Pokémon."
            if already_exists > 0:
                ack += f"\n{already_exists} channels already had identification on and have been "
                if args.override:
                    ack += f"overridden."
                else:
                    ack += f"skipped. Use `-o | --override` to override them."
        else:
            identify_channels[ctx.channel] = args.category
            ack = f"Enabled identification in {ctx.channel.mention} for **{args.category}+** Pokémon."
        await ctx.send(ack)


@identify.command(name="disable", aliases=["off"])
@owner_or_has_permissions(manage_guild=True)
async def identify_disable(ctx, *, message=""):
    parser = utils.NoExitParser()
    parser.add_argument("-s", "--server", action="store_true")
    args, unknown = parser.parse_known_args(shlex.split(message))
    if args.server:
        for channel in ctx.guild.text_channels:
            if channel in identify_channels:
                del identify_channels[channel]
        identify_servers.discard(ctx.guild)
        ack = f"Disabled identification in all channels."
    else:
        if ctx.channel in identify_channels:
            del identify_channels[ctx.channel]
            identify_servers.discard(ctx.guild)
            ack = f"Disabled identification in {ctx.channel.mention}"
        else:
            ack = f"Identification is already disabled in {ctx.channel.mention}"
    await ctx.send(ack)


@bot.command(aliases=["s"], hidden=True)
@commands.is_owner()
async def say(ctx, *, message):
    await ctx.send(message)


@bot.command(aliases=["link"])
async def invite(ctx):
    p = discord.Permissions.text()
    p.mention_everyone = False
    p.send_tts_messages = False
    p.manage_roles = True
    await ctx.send(oauth_url(bot.user.id, p))


@bot.event
async def on_ready():
    ts = crayons.white(utils.get_timestamp(), bold=True)
    print(f"{ts} Logged in as {crayons.red(bot.user, bold=True)} (ID {crayons.yellow(bot.user.id, bold=True)})")
    owner = bot.get_user(bot.owner_id)
    try:
        await owner.send("Ready !", delete_after=10)
    except discord.HTTPException:
        pass


@bot.event
async def on_command_error(ctx, error):
    ts = crayons.white(utils.get_timestamp(), bold=True)
    print(f"{ts} {crayons.red(error.__class__.__name__, bold=True)} {error}")
    if isinstance(error, commands.NotOwner):
        await ctx.send("**Restricted command.**", delete_after=10)
    elif isinstance(error, commands.MissingPermissions):
        missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
        await ctx.send(f"You are missing {missing} permission(s) to run this command.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(error)


def get_token(*, test=False):
    token = os.getenv("ROTOMDEX_TOKEN")
    if token:
        return token
    path = ".token"
    if test:
        path += "-test"
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


if __name__ == '__main__':
    import sys

    test = "--test" in sys.argv
    if test:
        bot.command_prefix = "-"
    bot.run(get_token(test=test))
