import discord
import akinator.exceptions
from discord.ext import commands
from akinator.async_aki import Akinator
import aiohttp

def w(ctx: commands.Context, aki: Akinator) -> discord.Embed:
    # {'id': '444271', 
    # 'name': 'IShowSpeed', 
    # 'id_base': '19813121', 
    # 'proba': '0.894199', 
    # 'description': 'YouTuber', 
    # 'valide_contrainte': '1', 
    # 'ranking': '5', 
    # 'pseudo': 'Speed', 
    # 'picture_path': 'partenaire/t/19813121__1094299039.jpeg', 
    # 'corrupt': '0', 
    # 'relative': '0', 
    # 'award_id': '-1', 
    # 'flag_photo': 0, 
    # 'absolute_picture_path': 'https://photos.clarinea.fr/BL_25_en/600/partenaire/t/19813121__1094299039.jpeg'}
    embed_win = discord.Embed(title=aki.first_guess['name'], description=aki.first_guess['description'],
                              colour=0x00FF00)
    if ctx.message.author.avatar: embed_win.set_author(name=ctx.author, icon_url=ctx.message.author.avatar.url)
    else: embed_win.set_author(name=ctx.author)
    embed_win.set_image(url=aki.first_guess['absolute_picture_path'])
    embed_win.add_field(name="Ranking", value="#"+aki.first_guess['ranking'], inline=True)
    embed_win.add_field(name="Questions", value=aki.step+1, inline=True)
    embed_win.add_field(name="Progress", value=f"{aki.progression}%", inline=True)
    return embed_win
def qEmbed(aki: Akinator, ctx: commands.Context, q: str) -> discord.Embed:
    e = discord.Embed(title=f"{aki.step+1}. {q}", description=f"{aki.progression}%", color=0x00FF00)
    if ctx.message.author.avatar: e.set_author(name=ctx.author, icon_url=ctx.message.author.avatar.url)
    else: e.set_author(name=ctx.author)
    return e

class QView(discord.ui.View):
    def __init__(self, aki: Akinator, ctx: commands.Context):
        super().__init__(timeout=None)
        self.add_item(ButtonAction(aki, ctx, 0, 'Yes', '✅', 'y'))
        self.add_item(ButtonAction(aki, ctx, 0, 'No', '❌', 'n'))
        self.add_item(ButtonAction(aki, ctx, 0, 'Don\'t Know', '❓', 'idk'))
        self.add_item(ButtonAction(aki, ctx, 1, 'Probably', '👍', 'p'))
        self.add_item(ButtonAction(aki, ctx, 1, 'Probably Not', '👎', 'pn'))
        self.add_item(ButtonAction(aki, ctx, 2, 'Back', '⏮', 'b'))
        self.add_item(ButtonAction(aki, ctx, 2, 'Stop', '🛑', 's'))

class ButtonAction(discord.ui.Button):
    def __init__(self, aki: Akinator, ctx: commands.Context, row: int, l: str, emoji: str, action: str):
        super().__init__(label=l, style=discord.ButtonStyle.success, emoji=emoji, row=row)
        self.aki, self.action, self.ctx = aki, action, ctx
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if interaction.user != self.ctx.author:
            return await interaction.followup.send(content=f"<@{self.ctx.message.author.id}> is playing this game! Use `-aki` to create your own game.", 
                                                   ephemeral=True)
        try:
            if self.action == 's':
                return await interaction.message.edit(content=f"Skill issue <@{interaction.user.id}>!", view=None, embed=None)
            if self.action == 'b':
                try: q = await self.aki.back()
                except akinator.exceptions.CantGoBackAnyFurther:
                    return await interaction.followup.send(content=f"akinator.exceptions.CantGoBackAnyFurther", ephemeral=True)
            else: 
                await interaction.message.edit(view=None)
                q = await self.aki.answer(self.action)
            if self.aki.progression <= 90 and self.aki.step < 79:
                await interaction.message.edit(embed=qEmbed(self.aki, self.ctx, q), view=QView(self.aki, self.ctx))
            else: 
                await self.aki.win()
                embed = w(self.ctx, self.aki)
                await interaction.message.edit(embed=embed, view=RView(self.aki, self.ctx))
        except akinator.exceptions.AkiTimedOut:
            await interaction.followup.send(content=f"Your session has timed out! Use `-aki` to create a new game.", ephemeral=True)

