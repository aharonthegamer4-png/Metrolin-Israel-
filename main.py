import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

# הגדרת אינטנטים מלאים וקידומת פקודות
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# משתנה גלובלי לשמירת מלאי המאפיה בשרת (נשקים וסמים)
MAFIA_INVENTORY = {
    "weapons": 100,
    "drugs": 250
}

# מילון גלובלי למעקב אחרי קישורי הזמנה (Invite Tracker)
invites = {}
async def update_bot_status():
    """עדכון הסטטוס של הבוט לפי כמות המשתמשים בשרת (Watching X/X Active Members)"""
    total_members = sum(guild.member_count for guild in bot.guilds)
    active_count = int(total_members * 0.6) if total_members > 0 else 0
    status_text = f"{active_count}/{total_members} Active Members ⚡"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))

@bot.event
async def on_ready():
    print(f"Metrolin Bot Online: {bot.user}")
    
    # טעינת כל קישורי ההזמנות מכל השרתים לזיכרון בעת ההפעלה
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            pass
            
    # הפעלת סטטוס הפיקוח האקטיבי
    await update_bot_status()
    
    # רישום מחדש של ה-Views הקבועים בבוט בצורה מאובטחת וחוקית לדיסקורד
    bot.add_view(AcceptancePanelLaunchView())
    bot.add_view(AcceptanceActionView())
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketControlView())
    bot.add_view(AbsenceLaunchView())
    bot.add_view(AbsenceApprovalView(member_id=0, name="", duration=""))
    bot.add_view(MafiaTicketLaunchView())
    bot.add_view(MafiaTicketControlView(ticket_type=""))
def find_invite_by_code(invite_list, code):
    for inv in invite_list:
        if inv.code == code:
            return inv
    return None

@bot.event
async def on_member_join(member):
    await update_bot_status()
    
    welcome_channel_id = 1518266605090377909
    invite_log_channel_id = 1518266872402022672
    
    welcome_channel = bot.get_channel(welcome_channel_id)
    invite_log_channel = bot.get_channel(invite_log_channel_id)
    
    inviter_text = "לא ידוע (קוד קבוע/Vanity)"
    invite_code = "N/A"
    
    if member.guild.id in invites:
        try:
            old_invites = invites[member.guild.id]
            new_invites = await member.guild.invites()
            invites[member.guild.id] = new_invites
            
            for new_inv in new_invites:
                old_inv = find_invite_by_code(old_invites, new_inv.code)
                if old_inv and new_inv.uses > old_inv.uses:
                    inviter_text = f"{new_inv.inviter.mention} ({new_inv.inviter.name})"
                    invite_code = new_inv.code
                    break
        except Exception as e:
            print(f"Error tracking invite: {e}")

    if welcome_channel:
        file1 = discord.File("background.gif", filename="background.gif")
        embed_welcome = discord.Embed(
            title="👋 ברוכים הבאים ל-Metrolin IL !",
            description=f"ברוך הבא לשרת הפשע הרשמי {member.mention}!\nנשמח שתקרא את החוקים ותהנה מהשהות שלך איתנו.",
            color=discord.Color.blue()
        )
        embed_welcome.set_image(url="attachment://background.gif")
        embed_welcome.set_footer(text=f"Metrolin IL • משתמש מספר {member.guild.member_count}")
        await welcome_channel.send(file=file1, embed=embed_welcome)

    if invite_log_channel:
        file2 = discord.File("background.gif", filename="background.gif")
        embed_invite = discord.Embed(
            title="📥 לוג כניסות והזמנות משתמשים",
            description=f"**המשתמש שנכנס:** {member.mention}\n**הוזמן על ידי:** {inviter_text}\n**קוד הזמנה:** `{invite_code}`",
            color=discord.Color.dark_green()
        )
        embed_invite.set_image(url="attachment://background.gif")
        await invite_log_channel.send(file=file2, embed=embed_invite)

@bot.event
async def on_member_remove(member):
    await update_bot_status()
