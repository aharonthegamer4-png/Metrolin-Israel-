import discord
from discord.ext import commands
import os
import asyncio
from keep_alive import keep_alive

# הגדרת אינטנטים מלאים וקידומת פקודות כפי שביקשת
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# משתנה גלובלי לשמירת מלאי המאפיה האמיתי והעדכני בשרת (נשקים וסמים)
MAFIA_INVENTORY = {
    "weapons": 100,
    "drugs": 250
}

# משתנה גלובלי לשמירת מזהה הודעת הפאנל הראשית לצורך עריכה ועדכון בלייב
MAFIA_PANEL_MESSAGE_ID = 0

# מילון גלובלי למעקב אחרי קישורי הזמנה (Invite Tracker)
invites = {}
async def update_bot_status():
    """עדכון הסטטוס של הבוט לפי כמות המשתמשים שבאמת מחוברים כרגע בשרת בלייב"""
    total_members = 0
    online_members = 0
    
    for guild in bot.guilds:
        total_members += guild.member_count
        for member in guild.members:
            # ספירת משתמשים שאינם אופליין ואינם בוטים
            if member.status != discord.Status.offline and not member.bot:
                online_members += 1
                
    status_text = f"{online_members}/{total_members} Active Members ⚡"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))

@bot.event
async def on_ready():
    print(f"Metrolin Bot Online: {bot.user}")
    
    for guild in bot.guilds:
        try:
            invites[guild.id] = await guild.invites()
        except:
            pass
            
    await update_bot_status()
    
    # רישום מחדש של ה-Views הקבועים בבוט בצורה מאובטחת וחוקית לדיסקורד
    bot.add_view(AcceptancePanelLaunchView())
    bot.add_view(AcceptanceActionView())
    bot.add_view(TicketLaunchView())
    bot.add_view(TicketControlView())
    bot.add_view(AbsenceLaunchView())
    bot.add_view(AbsenceApprovalView())
    bot.add_view(MafiaPanelLaunchView())
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
            description=f"**המשתמש המגיש:** {interaction.user.mention}\n**ID:** `{interaction.user.id}`\n\n**👤 הגורם המראיין/מקבל:**\n{self.interviewer.value}\n\n**🛡️ רולים מבוקשים:**\n{self.expected_roles.value}",
            color=discord.Color.orange()
        )
        embed.set_image(url="attachment://background.gif")
        embed.set_footer(text=f"Metrolin IL • מערכת בדיקה")
        
        # יצירת מופע דינמי של הכפתורים עם האיידי של המשתמש הספציפי למניעת שגיאות חילוץ
        await review_channel.send(file=file, embed=embed, view=AcceptanceActionView(target_id=interaction.user.id))
        await interaction.response.send_message("הטופס שלך נשלח בהצלחה לבדיקת הנהלת השרת! אנא המתן לאישור.", ephemeral=True)

class AcceptancePanelLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📝 הגש טופס בדיקה / קבלת רולים", style=discord.ButtonStyle.success, custom_id="launch_acceptance_modal")
    async def launch_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AcceptanceModal())
