import discord
from discord import app_commands

import database
from datetime import datetime

with open("token", "r") as token_id:
    token = token_id.read()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class Page(discord.ui.View):
    def __init__(self, *, timeout=180, queue=[], page=0):
        super().__init__(timeout=timeout)
        self.queue = queue
        self.page = page

    @discord.ui.button(label="⬅️ Previous page", style=discord.ButtonStyle.gray)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page <= 0:
            button.disabled = True
            await interaction.response.send_message("🚫 You're already at the first page!", ephemeral=True)
        else:
            self.page -= 1
            await interaction.response.edit_message(embed=compose_queue(self.page, self.queue), view=self)

    @discord.ui.button(label="➡️ Next page", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page >= max_page(self.queue):
            button.disabled = True
            await interaction.response.send_message("🚫 You're already at the last page!", ephemeral=True)
        else:
            self.page += 1
            await interaction.response.edit_message(embed=compose_queue(self.page, self.queue), view=self)

def max_page(queue):
    idx = int(len(queue) / 10)
    # Edge case: if queue length is 0
    if len(queue) == 0:
        pass
    # Edge case: if queue length is non-zero multiple of 10
    elif len(queue) % 10 == 0:
        idx -= 1
    return idx


def compose_queue(page: int, queue: list):
    try:
        station_slice = queue[10 * page: 10 * page + 10]
    except IndexError:
        station_slice = queue[10 * page: -1]

    embed_queue = discord.Embed(title="Stations")

    for i in range(len(station_slice)):
        track_number = 10 * page + i + 1
        embed_queue.add_field(name=f"🚌 {track_number}", value=station_slice[i], inline=False)

    return embed_queue


async def route_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    route_list = database.get_route_list()

    return list(set([
        app_commands.Choice(name=route, value=route)
        for route in route_list if route.lower().startswith(current.lower())
    ]))


async def serv_type_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    route = interaction.namespace.route
    start = interaction.namespace.start
    end = interaction.namespace.end

    serv_type = database.get_serv_type(route, start, end)

    return list(set([
        app_commands.Choice(name=serv_type, value=serv_type)
        for serv_type in serv_type
    ]))


async def start_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    direction_list = database.get_direction(interaction.namespace.route)

    # Users have not filled something in the end
    if interaction.namespace.end is None or interaction.namespace.end == "" or interaction.namespace.end == " ":
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in (list(zip(*direction_list))[0])
        ]))
    else:
        # Since user have filled something at the end, thus we can filter out some result according to the end
        result_list = [item[0] for item in direction_list if item[1] == interaction.namespace.end]
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in result_list
        ]))


async def end_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    direction_list = database.get_direction(interaction.namespace.route)

    # Users have not filled something in the start
    if interaction.namespace.start is None or interaction.namespace.start == "" or interaction.namespace.start == " ":
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in (list(zip(*direction_list))[1])
        ]))
    else:
        # Since user have filled something at the start, thus we can filter out some result according to the start
        result_list = [item[1] for item in direction_list if item[0] == interaction.namespace.start]
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in result_list
        ]))


@app_commands.autocomplete(route=route_selection)
@app_commands.autocomplete(end=end_selection)
@app_commands.autocomplete(start=start_selection)
@app_commands.autocomplete(serv_type=serv_type_selection)
@tree.command(
    name="getstop",
    description="Get the stops of a route",
    guild=discord.Object(id=1024304086679568475)
)
async def getstop(interaction, route: str, start: str, end: str, serv_type: str):
    data = database.get_stop_info(route, start, end, serv_type)

    data_list = []
    for i in range(len(data)):
        data_list.append(database.convert_id_to_name(data[i]))

    await interaction.response.defer()

    await interaction.edit_original_response(
        embed=compose_queue(page=0, queue=data_list), view=Page(queue=data_list, page=0))


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1024304086679568475))
    print("Ready!")


# run the bot
client.run(token)