class AcceptanceModal(discord.ui.Modal, title="טופס בדיקה וקבלת רולים למשתמש"):
    interviewer = discord.ui.TextInput(label="מי קיבל אותך / ביצע לך ראיון?", placeholder="הכנס שם או איידי של איש הצוות", required=True)
    expected_roles = discord.ui.TextInput(label="אילו רולים אתה אמור לקבל?", placeholder="למשל: משפחת פשע, טירונר, גאנג וכו'", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        review_channel_id = 1518269674851274792
        review_channel = interaction.guild.get_channel(review_channel_id)
        
        if not review_channel:
            await interaction.response.send_message("שגיאה: חדר אישורי הנהלה לא נמצא!", ephemeral=True)
            return

        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title="📝 טופס קבלה חדש ממתין לאישור",
            description=f"**המשתמש המגיש:** {interaction.user.mention}\n**מזהה משתמש (ID):** `{interaction.user.id}`\n\n**👤 הגורם המראיין/מקבל:**\n{self.interviewer.value}\n\n**🛡️ רולים מבוקשים:**\n{self.expected_roles.value}",
            color=discord.Color.orange()
        )
        embed.set_image(url="attachment://background.gif")
        
        # שליחת הטופס לערוץ ההנהלה עם ה-View המאובטח והמתוקן
        await review_channel.send(file=file, embed=embed, view=AcceptanceActionView())
        await interaction.response.send_message("הטופס שלך נשלח בהצלחה לבדיקת הנהלת השרת! אנא המתן לאישור.", ephemeral=True)

class AcceptancePanelLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 הגש טופס בדיקה / קבלת רולים", style=discord.ButtonStyle.success, custom_id="launch_acceptance_modal")
    async def launch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AcceptanceModal())
class AcceptanceActionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def get_target_id_from_embed(self, message: discord.Message) -> int:
        """פונקציית עזר לחילוץ האיידי של המשתמש מתוך הודעת ה-Embed של הטופס"""
        try:
            if message.embeds:
                description = message.embeds[0].description
                for line in description.split("\n"):
                    if "מזהה משתמש (ID):" in line:
                        return int(line.split("`")[1])
        except Exception as e:
            print(f"Error parsing target ID from embed: {e}")
        return 0

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518269453295685652
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ אין לך הרשאה מתאימה (רול הנהלה עליון) להשתמש בכפתור זה!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👢 תן קיק (Kick)", style=discord.ButtonStyle.danger, custom_id="accept_kick_fixed", row=0)
    async def kick_user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_id = self.get_target_id_from_embed(interaction.message)
        if target_id == 0:
            await interaction.response.send_message("❌ שגיאה: לא הצלחתי למצוא את האיידי של המשתמש בטופס!", ephemeral=True)
            return
            
        target_member = interaction.guild.get_member(target_id)
        if not target_member:
            await interaction.response.send_message("❌ המשתמש לא נמצא בשרת יותר!", ephemeral=True)
            return
        try:
            await target_member.kick(reason="נדחה במערכת בדיקת משתמש עלידי ההנהלה")
            await interaction.response.send_message(f"👢 המשתמש {target_member.name} נזרק מהשרת בהצלחה.", ephemeral=True)
            button.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במתן קיק: {e}", ephemeral=True)

    @discord.ui.button(label="🔨 תן באן (Ban)", style=discord.ButtonStyle.danger, custom_id="accept_ban_fixed", row=0)
    async def ban_user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_id = self.get_target_id_from_embed(interaction.message)
        if target_id == 0:
            await interaction.response.send_message("❌ שגיאה: לא הצלחתי למצוא את האיידי של המשתמש בטופס!", ephemeral=True)
            return
            
        try:
            await interaction.guild.ban(discord.Object(id=target_id), reason="נדחה במערכת בדיקת משתמש")
            await interaction.response.send_message(f"🔨 האיידי `{target_id}` נחסם מהשרת לצמיתות.", ephemeral=True)
            button.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במתן באן: {e}", ephemeral=True)