class AcceptanceActionView(discord.ui.View):
    def __init__(self, target_id: int = 0):
        super().__init__(timeout=None)
        self.target_id = target_id
        # הגדרת ה-Custom IDs בצורה דינמית ומאובטחת שמחזיקה את האיידי בפנים
        if target_id != 0:
            self.kick_user_btn.custom_id = f"ac_kick_{target_id}"
            self.ban_user_btn.custom_id = f"ac_ban_{target_id}"
            self.select_roles_btn.custom_id = f"ac_app_{target_id}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518269453295685652
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ אין לך הרשאה מתאימה (רול הנהלה עליון) להשתמש בכפתור זה!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="👢 תן קיק (Kick)", style=discord.ButtonStyle.danger, row=0)
    async def kick_user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # חילוץ האיידי ישירות משם הכפתור שנלחץ ללא תלות בטקסט של ה-Embed
        c_id = interaction.data['custom_id']
        target_id = int(c_id.split("_")[-1])
        
        target_member = interaction.guild.get_member(target_id)
        if not target_member:
            await interaction.response.send_message("❌ המשתמש לא נמצא בשרת יותר!", ephemeral=True)
            return
        try:
            await target_member.kick(reason="נדחה במערכת בדיקת משתמש עלידי ההנהלה")
            await interaction.response.send_message(f"👢 המשתמש {target_member.name} נזרק מהשרת בהצלחה.", ephemeral=True)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במתן קיק: {e}", ephemeral=True)

    @discord.ui.button(label="🔨 תן באן (Ban)", style=discord.ButtonStyle.danger, row=0)
    async def ban_user_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_id = interaction.data['custom_id']
        target_id = int(c_id.split("_")[-1])
        
        try:
            await interaction.guild.ban(discord.Object(id=target_id), reason="נדחה במערכת בדיקת משתמש")
            await interaction.response.send_message(f"🔨 האיידי `{target_id}` נחסם מהשרת לצמיתות.", ephemeral=True)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
        except Exception as e:
            await interaction.response.send_message(f"❌ שגיאה במתן באן: {e}", ephemeral=True)

    @discord.ui.button(label="🛡️ בחר רולים וסיום (Approve)", style=discord.ButtonStyle.success, row=1)
    async def select_roles_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        c_id = interaction.data['custom_id']
        target_id = int(c_id.split("_")[-1])
        
        target_member = interaction.guild.get_member(target_id)
        if not target_member:
            await interaction.response.send_message("❌ המשתמש לא נמצא בשרת יותר!", ephemeral=True)
            return
            
        # פתיחת תפריט הדרופדאון לבחירת הרולים מתוך חלק 6
        await interaction.response.send_message(f"אנא בחר מהרשימה מטה את הרולים שברצונך לתת ל-{target_member.mention}:", view=RoleSelectionView(target_member, self), ephemeral=True)
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
        await interaction.response.send_message(f"✅ הרולים הוענקו בהצלחה ל-{self.target_member.mention}:\n**{roles_list_str}**\nהטיפול בטופס הסתיים בהצלחה!", ephemeral=True)
        
        # השבתת כפתורי הניהול המקוריים לסגירת הטיפול
        for item in self.original_view.children:
            item.disabled = True
        await interaction.message.edit(view=self.original_view)

class RoleSelectionView(discord.ui.View):
    def __init__(self, target_member: discord.Member, original_view: discord.ui.View):
        super().__init__(timeout=60)
        self.add_item(RoleDropdownSelector(target_member, original_view))
class AbsenceModal(discord.ui.Modal, title="טופס הגשת חיסור - צוות פשע"):
    name = discord.ui.TextInput(label="שם מלא / כינוי בשרת:", placeholder="הכנס את שמך כאן", required=True)
    duration = discord.ui.TextInput(label="לכמה זמן החיסור? (טקסט חופשי)", placeholder="למשל: חצי שעה לסידורים, יומיים, שבוע...", required=True)
    reason = discord.ui.TextInput(label="סיבת החיסור:", placeholder="פרט בקצרה את סיבת החיסור שלך", style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        approval_channel_id = 1518273099194171593
        approval_channel = interaction.guild.get_channel(approval_channel_id)
        
        if not approval_channel:
            await interaction.response.send_message("❌ חדר אישור חיסורים לא נמצא!", ephemeral=True)
            return

        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title="⏳ בקשת חיסור חדשה ממתינת לאישור",
            description=f"**מגיש הבקשה:** {interaction.user.mention}\n**שם המחסיר:** `{self.name.value}`\n**משך החיסור:** `{self.duration.value}`\n\n**סיבת החיסור:**\n{self.reason.value}",
            color=discord.Color.dark_gold()
        )
        embed.set_image(url="attachment://background.gif")
        # פתרון באג החילוץ: שתילת האיידי בתוך ה-Footer של החיסורים
        embed.set_footer(text=f"Absence ID: {interaction.user.id}")
        
        await approval_channel.send(file=file, embed=embed, view=AbsenceApprovalView(member_id=interaction.user.id, name=self.name.value, duration=self.duration.value))
        await interaction.response.send_message("✅ בקשת החיסור שלך נשלחה בהצלחה לבדיקת ההנהלה!", ephemeral=True)

class AbsenceLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📅 מלא טופס חיסור", style=discord.ButtonStyle.blurple, custom_id="launch_absence_modal")
    async def launch_absence(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AcceptanceModal() if False else AbsenceModal())
