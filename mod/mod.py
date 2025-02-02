import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel, getLogger
import re
import asyncio
from .utils.util import Pag

logger = getLogger(__name__)


class moderation(commands.Cog):
    """
    Moderation commands to moderate the server!
    """
    
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.plugin_db.get_partition(self)
        self.errorcolor = 0xfc4343
        self.blue = 0x3ef7e8
        self.green = 0x00ff5a
        self.yell = 0xfffc36
        self.tick = "<:tick:819613405597532160>"
        self.cross = "<:x2:819613332892942347>"

    #On channel create set up mute stuff
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        guild = channel.guild
        role = discord.utils.get(guild.roles, name = "Muted")
        if role == None:
            role = await guild.create_role(name = "Muted")
        await channel.set_permissions(role, send_messages = False)
   
    #log channel
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMIN)
    async def modlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the log channel for moderation actions.
        """
        await self.db.find_one_and_update(
            {"_id": "config"}, {"$set": {"channel": channel.id}}, upsert=True
        )
        embed = discord.Embed(
            description=f" **{self.tick} Set modlog channel to {channel.mention}!**", color=self.green
        )
        await ctx.send(embed=embed)
        return

    #Purge command
    @commands.command(aliases = ["clear"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def purge(self, ctx, amount = 2, member : discord.Member = None):
        """
        Purge certain amount of messages!
        **Usage**:
        {ctx.prefix}purge 10
        {ctx.prefix}purge 10 @Aniket
        {ctx.prefix}purge <amount> [member]
        """
        #get-channel
        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        max_purge = 500
        if amount >= 1 and amount <= max_purge:
            await ctx.channel.purge(limit = amount + 1)
            embed = discord.Embed(
                description = f"{self.tick} Purged **{amount}** message(s)!",
                color = self.green
            )
            await ctx.send(embed = embed, delete_after = 10.0)
            embed = discord.Embed(
                title = "Purge 📑",
                color = self.green
            )
            embed.add_field(name="Amount :", value=f"**{amount}**", inline=True)
            embed.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
            embed.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
            await channel.send(embed = embed)
        if amount < 1:
            embed = discord.Embed(
                title = "Purge Error",
                description = f"**{self.cross} You must purge more then `{amount}` message(s)!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed, delete_after = 5.0)
            await ctx.message.delete()
        if amount > max_purge:
            embed = discord.Embed(
                title = "Purge Error",
                description = f"**{self.cross} You must purge less then `{amount}` messages!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed, delete_after = 5.0)
            await ctx.message.delete()

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions!",
                description = "**{self.cross} You are missing permissions to purge messages!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed, delete_after = 5.0)
            await ctx.message.delete()


    #Kick command
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def kick(self, ctx, member : discord.Member = None, *, reason = None):
        """
        Kicks the specified member.
        **Usage**:
        {ctx.prefix}kick @member 
        {ctx.prefix}kick @member bad!
        """
        channel_config = await self.db.find_one({"_id": "config"})

        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}kick <member> [reason]\n**Example: **{ctx.prefix}kick @member\n**Example: **{ctx.prefix}kick @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required | [] - optional")
            await ctx.send(embed = embed)
        else:
            if member.id == ctx.message.author.id:
                embed = discord.Embed(
                    description = f"{self.cross} **You can't kick yourself!**",
                    color = self.errorcolor
                )
                await ctx.send(embed = embed)
            else:
                if member.guild_permissions.administrator:
                    embed = discord.Embed(
                        description = f"{self.cross} **That user is an Admin, I can't kick them!**",
                        color = self.errorcolor
                    )
                    await ctx.send(embed = embed)
                else:    
                    if reason == None:
                        await member.kick(reason = f"Moderator - {ctx.message.author.name}#{ctx.message.author.discriminator}.\nReason - No reason proivded.")
                        embed = discord.Embed(
                            description = f"***{self.tick} {member} has been kicked!***",
                            color = self.green
                        )
                        await ctx.send(embed = embed)
                        msgembed = discord.Embed(
                            description = f"**You have been kicked from `{ctx.guild.name}`**",
                            color = self.blue
                        )
                        try:
                            await member.send(embed=msgembed)
                        except discord.errors.Forbidden:
                            embedlog2 = discord.Embed(color = self.blue)
                            embedlog2.set_author(name=f"Kick 📑 | {member}", icon_url=member.avatar_url)
                            embedlog2.add_field(name="User Kicked :", value=f"{member.mention}", inline=True)
                            embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                            embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                            embedlog2.add_field(name="Reason :", value="No reason provided!", inline=False)
                            embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                            return await channel.send(embed = embedlog2)    
                        
                        embedlog = discord.Embed(
                            color = self.green
                        )
                        embedlog.set_author(
                            name=f"Kick 📑 | {member}",
                            icon_url=member.avatar_url,
                        )
                        embedlog.add_field(name="User Kicked :", value=f"{member.mention}", inline=True)
                        embedlog.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog.add_field(name="Reason :", value="No reason provided!", inline=False)
                        await channel.send(embed = embedlog)

                    else:
                        await member.kick(reason = f"Moderator - {ctx.message.author.name}#{ctx.message.author.discriminator}.\nReason - {reason}")
                        
                        embed = discord.Embed(
                            description = f"**{self.tick} {member} has been kicked!** \n**|| {reason}**",
                            color = self.green
                        )
                        await ctx.send(embed = embed)
                        msgembed = discord.Embed(
                            description = f"**You have been kicked from `{ctx.guild.name}` \n|| {reason}**",
                            color = self.blue
                        )
                        try:
                            await member.send(embed=msgembed)
                        except discord.errors.Forbidden:
                            embedlog2 = discord.Embed(color = self.blue)
                            embedlog2.set_author(name=f"Kick 📑 | {member}", icon_url=member.avatar_url)
                            embedlog2.add_field(name="User Kicked :", value=f"{member.mention}", inline=True)
                            embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                            embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                            embedlog2.add_field(name="Reason :", value="No reason provided!", inline=False)
                            embedlog2.add_field(name="Status :", value=f"{reason}", inline=False)
                            return await channel.send(embed = embedlog2)  

                        embedlog = discord.Embed(
                            color = self.green
                        )
                        embedlog.set_author(
                            name=f"Kick 📑 | {member}",
                            icon_url=member.avatar_url,
                        )
                        embedlog.add_field(name="User Kicked :", value=f"{member.mention}", inline=True)
                        embedlog.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog.add_field(name="Reason :", value=f"{reason}", inline=False)
                        await channel.send(embed = embedlog)
                                               
                        
    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions !",
                description = f"{self.cross} You are missing permissions to kick members!",
                color = self.errorcolor
            )
            await ctx.send(embed = embed)


    #Ban command
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def ban(self, ctx, member : discord.Member = None, *, reason = None):
        """
        Bans the specified member.
        """
        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))
  
        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}kick <member> [reason]\n**Example: **{ctx.prefix}kick @member\n**Example: **{ctx.prefix}kick @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required | [] - optional")
            await ctx.send(embed = embed)
        else:
            if member.id == ctx.message.author.id:
                embed = discord.Embed(
                    description = f"{self.cross} **You can't kick yourself!**",
                    color = self.errorcolor
                )
                await ctx.send(embed = embed)
            else:
                if member.guild_permissions.administrator:
                    embed = discord.Embed(
                        description = f"{self.cross} **That user is a Admin, I can't ban them!**",
                        color = self.errorcolor
                    )
                    await ctx.send(embed = embed)
                else:    
                    if reason == None:
                        await member.ban(reason = f"Moderator - {ctx.message.author.name}#{ctx.message.author.discriminator}.\nReason - No Reason Provided.")
                        embed = discord.Embed(
                            description = f"***{self.tick} {member} has been banned !***",
                            color = self.green
                        )
                        await ctx.send(embed = embed)
                        msgembed = discord.Embed(
                            description = f"**You have been banned from `{ctx.guild.name}`**",
                            color = self.blue
                        )
                        
                        try:
                            await member.send(embed=msgembed)
                        except discord.errors.Forbidden:
                            embedlog2 = discord.Embed(color = self.blue)
                            embedlog2.set_author(name=f"Ban 📑 | {member}", icon_url=member.avatar_url)
                            embedlog2.add_field(name="User Banned :", value=f"{member.mention}", inline=True)
                            embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                            embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                            embedlog2.add_field(name="Reason :", value="No reason provided!", inline=False)
                            embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                            return await channel.send(embed = embedlog2)

                        embedlog = discord.Embed(color = self.green)
                        embedlog.set_author(
                            name=f"Ban 📑 | {member}",
                            icon_url=member.avatar_url,
                        )
                        embedlog.add_field(name="User Banned :", value=f"{member.mention}", inline=True)
                        embedlog.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog.add_field(name="Reason :", value="No reason provided!", inline=False)
                        await channel.send(embed = embedlog)
                    else:
                        await member.ban(reason = f"Moderator - {ctx.message.author.name}#{ctx.message.author.discriminator}.\nReason - {reason}")
                        embed = discord.Embed(
                            description = f"***{self.tick} {member} has been banned !*** \n**|| {reason}**",
                            color = self.green
                        )
                        await ctx.send(embed = embed)

                        msgembed = discord.Embed(
                            description = f"**You have been banned from `{ctx.guild.name}`\n|| {reason}**",
                            color = self.blue
                        )
                        
                        try:
                            await member.send(embed=msgembed)
                        except discord.errors.Forbidden:
                            embedlog2 = discord.Embed(color = self.blue)
                            embedlog2.set_author(name=f"Ban 📑 | {member}", icon_url=member.avatar_url)
                            embedlog2.add_field(name="User Banned :", value=f"{member.mention}", inline=True)
                            embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                            embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                            embedlog2.add_field(name="Reason :", value=f"{reason}", inline=False)
                            embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                            return await channel.send(embed = embedlog2)

                        embedlog = discord.Embed(color = self.green)
                        embedlog.set_author(
                            name=f"Ban 📑 | {member}",
                            icon_url=member.avatar_url,
                        )
                        embedlog.add_field(name="User Banned :", value=f"{member.mention}", inline=True)
                        embedlog.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog.add_field(name="Reason :", value=f"{reason}", inline=False)
                        await channel.send(embed = embedlog)

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions",
                description = f"{self.cross} **You are missing permissions to ban members!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed, delete_after = 5.0)


    #Unban command
    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def unban(self, ctx, *, member : discord.User = None):
        """
        Unbans the specified member.
        """
        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}unban <member>\n**Example: **{ctx.prefix}unban @member",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required")
            await ctx.send(embed = embed)
        else:
            banned_users = await ctx.guild.bans()
            for ban_entry in banned_users:
                user = ban_entry.user

                if (user.name, user.discriminator) == (member.name, member.discriminator):
                    embed = discord.Embed(
                        description = f"{self.tick} **Unbanned `{user.name}`**",
                        color = self.green
                    )
                    await ctx.guild.unban(user)
                    await ctx.send(embed = embed)
                    embed = discord.Embed(
                        title = "Unban 📑",
                        color = self.yell
                    )
                    embed.add_field(name="User UnBanned :", value=f"{member.mention}", inline=True)
                    embed.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                    embed.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                    await channel.send(embed = embed)


    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions!",
                description = "{self.cross} **You are missing permission to unban peole**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed, delete_after = 5.0)

    #Mute command
    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def mute(self, ctx, member : discord.Member = None, *, reason = None):
        """
        Mutes the specified member.
        """
        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))


        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}mute <member> [reason]\n**Example: **{ctx.prefix}mute @member\n**Example: **{ctx.prefix}mute @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required | [] - optional")
            await ctx.send(embed = embed)
        else:
            if member.id == ctx.message.author.id:
                embed = discord.Embed(
                    description = f"{self.cross} **You can't mute yourself!**",
                    color = self.errorcolor
                )
                await ctx.send(embed = embed, delete_after = 5.0)
            else:
                if reason == None:
                    role = discord.utils.get(ctx.guild.roles, name = "Muted")
                    if role == None:
                        role = await ctx.guild.create_role(name = "Muted")
                        for channel in ctx.guild.text_channels:
                            await channel.set_permissions(role, send_messages = False)
                    await member.add_roles(role)
                    embed = discord.Embed(
                        description = f"{self.tick} ***{member} has been muted !***",
                        color = self.green
                    )
                    await ctx.send(embed = embed)
                    msgembed = discord.Embed(
                        description = f"**You have been muted in `{ctx.guild.name}`**",
                        color = self.blue
                    )
                        
                    try:
                        await member.send(embed=msgembed)
                    except discord.errors.Forbidden:
                        embedlog2 = discord.Embed(color = self.blue)
                        embedlog2.set_author(name=f"Mute 🔇 | {member}", icon_url=member.avatar_url)
                        embedlog2.add_field(name="User Muted :", value=f"{member.mention}", inline=True)
                        embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog2.add_field(name="Reason :", value="No reason provided!", inline=False)
                        embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                        return await channel.send(embed = embedlog2)

                    embed = discord.Embed(
                        color = self.green
                    )
                    embed.set_author(
                        name=f"Mute 🔇 | {member}",
                        icon_url=member.avatar_url,
                    )
                    embed.add_field(name="User Muted :", value=f"{member.mention}", inline=True)
                    embed.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                    embed.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                    embed.add_field(name="Reason :", value="No reason provided!", inline=False)
                    await channel.send(embed = embed)

                else:
                    role = discord.utils.get(ctx.guild.roles, name = "Muted")
                    if role == None:
                        role = await ctx.guild.create_role(name = "Muted")
                        for channel in ctx.guild.text_channels:
                            await channel.set_permissions(role, send_messages = False)
                    await member.add_roles(role)
                    embed = discord.Embed(
                        description = f"***{self.tick} {member} has been muted !*** \n**|| {reason}**",
                        color = self.green
                    )
                    await ctx.send(embed = embed)
                    msgembed = discord.Embed(
                        description = f"**You have been muted in `{ctx.guild.name}`\n|| {reason}**",
                        color = self.blue
                    )
                        
                    try:
                        await member.send(embed=msgembed)
                    except discord.errors.Forbidden:
                        embedlog2 = discord.Embed(color = self.blue)
                        embedlog2.set_author(name=f"Mute 🔇 | {member}", icon_url=member.avatar_url)
                        embedlog2.add_field(name="User Muted :", value=f"{member.mention}", inline=True)
                        embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                        embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                        embedlog2.add_field(name="Reason :", value=f"{reason}", inline=False)
                        embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                        return await channel.send(embed = embedlog2)

                    embed = discord.Embed(
                        color = self.green
                    )
                    embed.set_author(
                        name=f"Mute 🔇 | {member}",
                        icon_url=member.avatar_url,
                    )
                    embed.add_field(name="User Muted :", value=f"{member.mention}", inline=True)
                    embed.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                    embed.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                    embed.add_field(name="Reason :", value=f"{reason}", inline=False)
                    await channel.send(embed = embed)

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions!",
                description = "{self.cross} **You are missing permission to mute people!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed)

    #Unmute command
    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def unmute(self, ctx, member : discord.Member = None):
        """
        Unmutes the specified member.
        """
        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}unmute <member> [reason]\n**Example: **{ctx.prefix}unmute @member\n**Example: **{ctx.prefix}unmute @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required | [] - optional")
            await ctx.send(embed = embed)
        else:
            role = discord.utils.get(ctx.guild.roles, name = "Muted")
            if role in member.roles:
                await member.remove_roles(role)
                embed = discord.Embed(
                    description = f"***{self.tick} {member} has been unmuted!***",
                    color = self.green
                )
                await ctx.send(embed = embed)
                msgembed = discord.Embed(
                    description = f"**You have been unmuted in `{ctx.guild.name}`**",
                    color = self.blue
                )
                        
                try:
                    await member.send(embed=msgembed)
                except discord.errors.Forbidden:
                    embedlog2 = discord.Embed(color = self.blue)
                    embedlog2.set_author(name=f"Unmute 🔉 | {member}", icon_url=member.avatar_url)
                    embedlog2.add_field(name="User UnMuted :", value=f"{member.mention}", inline=True)
                    embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                    embedlog2.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                    embedlog2.add_field(name="Reason :", value="No reason provided!", inline=False)
                    embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
                    return await channel.send(embed = embedlog2)

                embed = discord.Embed(
                    color = self.blue
                )
                embed.set_author(
                    name=f"Unmute 🔉 | {member}",
                    icon_url=member.avatar_url,
                )
                embed.add_field(name="User UnMuted :", value=f"{member.mention}", inline=True)
                embed.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=True)
                embed.add_field(name="Channel :", value=f"{ctx.message.channel.mention}", inline=True)
                embed.add_field(name="Reason :", value="No reason provided!", inline=False)
                await channel.send(embed = embed)
            else:
                embed = discord.Embed(
                    title = "Unmute Error!",
                    description = f"**{self.cross} {member.mention} is not muted!**",
                    color = self.errorcolor
                )
                await ctx.send(embed = embed)

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title = "Missing Permissions!",
                description = f"{self.cross} **You are missing permission to unmute people!**",
                color = self.errorcolor
            )
            await ctx.send(embed = embed)

    #warn command        
    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warn(self, ctx, member : discord.Member = None, *, reason: str):
        """Warn a member.
        Usage:
        {ctx.prefix}warn @member Spoilers
        """
        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}warn <member> <reason>\n**Example: **{ctx.prefix}warn @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required")
            return await ctx.send(embed = embed)

        if member.bot:
            embed = discord.Embed(
                description = f"**{self.cross} Bots can't be warned.**",
                color = self.errorcolor
            )
            return await ctx.send(embed=embed)

        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            config = await self.db.insert_one({"_id": "warns"})

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            userwarns = config[str(member.id)] = []

        if userwarns is None:
            userw = []
        else:
            userw = userwarns.copy()

        userw.append({"reason": reason, "mod": ctx.author.id})

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): userw}}, upsert=True
        )

        embed = discord.Embed(
            description = f"{self.tick} ***{member} has been warned.***\n**|| {reason}**",
            color = self.green
        )
        await ctx.send(embed = embed)
        msgembed = discord.Embed(
            description = f"**You have been warned in `{ctx.guild.name}`\n|| {reason}**",
            color = self.blue
        )
                        
        try:
            await member.send(embed=msgembed)
        except discord.errors.Forbidden:
            embedlog2 = discord.Embed(color = self.blue)
            embedlog2.set_author(name=f"Warn | {member}", icon_url=member.avatar_url)
            embedlog2.add_field(name="User Warn :", value=f"{member.mention}", inline=True)
            embedlog2.add_field(name="Moderator :", value=f"{ctx.message.author.mention}", inline=False)
            embedlog2.add_field(name="Total Warnings :", value=warning, inline = False)
            embedlog2.add_field(name="Reason :", value=reason, inline=False)
            embedlog2.add_field(name="Status :", value="I could not DM them.", inline=False)
            return await channel.send(embed = embedlog2)

        await channel.send(
            embed=await self.generateWarnEmbed(
                str(member.id), str(ctx.author.id), len(userw), reason
            )
        )
        del userw
        return


    @commands.command()
    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    async def pardon(self, ctx, member: discord.Member = None, *, reason: str):
        """Remove all warnings of a  member.
        Usage:
        {ctx.prefix}pardon @member Nice guy
        """
        if member == None:
            embed = discord.Embed(
                title=f"{self.cross} Invalid Usage!",
                description = f"**Usage: **{ctx.prefix}pardon <member> <reason>\n**Example: **{ctx.prefix}pardon @member doing spam!",
                color = self.errorcolor
            )
            embed.set_footer(text="<> - Required")
            return await ctx.send(embed = embed)

        if member.bot:
            embed = discord.Embed(
                description = f"**{self.cross} Bots can't be warned, so they can't be pardoned.**",
                color = self.errorcolor
            )
            return await ctx.send(embed=embed)

        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            channel = ctx.guild.get_channel(int(channel_config["channel"]))

        if channel is None:
            return

        config = await self.db.find_one({"_id": "warns"})

        if config is None:
            return

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            embed = discord.Embed(
                description = f"**{self.cross} {member} doesn't have any warnings.**",
                color = self.errorcolor
            )
            return await ctx.send(embed = embed)

        if userwarns is None:
            embedtwo = discord.Embed(
                description = f"**{self.cross} {member} doesn't have any warnings.**",
                color = self.errorcolor
            )
            await ctx.send(embed = embedtwo)

        await self.db.find_one_and_update(
            {"_id": "warns"}, {"$set": {str(member.id): []}}
        )

        embedfinal = discord.Embed(
                description = f"{self.tick} ***{member} has been pardoned.***\n**|| {reason}**",
                color = self.green
            )
        await ctx.send(embed = embedfinal)
        

        embed = discord.Embed(color = self.blue)
        embed.set_author(
            name=f"Pardon | {member}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User :", value=f"{member}", inline = True)
        embed.add_field(
            name="Moderator :",
            value=f"<@{ctx.author.id}>",
            inline = True,
        )
        embed.add_field(name="Total Warnings :", value="0", inline = True)
        embed.add_field(name="Reason :", value=reason, inline = False)

        return await channel.send(embed=embed)

    async def generateWarnEmbed(self, memberid, modid, warning, reason):
        member: discord.User = await self.bot.fetch_user(int(memberid))
        mod: discord.User = await self.bot.fetch_user(int(modid))

        embed = discord.Embed(color = self.yell)

        embed.set_author(
            name=f"Warn | {member}",
            icon_url=member.avatar_url,
        )
        embed.add_field(name="User Warn :", value=f"{member}", inline = True)
        embed.add_field(name="Moderator :", value=f"<@{modid}>", inline = True)
        embed.add_field(name="Total Warnings :", value=warning, inline = False)
        embed.add_field(name="Reason :", value=reason, inline = False)
        return embed

    #SLOW MODE COMMAND
    @commands.command(aliases=["sm"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def slowmode(self, ctx, time, channel: discord.TextChannel = None):
        """Set a slowmode to a channel
        It is not possible to set a slowmode longer than 6 hours
        **Usage**:
        {ctx.prefix}slowmode 5s
        {ctx.prefix}slowmode 1h
        """
        if channel == None:
            channel = ctx.channel

        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            logchannel = ctx.guild.get_channel(int(channel_config["channel"]))

        units = {
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1
        }
        seconds = 0
        match = re.findall("([0-9]+[smhd])", time)
        if not match:
            embed = discord.Embed(description=f"{self.cross} I cannot understand your time format!**",color = self.errorcolor)
            return await ctx.send(embed=embed)
        for item in match:
            seconds += int(item[:-1]) * units[item[-1]]
        if seconds > 21600:
            embed = discord.Embed(description=f"**{self.cross} You can't slowmode a channel for longer than 6 hours!**", color=self.errorcolor)
            return await ctx.send(embed=embed)
        try:
            await channel.edit(slowmode_delay=seconds)
        except discord.errors.Forbidden:
            embed = discord.Embed(description=f"**{self.cross} I don't have permission to do this!**", color=self.errorcolor)
            return await ctx.send(embed=embed)
        embed=discord.Embed(description=f"**{self.tick} Set a slowmode delay of `{time}` in {channel.mention}**", color=self.green)
        await ctx.send(embed=embed)
        embed = discord.Embed(color = self.green)
        embed.set_author(
            name=f"Slowmode Enabled",
            icon_url=ctx.guild.icon_url,
        )
        embed.add_field(name=f"Moderator :", value=f"{ctx.message.author.mention}", inline=False)
        embed.add_field(name=f"Channel :", value=f"{channel.mention}", inline=False)
        embed.add_field(name=f"Time", value=f"{time}", inline=False)   
        await logchannel.send(embed=embed)

    @commands.command(aliases=["sm-off"])
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def slowmode_off(self, ctx, channel: discord.TextChannel = None):
        """Turn off the slowmode in a channel"""
        if not channel:
            channel = ctx.channel

        channel_config = await self.db.find_one({"_id": "config"})
        if channel_config is None:
            return await ctx.send("There's no configured log channel.")
        else:
            logchannel = ctx.guild.get_channel(int(channel_config["channel"]))

        seconds_off = 0
        await channel.edit(slowmode_delay=seconds_off)
        embed=discord.Embed(description=f"**{self.tick} Turned off the slowmode for {channel.mention}**", color=self.green)
        await ctx.send(embed=embed)    
        embed = discord.Embed(color = self.blue)
        embed.set_author(
            name=f"Slowmode Disabled",
            icon_url=ctx.guild.icon_url,
        )
        embed.add_field(name=f"Moderator :", value=f"{ctx.message.author.mention}", inline=False)
        embed.add_field(name=f"Channel :", value=f"{channel.mention}", inline=False)  
        await logchannel.send(embed=embed)

    @commands.command()
    @checks.has_permissions(PermissionLevel.MODERATOR)
    async def warns(self, ctx, member: discord.Member = None):
        """Turn off the slowmode in a channel"""
        if member == None:
            member == ctx.message.author

        config = await self.db.find_one({"_id": "warns"})
        userwarns = config[str(member.id)]    

        try:
            userwarns = config[str(member.id)]
        except KeyError:
            userwarns = config[str(member.id)] = []

        if userwarns is None:
            userw = []
        else:
            userw = userwarns.copy()
        
        logger.info(f"warns - || {userwarns}  ||")  

        pages = []
        for warn in userw:
            description = f"""
            No of warns: `{len(userw)}`
            Warn Reason: `{warn['reason']}`
            Warned By: `<@{warn['mod']}>`
            """
            pages.append(description)
            logger.info(f"warns - || {warn['reason']} , {warn['mod']} ||")  
        
        await Pag(
            title=f"Warns for `{member.display_name}`",
            colour=0xCE2029,
            entries=pages,
            length=1
        ).start(ctx)
  
  

def setup(bot):
    bot.add_cog(moderation(bot))
