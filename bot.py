"""Permanent voice channels; run one process per bot token."""
from __future__ import annotations

import asyncio
import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Literal

import discord
from discord import app_commands
from dotenv import dotenv_values

MAX_BATCH = 100
MAX_FILE_BYTES = 64 * 1024
GUILD_CHANNEL_LIMIT = 500
CATEGORY_CHANNEL_LIMIT = 50
JOB_SECONDS = 12 * 60
LOG = logging.getLogger("voice_creator")


def validate_name(value: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 100:
        raise ValueError("ชื่อห้องต้องยาว 1–100 ตัวอักษร")
    if any(unicodedata.category(c) == "Cc" for c in value):
        raise ValueError("ชื่อห้องต้องไม่มีอักขระควบคุม")
    return value


def parse_names(data: bytes) -> list[str]:
    if len(data) > MAX_FILE_BYTES:
        raise ValueError("ไฟล์ต้องไม่เกิน 64 KiB")
    try:
        lines = data.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise ValueError("กรุณาบันทึกไฟล์เป็น UTF-8 หรือ UTF-8 with BOM") from exc
    names = [validate_name(line) for line in lines if line.strip()]
    if not 1 <= len(names) <= MAX_BATCH:
        raise ValueError(f"ไฟล์ต้องมีชื่อห้อง 1–{MAX_BATCH} บรรทัดที่ไม่ว่าง")
    return names


def text_name(value: str) -> str:
    return validate_name(re.sub(r"\s+", "-", validate_name(value)).lower())


def numbered_names(channels, prefix: str, amount: int, channel_type: str = "voice") -> list[str]:
    prefix = validate_name(prefix)
    if channel_type == "text":
        prefix = text_name(prefix)
    if not 1 <= amount <= MAX_BATCH:
        raise ValueError(f"จำนวนต้องอยู่ระหว่าง 1–{MAX_BATCH}")
    separator = "-" if channel_type == "text" else " "
    suffix_separator = r"[-\s]+" if channel_type == "text" else r"\s+"
    pattern = re.compile(rf"^{re.escape(prefix)}{suffix_separator}([0-9]+)$", re.IGNORECASE)
    channel_class = discord.TextChannel if channel_type == "text" else discord.VoiceChannel
    highest = 0
    for channel in channels:
        if isinstance(channel, channel_class):
            match = pattern.fullmatch(channel.name)
            if match:
                # Avoid converting arbitrarily large user-created numeric suffixes.
                digits = match[1].lstrip("0") or "0"
                if len(digits) > 12:
                    raise ValueError("พบเลขท้ายชื่อห้องที่ใหญ่เกินไป กรุณาใช้ prefix อื่น")
                highest = max(highest, int(digits))
    return [validate_name(f"{prefix}{separator}{i}") for i in range(highest + 1, highest + amount + 1)]


class VoiceCreator(discord.Client):
    def __init__(self, test_guild_id: int | None = None):
        super().__init__(intents=discord.Intents.default(),
                         allowed_mentions=discord.AllowedMentions.none())
        self.tree = app_commands.CommandTree(self)
        self.test_guild_id = test_guild_id
        self.busy: set[int] = set()

    async def setup_hook(self):
        if self.test_guild_id:
            guild = discord.Object(id=self.test_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        LOG.info("Synced %s commands", len(synced))

    async def on_ready(self):
        LOG.info("Connected as %s (%s)", self.user, self.user.id)


bot = VoiceCreator()


async def report(interaction: discord.Interaction, content: str):
    try:
        await interaction.edit_original_response(content=content,
                                                  allowed_mentions=discord.AllowedMentions.none())
    except discord.HTTPException:
        LOG.warning("Could not update interaction for guild %s", interaction.guild_id)


async def run_job(interaction: discord.Interaction, category, *, prefix=None,
                  amount=None, attachment=None, category_name=None, channel_type="voice"):
    if channel_type not in ("voice", "text"):
        raise ValueError("channel_type ต้องเป็น voice หรือ text")
    guild = interaction.guild
    if guild is None or not isinstance(interaction.user, discord.Member):
        raise ValueError("ใช้คำสั่งนี้ในเซิร์ฟเวอร์เท่านั้น")
    # Explicit server permission, in addition to the command's invocation-channel check.
    if not interaction.user.guild_permissions.manage_channels:
        raise ValueError("คุณต้องมีสิทธิ์ Manage Channels ระดับเซิร์ฟเวอร์")
    if category is not None and category_name is not None:
        raise ValueError("เลือก category หรือ category_name อย่างใดอย่างหนึ่งเท่านั้น")
    if category_name is not None:
        category_name = validate_name(category_name)
    if category and (category.guild.id != guild.id or
                     not category.permissions_for(interaction.user).manage_channels):
        raise ValueError("คุณไม่มีสิทธิ์ Manage Channels ใน Category นี้")
    if guild.id in bot.busy:
        raise ValueError("มีงานสร้างห้องกำลังทำในเซิร์ฟเวอร์นี้ กรุณารอให้เสร็จ")
    bot.busy.add(guild.id)
    try:
        await interaction.response.defer(ephemeral=True, thinking=True)
        started = time.monotonic()
        channels = await guild.fetch_channels()
        if category:
            category = next((c for c in channels if c.id == category.id and
                             isinstance(c, discord.CategoryChannel)), None)
            if category is None:
                raise ValueError("Category ถูกลบหรือไม่พบแล้ว")
        me = guild.me
        if me is None:
            raise ValueError("ไม่พบข้อมูลสมาชิกของบอท กรุณาลองใหม่")
        permissions = category.permissions_for(me) if category else me.guild_permissions
        if not permissions.manage_channels or not permissions.view_channel:
            raise ValueError("บอทต้องมี Manage Channels และ View Channels ในตำแหน่งปลายทาง")
        if attachment:
            if not attachment.filename.lower().endswith(".txt"):
                raise ValueError("รับเฉพาะไฟล์ .txt")
            if attachment.size > MAX_FILE_BYTES:
                raise ValueError("ไฟล์ต้องไม่เกิน 64 KiB")
            names = parse_names(await attachment.read())
            if channel_type == "text":
                names = [text_name(name) for name in names]
        else:
            names = numbered_names(channels, prefix, amount, channel_type)
        if category_name is not None and len(names) > CATEGORY_CHANNEL_LIMIT:
            raise ValueError("Category ใหม่รับได้สูงสุด 50 ห้อง กรุณาลดจำนวนหรือแบ่งคำสั่ง")
        if len(channels) + len(names) + (category_name is not None) > GUILD_CHANNEL_LIMIT:
            raise ValueError("จำนวนห้องรวมจะเกินเพดานเซิร์ฟเวอร์ 500 ช่อง (รวม Category)")
        if category and sum(c.category_id == category.id for c in channels) + len(names) > CATEGORY_CHANNEL_LIMIT:
            raise ValueError("Category มีพื้นที่ไม่พอ: สูงสุด 50 ช่องต่อ Category")
        if category_name is not None:
            if any(isinstance(c, discord.CategoryChannel) and
                   c.name.casefold() == category_name.casefold() for c in channels):
                raise ValueError("มี Category ชื่อนี้แล้ว กรุณาเลือกผ่าน category หรือใช้ชื่อใหม่")
            # All room/file validation is complete before creating the category.
            try:
                category = await asyncio.wait_for(guild.create_category(
                    category_name,
                    reason=f"Bulk voice creation requested by user {interaction.user.id}"),
                    timeout=max(0.01, JOB_SECONDS - (time.monotonic() - started)))
            except asyncio.TimeoutError as exc:
                raise ValueError("หมดเวลาสร้าง Category: อาจสร้างแล้ว โปรดตรวจ Discord ก่อนสั่งซ้ำ") from exc
        create_channel = guild.create_text_channel if channel_type == "text" else guild.create_voice_channel
        await report(interaction, f"กำลังสร้าง {len(names)} ห้อง ({channel_type})…")
        created = 0
        failed = 0
        stop_reason = ""
        last_update = time.monotonic()
        for name in names:
            remaining = JOB_SECONDS - (time.monotonic() - started)
            if remaining <= 0:
                stop_reason = "ถึงเวลาสูงสุดของงาน"
                break
            try:
                # Sequential. discord.py handles server-provided rate limits.
                await asyncio.wait_for(create_channel(
                    name, category=category,
                    reason=f"Bulk {channel_type} creation requested by user {interaction.user.id}"),
                    timeout=remaining)
                created += 1
                LOG.info("Created %s channel in guild %s (%s/%s)", channel_type, guild.id, created, len(names))
            except asyncio.TimeoutError:
                failed += 1
                stop_reason = "หมดเวลารอ Discord: ห้องล่าสุดอาจถูกสร้างแล้ว โปรดตรวจห้องจริงก่อนสั่งซ้ำ"
                break
            except discord.HTTPException as exc:
                failed += 1
                # Stop on any HTTP failure: avoid ambiguous retries or repeated failures.
                stop_reason = f"Discord ปฏิเสธ/มีปัญหา (HTTP {exc.status}, code {exc.code}); ตรวจสิทธิ์และจำนวนห้อง"
                LOG.warning("Creation stopped: guild=%s status=%s code=%s", guild.id, exc.status, exc.code)
                break
            if time.monotonic() - last_update >= 5:
                await report(interaction, f"สร้างแล้ว {created}/{len(names)} ห้อง…")
                last_update = time.monotonic()
        skipped = len(names) - created - failed
        result = f"เสร็จสิ้น: สำเร็จ {created} | ล้มเหลว/ไม่ยืนยัน {failed} | ยังไม่ได้ทำ {skipped}"
        if stop_reason:
            result += f"\n{stop_reason}"
        result += "\nห้องที่สร้างสำเร็จเป็นห้องถาวร ไม่มีการลบหรือ rollback อัตโนมัติ"
        if category_name is not None:
            result += "\nสร้าง Category ใหม่แล้ว และจะเก็บไว้แม้งานสร้างห้องหยุดกลางทาง"
        LOG.info("Result guild=%s created=%s failed=%s skipped=%s", guild.id, created, failed, skipped)
        await report(interaction, result)
    finally:
        bot.busy.discard(guild.id)


@bot.tree.command(name="create", description="สร้างห้องเสียงหรือข้อความถาวรเรียงเลขต่อจากห้องเดิม")
@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.describe(amount="จำนวน 1–100 ห้อง", name="ชื่อหน้าห้อง เช่น Room", category="Category ที่มีอยู่", category_name="ชื่อ Category ใหม่ (ไม่ใช้ร่วมกับ category; สูงสุด 50 ห้อง)")
async def create(interaction: discord.Interaction, amount: app_commands.Range[int, 1, MAX_BATCH],
                 name: str, category: discord.CategoryChannel | None = None,
                 category_name: str | None = None,
                 channel_type: Literal["voice", "text"] = "voice"):
    await run_job(interaction, category, prefix=name, amount=amount, category_name=category_name, channel_type=channel_type)


@bot.tree.command(name="createfile", description="สร้างห้องเสียงหรือข้อความถาวรจากไฟล์ TXT บรรทัดละชื่อ")
@app_commands.guild_only()
@app_commands.default_permissions(manage_channels=True)
@app_commands.checks.has_permissions(manage_channels=True)
@app_commands.describe(file="ไฟล์ TXT UTF-8 ไม่เกิน 64 KiB และ 100 ชื่อ", category="Category ที่มีอยู่", category_name="ชื่อ Category ใหม่ (ไม่ใช้ร่วมกับ category; สูงสุด 50 ห้อง)")
async def createfile(interaction: discord.Interaction, file: discord.Attachment,
                     category: discord.CategoryChannel | None = None,
                     category_name: str | None = None,
                     channel_type: Literal["voice", "text"] = "voice"):
    await run_job(interaction, category, attachment=file, category_name=category_name, channel_type=channel_type)


@bot.tree.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    original = getattr(error, "original", error)
    if isinstance(original, ValueError):
        message = str(original)
    elif isinstance(error, app_commands.MissingPermissions):
        message = "คุณต้องมีสิทธิ์ Manage Channels เพื่อใช้คำสั่งนี้"
    elif isinstance(error, app_commands.NoPrivateMessage):
        message = "ใช้คำสั่งนี้ในเซิร์ฟเวอร์เท่านั้น"
    elif isinstance(original, discord.HTTPException):
        message = f"ติดต่อ Discord ไม่สำเร็จ (HTTP {original.status}, code {original.code}) กรุณาลองใหม่ภายหลัง"
    else:
        message = "เกิดข้อผิดพลาดภายใน โปรดตรวจจำนวนห้องจริงก่อนสั่งซ้ำและดู log ของบอท"
        # Do not log arbitrary exception text, attachments or credentials.
        LOG.error("Unhandled command error type=%s guild=%s", type(original).__name__, interaction.guild_id)
    if interaction.response.is_done():
        await report(interaction, message)
    else:
        try:
            await interaction.response.send_message(message, ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            LOG.warning("Could not send command error")


def main():
    # Read credentials ONLY from the project's .env, independent of working directory.
    config = dotenv_values(Path(__file__).resolve().with_name(".env"), interpolate=False)
    token = (config.get("DISCORD_TOKEN") or "").strip()
    if not token or token == "PUT_YOUR_BOT_TOKEN_HERE":
        raise SystemExit("กรุณาสร้าง .env แล้วใส่ DISCORD_TOKEN ของบอท")
    guild_id = (config.get("TEST_GUILD_ID") or "").strip()
    if guild_id and (not guild_id.isdecimal() or int(guild_id) <= 0):
        raise SystemExit("TEST_GUILD_ID ต้องเป็นเลข ID เซิร์ฟเวอร์ หรือเว้นว่าง")
    bot.test_guild_id = int(guild_id) if guild_id else None
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        bot.run(token, log_handler=None)
    except discord.LoginFailure:
        raise SystemExit("Token ไม่ถูกต้อง กรุณา Reset Token แล้วแก้ .env") from None


if __name__ == "__main__":
    main()