class AbsenceApprovalView(discord.ui.View):
    def __init__(self, member_id: int = 0, name: str = "", duration: str = ""):
        super().__init__(timeout=None)
        self.member_id = member_id
        self.name = name
        self.duration = duration

    def parse_absence_embed(self, message: discord.Message):
        """פונקציית עזר משודרגת לחילוץ מושלם של נתוני החיסור החופשיים מתוך ה-Embed וה-Footer"""
        member_id = 0
        name = "לא ידוע"
        duration = "לא מוגדר"
        try:
            if message.embeds:
                if message.embeds[0].footer and message.embeds[0].footer.text:
                    f_text = message.embeds[0].footer.text
                    if "Absence ID:" in f_text:
                        member_id = int(f_text.split("Absence ID:")[-1].strip())
                        
                description = message.embeds[0].description
                for line in description.split("\n"):
                    if "שם המחסיר:" in line:
                        name = line.split("`")[1].strip()
                    elif "משך החיסור:" in line:
                        duration = line.split("`")[1].strip()
        except Exception as e:
            print(f"Error parsing absence embed: {e}")
        return member_id, name, duration

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        required_role_id = 1518269453295685652
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ רק דרגת הנהלה עליונה יכולה לאשר או לדחות חיסורים!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ אשר חיסור", style=discord.ButtonStyle.success, custom_id="abs_approve_fixed_btn")
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        public_log_id = 1510196538490622058
        public_channel = interaction.guild.get_channel(public_log_id)
        
        m_id, m_name, m_duration = self.parse_absence_embed(interaction.message)
        final_id = m_id if m_id != 0 else self.member_id
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        if public_channel:
            file = discord.File("background.gif", filename="background.gif")
            embed = discord.Embed(
                title="📢 עדכון סטטוס חיסורי צוות פשע",
                description=f"**איש הצוות:** <@{final_id}>\n**שם הצוות:** `{m_name if m_name != 'לא ידוע' else self.name}`\n**זמן החיסור:** `{m_duration if m_duration != 'לא מוגדר' else self.duration}`\n\n**סטטוס:** אושר באופן רשמי ע\"י ההנהלה ✅",
                color=discord.Color.green()
            )
            embed.set_image(url="attachment://background.gif")
            await public_channel.send(file=file, embed=embed)
            
        await interaction.response.send_message("✅ החיסור אושר ופורסם בלוג הציבורי בהצלחה.", ephemeral=True)

    @discord.ui.button(label="❌ דחה חיסור", style=discord.ButtonStyle.danger, custom_id="abs_deny_fixed_btn")
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        m_id, _, _ = self.parse_absence_embed(interaction.message)
        final_id = m_id if m_id != 0 else self.member_id
        
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)
        
        if final_id != 0:
            try:
                user = await bot.fetch_user(final_id)
                await user.send("❌ בקשת החיסור שהגשת בשרת Metrolin IL נדחתה על ידי ההנהלה.")
            except:
                pass
        await interaction.response.send_message("❌ בקשת החיסור נדחתה והודעה נשלחה למשתמש.", ephemeral=True)
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
        topic = select.values[0] if isinstance(select.values, list) else select.values
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
            description=f"שלום {interaction.user.mention} ,\nצוות השרת קיבל את פנייתך ויגיע לטפל בהקדם.\nלהלן כפתורי ניהול הטיקט הזמינים עבור הצוות המורשה בלבד.",
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

    @discord.ui.button(label="🔒 סגור טיקט (עם סיבה)", style=discord.ButtonStyle.danger, custom_id="t_close_with_reason")
    async def t_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        class CloseTicketModal(discord.ui.Modal, title="סגירה וארכוב כרטיס תמיכה 🔒"):
            summary = discord.ui.TextInput(label="סיכום הטיפול וההתרחשות בטיקט *", placeholder="...פרטי המקרה", style=discord.TextStyle.paragraph, required=True)
            answered = discord.ui.TextInput(label="האם הטיקט קיבל מענה מלא? (כן/לא) *", placeholder="כן / לא", max_length=5, required=True)

            async def on_submit(self, sub_interaction: discord.Interaction):
                log_channel_id = 1510196539962818653
                log_channel = sub_interaction.guild.get_channel(log_channel_id)
                
                await sub_interaction.response.send_message("🔒 הטיקט תועד בארכיון בהצלחה. הערוץ ייסגר כעת...")
                
                if log_channel:
                    file = discord.File("background.gif", filename="background.gif")
                    embed = discord.Embed(
                        title="🗂️ לוג סגירת טיקט - Metrolin IL",
                        description=f"**שם החדר שנסגר:** `{sub_interaction.channel.name}`\n**נסגר על ידי:** {sub_interaction.user.mention}\n\n**📊 סיכום הטיפול וההתרחשות:**\n{self.summary.value}\n\n**❓ קיבל מענה מלא:** `{self.answered.value}`",
                        color=discord.Color.red()
                    )
                    embed.set_image(url="attachment://background.gif")
                    await log_channel.send(file=file, embed=embed)
                
                await asyncio.sleep(3)
                await sub_interaction.channel.delete()

        await interaction.response.send_modal(CloseTicketModal())
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
        chosen_value = select.values if isinstance(select.values, list) else select.values
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
        
        stock_text = "💼 בירור כללי - אין ניהול מלאי ישיר לפנייה זו."
        if chosen_value == "weapons":
            stock_text = f"🔫 כמות נשקים נוכחית במלאי המאפיה: **{MAFIA_INVENTORY['weapons']} יחידות**"
        elif chosen_value == "drugs":
            stock_text = f"🌿 כמות סמים נוכחית במלאי המאפיה: **{MAFIA_INVENTORY['drugs']} ק\"ג**"

        file = discord.File("background.gif", filename="background.gif")
        embed = discord.Embed(
            title="🕶️ חמ\"ל הזמנות ואספקת מאפיה - Metrolin IL",
            description=f"ברוך הבא {interaction.user.mention},\nפתחתי עבורך פניית מאפיה מאובטחת.\n\n**📊 נתוני מלאי עדכניים בשרת:**\n{stock_text}\n\nצוות המאפיה יגיע לסגור איתך את העסקה מיד.",
            color=discord.Color.dark_purple()
        )
        embed.set_image(url="attachment://background.gif")
        
        await mafia_channel.send(file=file, embed=embed, view=MafiaTicketControlView(ticket_type=str(chosen_value)))
        await interaction.response.send_message(f"✅ הזמנת המאפיה שלך נפתחה בהצלחה בחדר: {mafia_channel.mention}", ephemeral=True)
