#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# (c) Shrimadhav U K | gautamajay52 | Priiiiyo

import asyncio
import logging
import os
import re
import io
import sys
import time
import pyprog
import requests
import psutil
import aria2p

from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from tobrot import (
    ARIA_TWO_STARTED_PORT,
    AUTH_CHANNEL,
    CUSTOM_FILE_NAME,
    DOWNLOAD_LOCATION,
    EDIT_SLEEP_TIME_OUT,
    LOGGER,
    MAX_TIME_TO_WAIT_FOR_TORRENTS_TO_START,
)
from tobrot.helper_funcs.create_compressed_archive import (
    create_archive,
    get_base_name,
    unzip_me,
)
from tobrot.helper_funcs.extract_link_from_message import extract_link
from tobrot.helper_funcs.upload_to_tg import upload_to_gdrive, upload_to_tg
from tobrot.helper_funcs.direct_link_generator import direct_link_generator
from tobrot.helper_funcs.exceptions import DirectDownloadLinkException
sys.setrecursionlimit(10 ** 4)

def KopyasizListe(string):
    kopyasiz = list(string.split(","))
    kopyasiz = list(dict.fromkeys(kopyasiz))
    return kopyasiz

def Virgullustring(string):
    string = string.replace("\n\n",",")
    string = string.replace("\n",",")
    string = string.replace(",,",",")
    string = string.rstrip(',')
    string = string.lstrip(',')
    return string

tracker_urlsss = [
    "https://raw.githubusercontent.com/XIU2/TrackersListCollection/master/all.txt",
    "https://raw.githubusercontent.com/ngosang/trackerslist/master/trackers_all.txt",
    "https://raw.githubusercontent.com/DeSireFire/animeTrackerList/master/AT_all.txt"
    ]
tumtorrenttrackerstringi = ""
sonstringtrckr = ""
for tracker_urlss in tracker_urlsss:
    response = requests.get(tracker_urlss)
    response.encoding = "utf-8"
    tumtorrenttrackerstringi += "\n"
    tumtorrenttrackerstringi += response.text
trackerlistemiz = KopyasizListe(Virgullustring(tumtorrenttrackerstringi))
sonstringtrckr = ','.join(trackerlistemiz)
# LOGGER.info(sonstringtrckr)
# trackelreri alıyoz dinamik olarak
async def aria_start():
    global sonstringtrckr
    aria2_daemon_start_cmd = []
    # start the daemon, aria2c command

