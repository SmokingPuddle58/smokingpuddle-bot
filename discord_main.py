import discord
from discord import app_commands
from typing import Callable
import datetime


import database

with open("token", "r") as token_id:
    token = token_id.read()

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


class Page(discord.ui.View):
    # Later can change the input into kwargs
    def __init__(self, *, timeout=180, queue, page=0, route, serv_type, dest, funct: Callable):
        super().__init__(timeout=timeout)
        self.queue = queue
        self.page = page
        self.route = route
        self.serv_type = serv_type
        self.dest = dest
        self.funct = funct

    @discord.ui.button(label="<", style=discord.ButtonStyle.gray)

    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page <= 0:
            await interaction.response.edit_message(
                embed=self.funct(self.page, self.queue, self.route, self.serv_type, self.dest), view=self)
        else:
            self.page -= 1
            await interaction.response.edit_message(
                embed=self.funct(self.page, self.queue, self.route, self.serv_type, self.dest), view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page >= max_page(self.queue):
            await interaction.response.edit_message(
                embed=self.funct(self.page, self.queue, self.route, self.serv_type, self.dest), view=self)
        else:
            self.page += 1
            await interaction.response.edit_message(
                embed=self.funct(self.page, self.queue, self.route, self.serv_type, self.dest), view=self)


def max_page(queue):
    idx = int(len(queue) / 10)
    # Edge case: if queue length is 0
    if len(queue) == 0:
        pass
    # Edge case: if queue length is non-zero multiple of 10
    elif len(queue) % 10 == 0:
        idx -= 1
    return idx


def compose_queue(page: int, queue: list, route: str, serv: str, dest: str):
    try:
        station_slice = queue[10 * page: 10 * page + 10]
    except IndexError:
        station_slice = queue[10 * page: -1]

    serv_string = "普通班次" if serv == '1' else "特別班次"

    embed_queue = discord.Embed(title=f"{route} 往 {dest} {serv_string}")

    for i in range(len(station_slice)):
        num = 10 * page + i + 1
        embed_queue.add_field(name=f"🚌 {num}", value=station_slice[i], inline=False)

    return embed_queue



async def route_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    route_list = database.get_route_list()

    return list(set([
        app_commands.Choice(name=route, value=route)
        for route in route_list if route.lower().startswith(current.lower())
    ]))


async def serv_type_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    route = interaction.namespace.路線
    start = interaction.namespace.起點站
    end = interaction.namespace.終點站

    serv_type = database.get_serv_type(route, start, end)

    return list(set([
        app_commands.Choice(name=(f"{serv} 正常班次" if serv == '1' else f"{serv} 特別班次"), value=serv)
        for serv in serv_type
    ]))


async def start_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    direction_list = database.get_direction(interaction.namespace.路線)

    # Users have not filled something in the end
    if interaction.namespace.終點站 is None or interaction.namespace.終點站 == "" or interaction.namespace.終點站 == " ":
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in (list(zip(*direction_list))[0])
        ]))
    else:
        # Since user have filled something at the end, thus we can filter out some result according to the end
        result_list = [item[0] for item in direction_list if item[1] == interaction.namespace.終點站]
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in result_list
        ]))


async def end_selection(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    direction_list = database.get_direction(interaction.namespace.路線)

    # Users have not filled something in the start
    if interaction.namespace.起點站 is None or interaction.namespace.起點站 == "" or interaction.namespace.起點站 == " ":
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in (list(zip(*direction_list))[1])
        ]))
    else:
        # Since user have filled something at the start, thus we can filter out some result according to the start
        result_list = [item[1] for item in direction_list if item[0] == interaction.namespace.起點站]
        return list(set([
            app_commands.Choice(name=direction, value=direction)
            for direction in result_list
        ]))


@app_commands.autocomplete(路線=route_selection)
@app_commands.autocomplete(起點站=start_selection)
@app_commands.autocomplete(終點站=end_selection)
@app_commands.autocomplete(服務類型=serv_type_selection)
@tree.command(
    name="獲得路線的車站",
    description="獲得查詢路線的所有車站",
    guild=discord.Object(id=1024304086679568475)
)
async def get_stop(interaction, 路線: str, 起點站: str, 終點站: str, 服務類型: str):
    data = database.get_stop_info(路線, 起點站, 終點站, 服務類型)

    data_list = []
    for i in range(len(data)):
        data_list.append(database.convert_id_to_name(data[i]))

    await interaction.response.defer()

    await interaction.edit_original_response(
        embed=compose_queue(page=0, queue=data_list, route=路線, serv=服務類型, dest=終點站),
        view=Page(queue=data_list, page=0, dest=終點站, serv_type=服務類型, route=路線, funct=compose_queue))


def compose_queue_for_bus_route_eta(page: int, queue: list, route: str, serv: str, dest: str):
    try:
        station_slice = queue[10 * page: 10 * page + 10]
    except IndexError:
        station_slice = queue[10 * page: -1]

    serv_string = "普通班次" if serv == '1' else "特別班次"

    embed_queue = discord.Embed(title=f"{route} 往 {dest} {serv_string}")

    for i in range(len(station_slice)):
        num = 10 * page + i + 1
        embed_queue.add_field(name=f"🚌 {num} {station_slice[i][0]}", value=station_slice[i][1], inline=False)

    return embed_queue

@app_commands.autocomplete(路線=route_selection)
@app_commands.autocomplete(起點站=start_selection)
@app_commands.autocomplete(終點站=end_selection)
@app_commands.autocomplete(服務類型=serv_type_selection)
@tree.command(
    name="所有車站路線預計到達時間",
    description="獲得查詢路線所有車站預計到達時間",
    guild=discord.Object(id=1024304086679568475)
)
async def get_route_eta(interaction, 路線: str, 起點站: str, 終點站: str, 服務類型: str):
    bound = database.get_bound(路線, 起點站, 終點站, 服務類型)
    data = database.get_stop_info(路線, 起點站, 終點站, 服務類型)
    query_url = f"https://data.etabus.gov.hk/v1/transport/kmb/route-eta/{路線}/{服務類型}"

    json_parsed = database.get_json(query_url)['data']

    station_list = []
    for i in range(len(data)):
        station_list.append(database.convert_id_to_name(data[i]))

    filtered_json = [dict_item for dict_item in json_parsed if dict_item['dir'] == bound]

    data_list = []

    for i in range(len(station_list)):
        eta_info = [item for item in filtered_json if (int(item['seq']) - 1) == i]
        string = ""

        for datum in eta_info:
            string += f"{datetime.datetime.fromisoformat(datum['eta']).time() if datum['eta'] is not None else '末班車經已開出'}\n註：{datum['rmk_tc']}\n"

        data_list.append([station_list[i],string])

    await interaction.response.defer()

    await interaction.edit_original_response(
        embed=compose_queue_for_bus_route_eta(page=0, queue=data_list, route=路線, serv=服務類型, dest=終點站),
        view=Page(queue=data_list, page=0, dest=終點站, serv_type=服務類型, route=路線, funct=compose_queue_for_bus_route_eta))


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=1024304086679568475))
    print("Ready!")


# run the bot
client.run(token)