class MafiaPanelLaunchView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="בחר סוג הזמנת מאפיה...",
        custom_id="mafia_ticket_select_v2",
        options=[
            discord.SelectOption(label="הזמנת נשקים חמים", value="weapons", description="פתיחת פנייה לרכישת נשק ותחמושת", emoji="🔫"),
            discord.SelectOption(label="הזמנת סמים / חומרים", value="drugs", description="פתיחת פנייה לרכישת סחורה לא חוקית", emoji="🌿"),
            discord.SelectOption(label="אחר / בירור מאפיה", value="other", description="נושאים כלליים הקשורים למאפיה", emoji="💼")
        ],
        row=0
    )
    async def select_mafia_v2(self, interaction: discord.Interaction, select: discord.ui.Select):
        launcher = MafiaTicketLaunchView()
        await launcher.select_mafia(interaction, select)

    @discord.ui.button(label="⚙️ ניהול ועדכון מלאי (צוות בלבד)", style=discord.ButtonStyle.secondary, custom_id="mafia_owner_manage_stock", row=1)
    async def manage_stock_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        required_role_id = 1518267524050063440
        if required_role_id not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ אין לך את רול צוות המאפיה הנדרש לניהול החנות!", ephemeral=True)
            return

        class GlobalStockModal(discord.ui.Modal, title="ניהול מלאי חנות המאפיה"):
            weapons_input = discord.ui.TextInput(label="כמות נשקים חמים חדשה במלאי:", default=str(MAFIA_INVENTORY["weapons"]), required=True)
            drugs_input = discord.ui.TextInput(label="כמות סמים / חומרים חדשה במלאי:", default=str(MAFIA_INVENTORY["drugs"]), required=True)

            async def on_submit(self, sub_interaction: discord.Interaction):
                try:
                    w_val = int(self.weapons_input.value)
                    doc_val = int(self.drugs_input.value)
                    MAFIA_INVENTORY["weapons"] = w_val
                    MAFIA_INVENTORY["drugs"] = doc_val
                    
                    global MAFIA_PANEL_MESSAGE_ID
                    if MAFIA_PANEL_MESSAGE_ID != 0:
                        try:
                            main_msg = await sub_interaction.channel.fetch_message(MAFIA_PANEL_MESSAGE_ID)
                            if main_msg and main_msg.embeds:
                                main_embed = main_msg.embeds
                                main_embed.description = (
                                    "רוצה לבצע הזמנת נשקים חמים או סחורת סמים עבור הארגון שלך?\n"
                                    "בחר את סוג ההברחה בתפריט הדרופדאון למטה וחדר עסקה סודי ייפתח מול ברוני המאפיה.\n\n"
                                    f"**📊 מלאי עדכני בחנות המאפיה:**\n"
                                    f"🔫 נשקים חמים: **{w_val} יחידות**\n"
                                    f"🌿 סמים וחומרים: **{doc_val} ק\"ג**"
                                )
                                await main_msg.edit(embed=main_embed)
                        except Exception as e:
                            print(f"Could not update main shop panel embed: {e}")

                    await sub_interaction.response.send_message(f"✅ מלאי החנות עודכן בהצלחה!\n🔫 נשקים: **{w_val}** | 🌿 סמים: **{doc_val}**", ephemeral=True)
                except ValueError:
                    await sub_interaction.response.send_message("❌ נא להזין מספרים שלמים בלבד!", ephemeral=True)

        await interaction.response.send_modal(GlobalStockModal())