async def aria_start():
    aria2_daemon_start_cmd = [
        'aria2c',
        '--allow-overwrite=true',
        '--daemon=true',
        '--enable-rpc',
        '--follow-torrent=mem',
        '--max-connection-per-server=10',
        '--min-split-size=10M',
        '--rpc-listen-all=false',
        f"--rpc-listen-port={ARIA_TWO_STARTED_PORT}",
        '--rpc-max-request-size=1024M',
        '--seed-time=0',
        '--max-overall-upload-limit=1K',
        '--split=10',
        f"--bt-stop-timeout={MAX_TIME_TO_WAIT_FOR_TORRENTS_TO_START}",
    ]

    #
    LOGGER.info(aria2_daemon_start_cmd)
    #
    process = await asyncio.create_subprocess_exec(
        *aria2_daemon_start_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    LOGGER.info(stdout)
    LOGGER.info(stderr)
    return aria2p.API(
        aria2p.Client(
            host="http://localhost", port=ARIA_TWO_STARTED_PORT, secret=""
        )
    )


def add_magnet(aria_instance, magnetic_link, c_file_name):
    options = None
    # if c_file_name is not None:
    #     options = {
    #         "dir": c_file_name
    #     }
    try:
        download = aria_instance.add_magnet(magnetic_link, options=options)
    except Exception as e:
        return (
            False,
            "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help",
        )
    else:
        return True, "" + download.gid + ""


def add_torrent(aria_instance, torrent_file_path):
    if torrent_file_path is None:
        return (
            False,
            "**FAILED** \n"
            + str(e)
            + " \nsomething wrongings when trying to add <u>TORRENT</u> file",
        )
    if os.path.exists(torrent_file_path):
        # Add Torrent Into Queue
        try:
            download = aria_instance.add_torrent(
                torrent_file_path, uris=None, options=None, position=None
            )
        except Exception as e:
            return (
                False,
                "**FAILED** \n"
                + str(e)
                + " \nPlease do not send SLOW links. Read /help",
            )
        else:
            return True, "" + download.gid + ""
    else:
        return False, "**FAILED** \nPlease try other sources to get workable link"


def add_url(aria_instance, text_url, c_file_name):
    options = None
    # if c_file_name is not None:
    #     options = {
    #         "dir": c_file_name
    #     }
    #
    # or "cloud.mail.ru" in text_url \  doesnt work.
    # or "github.com" in text_url \   doesnt work.
    #
    if "zippyshare.com" in text_url \
        or "osdn.net" in text_url \
        or "mediafire.com" in text_url \
        or "cloud.mail.ru" in text_url \
        or "github.com" in text_url \
        or "yadi.sk" in text_url  \
        or "racaty.net" in text_url:
            try:
                urisitring = direct_link_generator(text_url)
                uris = [urisitring]
            except DirectDownloadLinkException as e:
                LOGGER.info(f'{text_url}: {e}')
    else:
        uris = [text_url]
    # Add URL Into Queue
    try:
        download = aria_instance.add_uris(uris, options=options)
    except Exception as e:
        return (
            False,
            "**FAILED** \n" + str(e) + " \nPlease do not send SLOW links. Read /help",
        )
    else:
        return True, "" + download.gid + ""


async def call_apropriate_function(
    aria_instance,
    incoming_link,
    c_file_name,
    sent_message_to_update_tg_p,
    is_zip,
    cstom_file_name,
    is_cloud,
    is_unzip,
    user_message,
    client,
):
    regexp = re.compile(r'^https?:\/\/.*(\.torrent|\/torrent|\/jav.php|nanobytes\.org).*')
    if incoming_link.lower().startswith("magnet:"):
        sagtus, err_message = add_magnet(aria_instance, incoming_link, c_file_name)
    elif incoming_link.lower().endswith(".torrent"):
        sagtus, err_message = add_torrent(aria_instance, incoming_link)
    else:
        sagtus, err_message = add_url(aria_instance, incoming_link, c_file_name)
    if not sagtus:
        return sagtus, err_message
    LOGGER.info(err_message)
    # https://stackoverflow.com/a/58213653/4723940
    await check_progress_for_dl(
        aria_instance, err_message, sent_message_to_update_tg_p, None
    )
    if incoming_link.startswith("magnet:"):
        #
        err_message = await check_metadata(aria_instance, err_message)
        #
        await asyncio.sleep(1)
        if err_message is not None:
            await check_progress_for_dl(
                aria_instance, err_message, sent_message_to_update_tg_p, None
            )
        else:
            return False, "can't get metadata \n\n#MetaDataError"
    await asyncio.sleep(1)
    file = aria_instance.get_download(err_message)
    to_upload_file = file.name
    com_g = file.is_complete
    #
    if is_zip:
        check_if_file = await create_archive(to_upload_file)
        if check_if_file is not None:
            to_upload_file = check_if_file
    #
    if is_unzip:
        try:
            check_ifi_file = get_base_name(to_upload_file)
            await unzip_me(to_upload_file)
            if os.path.exists(check_ifi_file):
                to_upload_file = check_ifi_file
        except Exception as ge:
            LOGGER.info(ge)
            LOGGER.info(
                f"Can't extract {os.path.basename(to_upload_file)}, Uploading the same file"
            )

    if to_upload_file and CUSTOM_FILE_NAME:
        if os.path.isfile(to_upload_file):
            os.rename(to_upload_file, f"{CUSTOM_FILE_NAME}{to_upload_file}")
            to_upload_file = f"{CUSTOM_FILE_NAME}{to_upload_file}"
        else:
            for root, _, files in os.walk(to_upload_file):
                LOGGER.info(files)
                for org in files:
                    p_name = f"{root}/{org}"
                    n_name = f"{root}/{CUSTOM_FILE_NAME}{org}"
                    os.rename(p_name, n_name)
            to_upload_file = to_upload_file

    if cstom_file_name:
        os.rename(to_upload_file, cstom_file_name)
        to_upload_file = cstom_file_name
    #
    response = {}
    LOGGER.info(response)
    user_id = user_message.from_user.id
    if com_g:
        if is_cloud:
            await upload_to_gdrive(
                to_upload_file, sent_message_to_update_tg_p, user_message, user_id
            )
        else:
            final_response = await upload_to_tg(
                sent_message_to_update_tg_p, to_upload_file, user_id, response, client
            )
            if not final_response:
                return True, None
            try:
                message_to_send = ""
                for key_f_res_se in final_response:
                    local_file_name = key_f_res_se
                    message_id = final_response[key_f_res_se]
                    channel_id = str(sent_message_to_update_tg_p.chat.id)[4:]
                    private_link = f"https://t.me/c/{channel_id}/{message_id}"
                    message_to_send += "⭕ <a href='"
                    message_to_send += private_link
                    message_to_send += "'>"
                    message_to_send += local_file_name
                    message_to_send += "</a>"
                    message_to_send += "\n"
                if not message_to_send:
                    message_to_send = "<i>FAILED</i> to upload files. 😞😞"
                else:
                    mention_req_user = (
                        f"<a href='tg://user?id={user_id}'>ꜱᴏᴜʀᴄᴇ ᴄᴏᴅᴇ 😑</a>\n\n"
                    )
                    message_to_send = mention_req_user + message_to_send
                    message_to_send = message_to_send + "\n\n" + "✅ 𝗣𝗼𝘄𝗲𝗿𝗲𝗱 𝗕𝘆 : @PriiiiyoBOTs"
                await user_message.reply_text(
                    text=message_to_send, quote=True, disable_web_page_preview=True
                )
            except Exception as go:
                LOGGER.error(go)
    return True, None


#


# https://github.com/jaskaranSM/UniBorg/blob/6d35cf452bce1204613929d4da7530058785b6b1/stdplugins/aria.py#L136-L164
async def check_progress_for_dl(aria2, gid, event, previous_message):
    # g_id = event.reply_to_message.from_user.id
    try:
        file = aria2.get_download(gid)
        complete = file.is_complete
        is_file = file.seeder
        if not complete:
            if not file.error_message:
                # sometimes, this weird https://t.me/c/1220993104/392975
                # error creeps up
                # TODO: temporary workaround
                downloading_dir_name = "N/A"
                try:
                    # another derp -_-
                    # https://t.me/c/1220993104/423318
                    downloading_dir_name = str(file.name)
                except:
                    pass
                #
                prog = pyprog.ProgressBar(" ", " ", total=100, bar_length=15, complete_symbol="■", not_complete_symbol="□", wrap_bar_prefix=" [", wrap_bar_suffix="]", progress_explain="", progress_loc=pyprog.ProgressBar.PROGRESS_LOC_END)

                old_stdout = sys.stdout
                new_stdout = io.StringIO()
                sys.stdout = new_stdout

                p = file.progress_string()
                l = len(p)
                p = p[:l-1]
                a = float(p)

                prog.set_stat(a)
                prog.update()
                output = new_stdout.getvalue()
                sys.stdout = old_stdout
                prg = output[3:len(output)]
                STR = int(os.environ.get("STR", 30))
                msg = ""
                msg = '╭──── ⌊ 📥 <b>𝑫𝒐𝒘𝒏𝒍𝒐𝒂𝒅𝒊𝒏𝒈...</b> ⌉ \n'
                msg += "│"+"\n├"+f"{prg}\n" +"│"
                msg += '\n├<b>ꜰɪʟᴇ ɴᴀᴍᴇ</b> 📚: '
                i = 0
                i = int(i)
                while downloading_dir_name != '':
                    st = downloading_dir_name[:STR]
                    if (i==0):
                        msg += f'{downloading_dir_name[:STR-15]}'
                        downloading_dir_name = downloading_dir_name[STR-15:len(downloading_dir_name)]
                        i = 1
                    else:
                        msg += f"\n│{st}"
                        downloading_dir_name = downloading_dir_name[STR:len(downloading_dir_name)]

                msg += f"\n├<b>ꜱᴘᴇᴇᴅ</b> 🚀 :  <code>{file.download_speed_string()} </code>"
                msg += f"\n├<b>ᴛᴏᴛᴀʟ ꜱɪᴢᴇ</b> 🗂 :  <code>{file.total_length_string()}</code>"

                if is_file is None :
                   msg += f"\n├<b>ᴄᴏɴɴᴇᴄᴛɪᴏɴꜱ</b> 📬 :  <code>{file.connections}</code>"
                else :
                   msg += f"\n├<b>ɪɴꜰᴏ</b> 📄 : <code>[ P : {file.connections} || S : {file.num_seeders} ]</code>"

                # msg += f"\n<b>ꜱᴛᴀᴛᴜꜱ</b> : <code>{file.status}</code>"
                msg += f"\n├<b>ᴇᴛᴀ</b> ⏳ :  <code>{file.eta_string()}</code>" +"\n│"
                msg += "\n╰─── ⌊ ⚡️ using engine aria2 ⌉"
                ikeyboard = [
                    InlineKeyboardButton(
                        "𝐂𝐚𝐧𝐜𝐞𝐥 🚫",
                        callback_data=(f"cancel {gid}").encode("UTF-8"),
                    )
                ]

                inline_keyboard = [ikeyboard]
                reply_markup = InlineKeyboardMarkup(inline_keyboard)
                if msg != previous_message:
                    if not file.has_failed:
                        try:
                            await event.edit(msg, reply_markup=reply_markup)
                        except FloodWait as e_e:
                            LOGGER.warning(f"Trying to sleep for {e_e}")
                            time.sleep(e_e.x)
                        except MessageNotModified as e_p:
                            LOGGER.info(e_p)
                            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
                        previous_message = msg
                    else:
                        LOGGER.info(
                            f"Cancelling downloading of {file.name} may be due to slow torrent"
                        )
                        await event.edit(
                            f"Download cancelled :\n<code>{file.name}</code>\n\n #MetaDataError"
                        )
                        file.remove(force=True, files=True)
                        return False
            else:
                msg = file.error_message
                LOGGER.info(msg)
                await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
                await event.edit(f"`{msg}`")
                return False
            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            await check_progress_for_dl(aria2, gid, event, previous_message)
        else:
            LOGGER.info(
                f"Downloaded Successfully 💯: `{file.name} ({file.total_length_string()})` 🤒"
            )
            await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
            await event.edit(
                f"Downloaded Successfully 💯: `{file.name} ({file.total_length_string()})` 🤒"
            )
            return True
    except aria2p.client.ClientException:
        await event.edit(
            f"Download cancelled ❌:\n<code>{file.name} ({file.total_length_string()})</code>"
        )
    except MessageNotModified as ep:
        LOGGER.info(ep)
        await asyncio.sleep(EDIT_SLEEP_TIME_OUT)
        await check_progress_for_dl(aria2, gid, event, previous_message)
    except FloodWait as e:
        LOGGER.info(e)
        time.sleep(e.x)
    except RecursionError:
        file.remove(force=True, files=True)
        await event.edit(
            "Download Auto Canceled :\n\n"
            "Your Torrent/Link is Dead.".format(file.name)
        )
        return False
    except Exception as e:
        LOGGER.info(str(e))
        if "not found" in str(e) or "'file'" in str(e):
            await event.edit(
                f"Download cancelled ❌:\n<code>{file.name} ({file.total_length_string()})</code>"
            )
        else:
            LOGGER.info(str(e))
            await event.edit(
                "<u>error</u> :\n<code>{}</code> \n\n#error".format(str(e))
            )

        return False


# https://github.com/jaskaranSM/UniBorg/blob/6d35cf452bce1204613929d4da7530058785b6b1/stdplugins/aria.py#L136-L164


async def check_metadata(aria2, gid):
    file = aria2.get_download(gid)
    LOGGER.info(file)
    if not file.followed_by_ids:
        # https://t.me/c/1213160642/496
        return None
    new_gid = file.followed_by_ids[0]
    LOGGER.info("Changing GID " + gid + " to " + new_gid)
    return new_gid