class RView(discord.ui.View):
    def __init__(self, aki: Akinator, ctx):
        super().__init__(timeout=None)
        self.add_item(ButtonAction0(aki, ctx, 'Yes', '✅', 'y'))
        self.add_item(ButtonAction0(aki, ctx, 'No', '❌', 'n'))

class ButtonAction0(discord.ui.Button):
    def __init__(self, aki: Akinator, ctx: commands.Context, l: str, emoji: str, action: str):
        super().__init__(label=l, style=discord.ButtonStyle.success, emoji=emoji)
        self.aki, self.action, self.ctx = aki, action, ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.followup.send(content=f"<@{self.ctx.message.author.id}> is playing this game! Use `-aki` to create your own game.", 
                                                   ephemeral=True)
        if self.action == 'y':
            embed_win = discord.Embed(title='GG!', color=0x00FF00)
            embed_win.add_field(name=self.aki.first_guess['name'], value=self.aki.first_guess['description'], inline=False)
            embed_win.set_image(url=self.aki.first_guess['absolute_picture_path'])
            embed_win.add_field(name="Ranking", value="#"+self.aki.first_guess['ranking'], inline=True)
            embed_win.add_field(name="Questions", value=self.aki.step+1, inline=True)
            embed_win.add_field(name="Progress", value=f"{self.aki.progression}%", inline=True)
            if self.ctx.message.author.avatar: embed_win.set_author(name=self.ctx.author, icon_url=self.ctx.message.author.avatar.url)
            else: embed_win.set_author(name=self.ctx.author)
            await interaction.response.edit_message(embed=embed_win, view=None)
        else: 
            embed_loss = discord.Embed(title="Game over!", description="Here's some of my guesses:", color=0xFF0000)
            for times in self.aki.guesses:
                embed_loss.add_field(name=times['name'], value=times['description'])
            if self.ctx.message.author.avatar: embed_loss.set_author(name=self.ctx.author, icon_url=self.ctx.message.author.avatar.url)
            else: embed_loss.set_author(name=self.ctx.author)
            await interaction.response.edit_message(embed=embed_loss, view=None)

# @commands.max_concurrency(1, per=BucketType.default, wait=False)
async def Aki(ctx: commands.Context, cat: str='people', lang: str='en'):
    msg = await ctx.reply('Starting game…')
    categories = ['people', 'objects', 'animals']
    sfw = not ctx.channel.nsfw if ctx.guild else True
    languages = ['en', 'ar', 'cn', 'de', 'es', 'fr', 'it', 'jp', 'kr', 'nl', 'pl', 'pt', 'ru', 'tr', 'id']
    if not lang in languages:
        return await msg.edit(content=f"Invalid language parameter.\nSupported languages:```{languages}```")
    if not cat in categories:
        return await msg.edit(content=f'Category `{cat}` not found.\nAvailable categories:```{categories}```')
    try: 
        aki = Akinator()
        session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))
        q = await aki.start_game(language=f'{lang}' if cat == 'people' else f'{lang}_{cat}', child_mode=sfw, client_session=session)
        await msg.edit(content=None, embed=qEmbed(aki, ctx, q), view=QView(aki, ctx))
    except Exception as e: await msg.edit(content=f"Error! :(\n{e}")

# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.MaxConcurrencyReached):
#         title_error_four = 'Someone is already playing'
#         desc_error_four = 'Please wait until the person currently playing is done with their turn'
#         embed_var_four = discord.Embed(title=title_error_four,
#                                        description=desc_error_four,
#                                        color=0xFF0000)
#         await ctx.reply(embed=embed_var_four)