class RoleDropdownSelector(discord.ui.Select):
    def __init__(self, target_member: discord.Member, original_view: discord.ui.View):
        self.target_member = target_member
        self.original_view = original_view
        
        options = []
        guild_roles = sorted(target_member.guild.roles, key=lambda r: r.position, reverse=True)
        
        for role in guild_roles:
            if not role.is_default() and not role.managed:
                options.append(discord.SelectOption(label=role.name, value=str(role.id), description=f"ID: {role.id}"))
            if len(options) == 25:
                break
                
        super().__init__(
            placeholder="בחר רולים להענקה למשתמש...",
            min_values=1,
            max_values=len(options) if options else 1,
            options=options if options else [discord.SelectOption(label="אין רולים זמינים", value="0")]
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values == "0":
            await interaction.response.send_message("לא נבחרו רולים תקפים.", ephemeral=True)
            return
            
        added_roles = []
        for role_id in self.values:
            role = interaction.guild.get_role(int(role_id))
            if role:
                try:
                    await self.target_member.add_roles(role)
                    added_roles.append(role.name)
                except:
                    pass
                    
        roles_list_str = ", ".join(added_roles)
        await interaction.response.send_message(f"✅ הרולים הוענקו בהצלחה ל-{self.target_member.mention}:\n**{roles_list_str}**", ephemeral=True)
        
        for item in self.original_view.children:
            item.disabled = True
        await interaction.message.edit(view=self.original_view)

class RoleSelectionView(discord.ui.View):
    def __init__(self, target_member: discord.Member, original_view: discord.ui.View):
        super().__init__(timeout=60)
        self.add_item(RoleDropdownSelector(target_member, original_view))

@discord.ui.button(label="🛡️ בחר רולים וסיום (Approve)", style=discord.ButtonStyle.success, custom_id="accept_approve_fixed", row=0)
async def select_roles_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    target_id = self.get_target_id_from_embed(interaction.message)
    if target_id == 0:
        await interaction.response.send_message("❌ שגיאה: לא הצלחתי למצוא את האיידי של המשתמש בטופס!", ephemeral=True)
        return
        
    target_member = interaction.guild.get_member(target_id)
    if not target_member:
        await interaction.response.send_message("❌ המשתמש לא נמצא בשרת יותר!", ephemeral=True)
        return
        
    await interaction.response.send_message("אנא בחר מהרשימה מטה את הרולים שברצונך לתת לו:", view=RoleSelectionView(target_member, self), ephemeral=True)

AcceptanceActionView.select_roles_btn = select_roles_btn
class AbsenceModal(discord.ui.Modal, title="טופס הגשת חיסור - צוות פשע"):
    name = discord.ui.TextInput(label="שם מלא / כינוי בשרת", placeholder="הכנס את שמך כאן", required=True)
    duration = discord.ui.TextInput(label="לכמה זמן החיסור?", placeholder="למשל: 3 ימים, שבוע", required=True)
    reason = discord.ui.TextInput(label="סיבת החיסור", placeholder="פרט בקצרה את סיבת החיסור", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        approval_channel_id = 1518273099194171593
        approval_channel = interaction.guild.get_channel(approval_channel_id)
        
        if not approval_channel:
            await interaction.response.send_message("❌ חדר אישור חיסורים לא נמצא!", ephemeral=True)
            return

        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title="⏳ בקשת חיסור חדשה ממתינת לאישור",
            description=f"**מגיש הבקשה:** {interaction.user.mention}\n**שם:** {self.name.value}\n**משך החיסור:** {self.duration.value}\n**סיבה:**\n{self.reason.value}",
            color=discord.Color.dark_gold()
        )
        embed.set_image(url="attachment://background.gif")
        
        await approval_channel.send(
            file=file, 
            embed=embed, 
            view=AbsenceApprovalView(member_id=interaction.user.id, name=self.name.value, duration=self.duration.value)
        )
        await interaction.response.send_message("✅ בקשת החיסור שלך נשלחה בהצלחה לבדיקת ההנהלה!", ephemeral=True)

class AbsenceLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📅 מלא טופס חיסור", style=discord.ButtonStyle.blurple, custom_id="launch_absence_modal")
    async def launch_absence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AbsenceModal())
