import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel
import re
import asyncio

    
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
        self.tick = "✅"
        self.cross = "❌"

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
            description=f" **{self.tick} Set suggestion channel to {channel.mention}!**", color=self.green
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
                if member.guild_permissions.kick_members:
                    embed = discord.Embed(
                        description = f"{self.cross} **That user is a moderator, I can't kick them!**",
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
                title = "Missing Permissions!",
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
                if member.guild_permissions.ban_members:
                    embed = discord.Embed(
                        description = f"{self.cross} **That user is a moderator, I can't ban them!**",
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

class UnMuteCommand(Command):
    def __init__(self, client_instance):
        self.cmd = "unmute"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}unmute <user id>"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to unmute. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message, **kwargs):
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) == 1:
                if is_integer(command[0]):
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    muted_role_id = int(self.storage.settings["guilds"][guild_id]["muted_role_id"])
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    muted_role = message.guild.get_role(muted_role_id)
                    if user is not None:
                        # Remove the muted role from the user and remove them from the guilds muted users list
                        await user.remove_roles(muted_role, reason=f"Unmuted by {message.author.name}")
                        self.storage.settings["guilds"][guild_id]["muted_users"].pop(str(user_id))
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(f"**Unmuted user:** `{user.name}`**.**")
                        
                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="unmute")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Unmuted user**", value=f"`{user.name}`")
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")


class MuteCommand(Command):
    def __init__(self, client_instance):
        self.cmd = "mute"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}mute <user id> [reason]"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.not_enough_arguments = "You must provide a user to mute. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message, **kwargs):
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 1:
                if is_integer(command[0]):
                    guild_id = str(message.guild.id)
                    user_id = int(command[0])
                    muted_role_id = int(self.storage.settings["guilds"][guild_id]["muted_role_id"])
                    try:
                        user = await message.guild.fetch_member(user_id)
                    except discord.errors.NotFound or discord.errors.HTTPException:
                        user = None
                    muted_role = message.guild.get_role(muted_role_id)
                    if len(command) >= 2:
                        # Collects everything after the first item in the command and uses it as a reason.
                        temp = [item for item in command if command.index(item) > 0]
                        reason = " ".join(temp)
                    else:
                        reason = f"Muted by {message.author.name}"
                    if user is not None:
                        # Add the muted role and store them in guilds muted users list. We use -1 as the duration to state that it lasts forever.
                        await user.add_roles(muted_role, reason=f"Muted by {message.author.name}")
                        self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)] = {}
                        self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["duration"] = -1
                        self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["reason"] = reason
                        self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["normal_duration"] = -1
                        await self.storage.write_file_to_disk()
                        # Message the channel
                        await message.channel.send(f"**Permanently muted user:** `{user.name}`**. Reason:** `{reason}`")
                        
                        # Build the embed and message it to the log channel
                        embed_builder = EmbedBuilder(event="mute")
                        await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                        await embed_builder.add_field(name="**Muted user**", value=f"`{user.name}`")
                        await embed_builder.add_field(name="**Reason**", value=f"`{reason}`")
                        embed = await embed_builder.get_embed()
                        log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                        log_channel = message.guild.get_channel(log_channel_id)
                        if log_channel is not None:
                            await log_channel.send(embed=embed)
                        
                    else:
                        await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")
    
    
class TempMuteCommand(Command):
    def __init__(self, client_instance):
        self.cmd = "tempmute"
        self.client = client_instance
        self.storage = client_instance.storage
        self.usage = f"Usage: {self.client.prefix}tempmute <user id> <duration> [reason]"
        self.invalid_user = "There is no user with the userID: {user_id}. {usage}"
        self.invalid_duration = "The duration provided is invalid. The duration must be a string that looks like: 1w3d5h30m20s or a positive number in seconds. {usage}"
        self.not_enough_arguments = "You must provide a user to temp mute. {usage}"
        self.not_a_user_id = "{user_id} is not a valid user ID. {usage}"

    async def execute(self, message, **kwargs):
        command = kwargs.get("args")
        if await author_is_mod(message.author, self.storage):
            if len(command) >= 2:
                if is_integer(command[0]):
                    user_id = int(command[0])
                    duration = parse_duration(command[1])
                    if is_valid_duration(duration):
                        guild_id = str(message.guild.id)
                        mute_duration = int(time.time()) + duration
                        muted_role_id = int(self.storage.settings["guilds"][guild_id]["muted_role_id"])
                        try:
                            user = await message.guild.fetch_member(user_id)
                        except discord.errors.NotFound or discord.errors.HTTPException:
                            user = None
                        muted_role = message.guild.get_role(muted_role_id)
                        if len(command) >= 3:
                            # Collects everything after the first two items in the command and uses it as a reason.
                            temp = [item for item in command if command.index(item) > 1]
                            reason = " ".join(temp)
                        else:
                            reason = f"Temp muted by {message.author.name}"
                        if user is not None:
                            # Add the muted role and store them in guilds muted users list. We use -1 as the duration to state that it lasts forever.
                            await user.add_roles(muted_role, reason=f"Muted by {message.author.name}")
                            self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)] = {}
                            self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["duration"] = mute_duration
                            self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["reason"] = reason
                            self.storage.settings["guilds"][guild_id]["muted_users"][str(user_id)]["normal_duration"] = command[1]
                            await self.storage.write_file_to_disk()
                            # Message the channel
                            await message.channel.send(f"**Temporarily muted user:** `{user.name}` **for:** `{command[1]}`**. Reason:** `{reason}`")
                            
                            # Build the embed and message it to the log channel
                            embed_builder = EmbedBuilder(event="tempmute")
                            await embed_builder.add_field(name="**Executor**", value=f"`{message.author.name}`")
                            await embed_builder.add_field(name="**Muted user**", value=f"`{user.name}`")
                            await embed_builder.add_field(name="**Reason**", value=f"`{reason}`")
                            await embed_builder.add_field(name="**Duration**", value=f"`{command[1]}`")
                            embed = await embed_builder.get_embed()
                            log_channel_id = int(self.storage.settings["guilds"][guild_id]["log_channel_id"])
                            log_channel = message.guild.get_channel(log_channel_id)
                            if log_channel is not None:
                                await log_channel.send(embed=embed)
                        else:
                            await message.channel.send(self.invalid_user.format(user_id=user_id, usage=self.usage))
                    else:
                        await message.channel.send(self.invalid_duration.format(user_id=user_id, usage=self.usage))
                else:
                    await message.channel.send(self.not_a_user_id.format(user_id=command[0], usage=self.usage))
            else:
                await message.channel.send(self.not_enough_arguments.format(usage=self.usage))
        else:
            await message.channel.send("**You must be a moderator to use this command.**")

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
  

def setup(bot):
    bot.add_cog(moderation(bot))