class MafiaTicketControlView(discord.ui.View):
    def __init__(self, ticket_type: str = ""):
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

    @discord.ui.button(label="🔒 סגור עסקה (עם סיבה)", style=discord.ButtonStyle.danger, custom_id="m_close_with_reason")
    async def m_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        class CloseMafiaModal(discord.ui.Modal, title="סגירה וארכוב כרטיס תמיכה 🔒"):
            summary = discord.ui.TextInput(label="סיכום הטיפול וההתרחשות בטיקט *", placeholder="פרטי המקרה, מה נקנה וכמה שולם...", style=discord.TextStyle.paragraph, required=True)
            answered = discord.ui.TextInput(label="האם הטיקט קיבל מענה מלא? (כן/לא) *", placeholder="כן / לא", max_length=5, required=True)

            async def on_submit(self, sub_interaction: discord.Interaction):
                log_channel_id = 1510196539962818653
                log_channel = sub_interaction.guild.get_channel(log_channel_id)
                
                await sub_interaction.response.send_message("🔒 העסקה תועדה בארכיון. חדר ההברחות ייסגר כעת...")
                
                if log_channel:
                    file = discord.File("background.gif", filename="background.gif")
                    embed = discord.Embed(
                        title="🕶️ לוג סגירת עסקת מאפיה - Metrolin IL",
                        description=f"**חדר עסקה:** `{sub_interaction.channel.name}`\n**נסגר על ידי:** {sub_interaction.user.mention}\n\n**📊 סיכום הטיפול והעסקה:**\n{self.summary.value}\n\n**❓ קיבל מענה מלא:** `{self.answered.value}`",
                        color=discord.Color.purple()
                    )
                    embed.set_image(url="attachment://background.gif")
                    await log_channel.send(file=file, embed=embed)
                
                await asyncio.sleep(3)
                await sub_interaction.channel.delete()

        await interaction.response.send_modal(CloseMafiaModal())

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
        t_type = self.ticket_type
        if not t_type and interaction.message.embeds:
            embed_desc = interaction.message.embeds.description
            if "נשק" in embed_desc or "weapons" in embed_desc:
                t_type = "weapons"
            elif "סמים" in embed_desc or "drugs" in embed_desc:
                t_type = "drugs"

        if t_type not in ["weapons", "drugs"]:
            await interaction.response.send_message("❌ בטיקט זה אין ניהול מלאי מוגדר וממוחשב.", ephemeral=True)
            return

        class UpdateStockModal(discord.ui.Modal, title="עדכון מלאי סחורה"):
            amount = discord.ui.TextInput(label="הכנס כמות חדשה להגדרה במלאי השרת:")
            async def on_submit(self, sub_interaction: discord.Interaction):
                try:
                    new_val = int(self.amount.value)
                    original_message = sub_interaction.message
                    original_embed = original_message.embeds
                    
                    if modal.ticket_kind == "weapons":
                        MAFIA_INVENTORY["weapons"] = new_val
                        new_stock_text = f"🔫 כמות נשקים נוכחית במלאי המאפיה: **{new_val} יחידות**"
                        msg = f"📊 מלאי הנשקים הגלובלי עודכן בהצלחה! כמות חדשה: **{new_val} יחידות**"
                    else:
                        MAFIA_INVENTORY["drugs"] = new_val
                        new_stock_text = f"🌿 כמות סמים נוכחית במלאי המאפיה: **{new_val} ק\"ג**"
                        msg = f"📊 מלאי הסמים הגלובלי עודכן בהצלחה! כמות חדשה: **{new_val} ק\"ג**"
                    
                    lines = original_embed.description.split("\n")
                    for i, line in enumerate(lines):
                        if "כמות נשקים נוכחית" in line or "כמות סמים נוכחית" in line or "ניהול מלאי ישיר" in line or "נתוני מלאי עדכניים" in line:
                            lines[i] = new_stock_text
                            break
                    
                    original_embed.description = "\n".join(lines)
                    await original_message.edit(embed=original_embed)
                    await sub_interaction.response.send_message(msg)
                except ValueError:
                    await sub_interaction.response.send_message("❌ נא להזין מספר שלם בלבד!", ephemeral=True)
        
        modal = UpdateStockModal()
        modal.ticket_kind = t_type
        await interaction.response.send_modal(modal)
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_verification(ctx):
    file = discord.File("background.gif", filename="background.gif")
    embed = discord.Embed(title="🛡️ פאנל קבלת רולים ואישור כניסה - Metrolin IL", description="עברת ראיון או קבלה לשרת הפשע?\nלחץ על הכפתור הירוק למטה כדי להזין את פרטי הקבלה שלך.\nהטופס יישלח אוטומטית לבדיקת הנהלת השרת לצורך קבלת הדרגות שלך!", color=discord.Color.green())
    embed.set_image(url="attachment://background.gif")
    await ctx.send(file=file, embed=embed, view=AcceptancePanelLaunchView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    file = discord.File("background.gif", filename="background.gif")
    embed = discord.Embed(title="🎫 מרכז תמיכה ופניות - Metrolin IL", description="צריך עזרה מצוות השרת, הגשת תלונה או החזר ציוד?\nבחר את קטגוריית הפנייה שלך מתוך התפריט המודרני למטה וערוץ פרטי ייפתח עבורך מיד.", color=discord.Color.blue())
    embed.set_image(url="attachment://background.gif")
    await ctx.send(file=file, embed=embed, view=TicketLaunchView())
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_mafia(ctx):
    global MAFIA_PANEL_MESSAGE_ID
    file = discord.File("background.gif", filename="background.gif")
    embed = discord.Embed(
        title="🕶️ חמ\"ל אספקת נשקים וסמים - המאפיה הרשמית", 
        description=(
            "רוצה לבצע הזמנת נשקים חמים או סחורת סמים עבור הארגון שלך?\n"
            "בחר את סוג ההברחה בתפריט הדרופדאון למטה וחדר עסקה סודי ייפתח מול ברוני המאפיה.\n\n"
            f"**📊 מלאי עדכני בחנות המאפיה:**\n"
            f"🔫 נשקים חמים: **{MAFIA_INVENTORY['weapons']} יחידות**\n"
            f"🌿 סמים וחומרים: **{MAFIA_INVENTORY['drugs']} ק\"ג**"
        ), 
        color=discord.Color.dark_purple()
    )
    embed.set_image(url="attachment://background.gif")
    
    panel_msg = await ctx.send(file=file, embed=embed, view=MafiaPanelLaunchView())
    MAFIA_PANEL_MESSAGE_ID = panel_msg.id
    await ctx.message.delete()

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_absence(ctx):
    file = discord.File("background.gif", filename="background.gif")
    embed = discord.Embed(title="📅 מערכת הגשת חיסורים - צוות השרת", description="חבר צוות יקר, במידה ואתה עומד להיעדר מהשרת לפעילות פשע, עליך למלא את טופס החיסור באופן דיגיטלי.\nההיעדרות שלך תועבר לאישור הנהלה ולוג רשמי יתפרסם.", color=discord.Color.gold())
    embed.set_image(url="attachment://background.gif")
    await ctx.send(file=file, embed=embed, view=AbsenceLaunchView())
    await ctx.message.delete()

keep_alive()

token = os.environ.get("DISCORD_TOKEN")
if token:
    bot.run(token)
else:
    print("שגיאה קריטית: ה-DISCORD_TOKEN לא מוגדר בהגדרות שרת ה-Render!")