class AbsenceApprovalView(discord.ui.View):
    def __init__(self, member_id: int, name: str, duration: str):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.name = name
        self.duration = duration
        if member_id != 0:
            self.approve_btn.custom_id = f"abs_approve_{member_id}"
            self.deny_btn.custom_id = f"abs_deny_{member_id}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518269453295685652
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ רק דרגת הנהלה עליונה יכולה לאשר או לדחות חיסורים!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ אשר חיסור", style=discord.ButtonStyle.success)
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        public_log_id = 1510196538490622058
        public_channel = interaction.guild.get_channel(public_log_id)
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        if public_channel:
            file = discord.File("background.gif", filename="background.gif")
            embed = discord.Embed(
                title="📢 עדכון סטטוס חיסורי צוות פשע",
                description=f"**איש הצוות:** <@{self.member_id}>\n**שם:** {self.name}\n**זמן חיסור:** {self.duration}\n**סטטוס:** אושר באופן רשמי ע\"י ההנהלה ✅",
                color=discord.Color.green()
            )
            embed.set_image(url="attachment://background.gif")
            await public_channel.send(file=file, embed=embed)
            
        await interaction.response.send_message("✅ החיסור אושר ופורסם בלוג הציבורי בהצלחה.", ephemeral=True)

    @discord.ui.button(label="❌ דחה חיסור", style=discord.ButtonStyle.danger)
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        try:
            user = await bot.fetch_user(self.member_id)
            await user.send("❌ בקשת החיסור שהגשת בשרת Metrolin IL נדחתה על ידי ההנהלה.")
        except:
            pass
        await interaction.response.send_message("❌ בקשת החיסור נדחתה.", ephemeral=True)
class TicketLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="בחר את נושא הפנייה שלך...",
        custom_id="regular_ticket_select",
        options=[
            discord.SelectOption(label="תלונה על גאנג", value="תלונה על גאנג", description="הגשת תלונה מסודרת כנגד כנופיה", emoji="💥"),
            discord.SelectOption(label="קבלת רכבי קאסטיום פשע", value="רכבי קאסטיום", description="איסוף או רכישת רכבי פשע מיוחדים", emoji="🚗"),
            discord.SelectOption(label="החזר חפצים", value="החזר חפצים", description="בקשת שחזור או החזר ציוד פשע", emoji="📦"),
            discord.SelectOption(label="אחר", value="אחר", description="פנייה כללית בנושא אחר", emoji="❓")
        ]
    )
    async def select_ticket(self, interaction: discord.Interaction, select: discord.ui.Select):
        topic = select.values
        guild = interaction.guild
        staff_role = guild.get_role(1518269453295685652)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            name=f"🎫-{interaction.user.name}",
            category=interaction.channel.category,
            overwrites=overwrites
        )
        
        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title=f"🎫 פנייה חדשה בנושא: {topic}",
            description=f"שלום {interaction.user.mention},\nצוות השרת קיבל את פנייתך ויגיע לטפל בהקדם.\nלהלן כפתורי ניהול הטיקט הזמינים עבור הצוות המורשה בלבד.",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://background.gif")
        
        await ticket_channel.send(file=file, embed=embed, view=TicketControlView())
        await interaction.response.send_message(f"✅ הטיקט שלך נפתח בהצלחה בערוץ: {ticket_channel.mention}", ephemeral=True)

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518269453295685652
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ אין לך הרשאת צוות לנהל טיקט זה!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🤝 לקיחת הפנייה", style=discord.ButtonStyle.success, custom_id="t_claim")
    async def t_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(f"🔒 הטיקט נלקח לטיפול על ידי איש הצוות: {interaction.user.mention}")
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="🔒 סגירת הטיקט", style=discord.ButtonStyle.danger, custom_id="t_close")
    async def t_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הערוץ ייסגר בעוד כ-5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="➕ הוסף משתמש (ID)", style=discord.ButtonStyle.secondary, custom_id="t_add_user")
    async def t_add_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        class AddUserModal(discord.ui.Modal, title="הוספת משתמש לטיקט"):
            user_id = discord.ui.TextInput(label="מזהה משתמש (User ID)")
            async def on_submit(self, sub_interaction: discord.Interaction):
                try:
                    member = sub_interaction.guild.get_member(int(self.user_id.value))
                    if member:
                        await sub_interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
                        await sub_interaction.response.send_message(f"✅ המשתמש {member.mention} הוסף בהצלחה לטיקט.")
                    else:
                        await sub_interaction.response.send_message("❌ המשתמש לא נמצא בשרת.", ephemeral=True)
                except:
                    await sub_interaction.response.send_message("❌ איידי לא תקין.", ephemeral=True)
        await interaction.response.send_modal(AddUserModal())

    @discord.ui.button(label="✏️ שינוי שם חדר", style=discord.ButtonStyle.primary, custom_id="t_rename")
    async def t_rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        class RenameModal(discord.ui.Modal, title="שינוי שם הערוץ"):
            new_name = discord.ui.TextInput(label="שם חדר חדש")
            async def on_submit(self, sub_interaction: discord.Interaction):
                await sub_interaction.channel.edit(name=self.new_name.value)
                await sub_interaction.response.send_message(f"✅ שם החדר שונה בהצלחה ל: `{self.new_name.value}`")
        await interaction.response.send_modal(RenameModal())
class MafiaTicketLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="בחר סוג הזמנת מאפיה...",
        custom_id="mafia_ticket_select",
        options=[
            discord.SelectOption(label="הזמנת נשקים חמים", value="weapons", description="פתיחת פנייה לרכישת נשק ותחמושת", emoji="🔫"),
            discord.SelectOption(label="הזמנת סמים / חומרים", value="drugs", description="פתיחת פנייה לרכישת סחורה לא חוקית", emoji="🌿"),
            discord.SelectOption(label="אחר / בירור מאפיה", value="other", description="נושאים כלליים הקשורים למאפיה", emoji="💼")
        ]
    )
    async def select_mafia(self, interaction: discord.Interaction, select: discord.ui.Select):
        ticket_type = select.values
        guild = interaction.guild
        mafia_staff = guild.get_role(1518267524050063440)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if mafia_staff:
            overwrites[mafia_staff] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        mafia_channel = await guild.create_text_channel(
            name=f"מאפיה-{interaction.user.name}",
            category=interaction.channel.category,
            overwrites=overwrites
        )
        
        stock_text = "N/A"
        if ticket_type == "weapons":
            stock_text = f"🔫 כמות נשקים נוכחית במלאי המאפיה: **{MAFIA_INVENTORY['weapons']} יחידות**"
        elif ticket_type == "drugs":
            stock_text = f"🌿 כמות סמים נוכחית במלאי המאפיה: **{MAFIA_INVENTORY['drugs']} ק\"ג**"
        else:
            stock_text = "💼 בירור כללי - אין ניהול מלאי ישיר לפנייה זו."

        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title="🕶️ חמ\"ל הזמנות ואספקת מאפיה - Metrolin IL",
            description=f"ברוך הבא {interaction.user.mention},\nפתחתי עבורך פניית מאפיה מאובטחת.\n\n**📊 נתוני מלאי עדכניים בשרת:**\n{stock_text}\n\nצוות המאפיה יגיע לסגור איתך את העסקה מיד.",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url="attachment://background.gif")
        
        await mafia_channel.send(file=file, embed=embed, view=MafiaTicketControlView(ticket_type=ticket_type))
        await interaction.response.send_message(f"✅ הזמנת המאפיה שלך נפתחה בהצלחה בחדר: {mafia_channel.mention}", ephemeral=True)

class MafiaTicketControlView(discord.ui.View):
    def __init__(self, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518267524050063440
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ רק רול צוות מאפיה מורשה לנהל טיקט וסחורה זו!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🤝 קח טיפול", style=discord.ButtonStyle.success, custom_id="m_claim")
    async def m_claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(f"🕶️ צוות המאפיה {interaction.user.mention} לקח את ההזמנה שלך לטיפול אישי ומאובטח.")
        button.disabled = True
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="🔒 סגור עסקה", style=discord.ButtonStyle.danger, custom_id="m_close")
    async def m_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 העסקה נסגרה. חדר הברחות זה יימחק לצמיתות בעוד כ-5 שניות...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @discord.ui.button(label="➕ הוסף שותף (ID)", style=discord.ButtonStyle.secondary, custom_id="m_add")
    async def m_add(self, interaction: discord.Interaction, button: discord.ui.Button):
        class AddMafiaUserModal(discord.ui.Modal, title="הוספת משתמש לעסקה"):
            user_id = discord.ui.TextInput(label="מזהה משתמש (User ID)")
            async def on_submit(self, sub_interaction: discord.Interaction):
                try:
                    member = sub_interaction.guild.get_member(int(self.user_id.value))
                    if member:
                        await sub_interaction.channel.set_permissions(member, read_messages=True, send_messages=True)
                        await sub_interaction.response.send_message(f"✅ שותף פשע {member.mention} צורף בהצלחה לערוץ העסקה.")
                    else:
                        await sub_interaction.response.send_message("❌ המשתמש לא נמצא בשרת.", ephemeral=True)
                except:
                    await sub_interaction.response.send_message("❌ מזהה איידי לא תקין.", ephemeral=True)
        await interaction.response.send_modal(AddMafiaUserModal())

    @discord.ui.button(label="📦 עדכן מלאי (מלאי סחורה)", style=discord.ButtonStyle.primary, custom_id="m_update_stock")
    async def m_update_stock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ticket_type not in ["weapons", "drugs"]:
            await interaction.response.send_message("❌ בטיקט זה אין ניהול מלאי מוגדר וממוחשב.", ephemeral=True)
            return

        class UpdateStockModal(discord.ui.Modal, title="עדכון מלאי סחורה גלובלי"):
            amount = discord.ui.TextInput(label="הכנס כמות חדשה להגדרה במלאי השרת:")
            async def on_submit(self, sub_interaction: discord.Interaction):
                try:
                    new_val = int(self.amount.value)
                    if "weapon" in str(sub_interaction.message.embeds.title).lower() or "נשק" in str(sub_interaction.message.embeds.title):
                        MAFIA_INVENTORY["weapons"] = new_val
                    else:
                        MAFIA_INVENTORY["drugs"] = new_val
                    await sub_interaction.response.send_message(f"📊 המלאי הגלובלי עודכן בהצלחה! כמות חדשה בבסיס הנתונים: **{new_val}**")
                except ValueError:
                    await sub_interaction.response.send_message("❌ נא להזין מספר שלם בלבד!", ephemeral=True)
        
        modal = UpdateStockModal()
        await interaction.response.send_modal(modal)

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_bot(ctx):
    """פקודה להקמת כל הפאנלים המעוצבים בערוצים המתאימים בשרת"""
    ch1 = bot.get_channel(1510196538490622057)
    if ch1:
        f1 = discord.File("background.gif", filename="background.gif")
        em1 = discord.Embed(title="🛡️ פאנל קבלת רולים ואישור כניסה - Metrolin IL", description="עברת ראיון או קבלה לשרת הפשע?\nלחץ על הכפתור הירוק למטה כדי להזין את פרטי הקבלה שלך.\nהטופס יישלח אוטומטית לבדיקת הנהלת השרת לצורך קבלת הדרגות שלך!", color=discord.Color.green())
        em1.set_image(url="attachment://background.gif")
        await ch1.send(file=f1, embed=em1, view=AcceptancePanelLaunchView())

    ch2 = bot.get_channel(1510196539962818652)
    if ch2:
        f2 = discord.File("background.gif", filename="background.gif")
        em2 = discord.Embed(title="🎫 מרכז תמיכה ופניות - Metrolin IL", description="צריך עזרה מצוות השרת, הגשת תלונה או החזר ציוד?\nבחר את קטגוריית הפנייה שלך מתוך התפריט המודרני למטה וערוץ פרטי ייפתח עבורך מיד.", color=discord.Color.blue())
        em2.set_image(url="attachment://background.gif")
        await ch2.send(file=f2, embed=em2, view=TicketLaunchView())

        f4 = discord.File("background.gif", filename="background.gif")
        em4 = discord.Embed(title="🕶️ חמ\"ל אספקת נשקים וסמים - המאפיה הרשמית", description="רוצה לבצע הזמנת נשקים חמים או סחורת סמים עבור הארגון שלך?\nבחר את סוג ההברחה בתפריט הדרופדאון למטה וחדר עסקה סודי ייפתח מול ברוני המאפיה.", color=discord.Color.dark_purple())
        em4.set_image(url="attachment://background.gif")
        await ch2.send(file=f4, embed=em4, view=MafiaTicketLaunchView())

    ch3 = bot.get_channel(1518272315648118864)
    if ch3:
        f3 = discord.File("background.gif", filename="background.gif")
        em3 = discord.Embed(title="📅 מערכת הגשת חיסורים - צוות השרת", description="חבר צוות יקר, במידה ואתה עומד להיעדר מהשרת לפעילות פשע, עליך למלא את טופס החיסור באופן דיגיטלי.\nההיעדרות שלך תועבר לאישור הנהלה ולוג רשמי יתפרסם.", color=discord.Color.gold())
        em3.set_image(url="attachment://background.gif")
        await ch3.send(file=f3, embed=em3, view=AbsenceLaunchView())

    await ctx.send("✅ כל מערכות הפאנלים המודרניות הוקמו ושולחו בהצלחה לערוצים המוגדרים בדיסקורד!")

keep_alive()

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("שגיאה קריטית: ה-DISCORD_TOKEN לא מוגדר בשרת!")
