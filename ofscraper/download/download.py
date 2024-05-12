import json
import logging
import subprocess
import traceback

import ofscraper.download.downloadbatch as batchdownloader
import ofscraper.download.downloadnormal as normaldownloader
import ofscraper.utils.args.read as read_args
import ofscraper.utils.config.data as config_data
import ofscraper.utils.constants as constants
import ofscraper.utils.hash as hash
import ofscraper.utils.settings as settings
import ofscraper.utils.system.system as system

from ofscraper.download.shared.utils.text import textDownloader



def download_process(username, model_id, medialist, posts=None):
    if not read_args.retriveArgs().command=="metadata":
        textDownloader(posts, username=username)
    data= download_picker(username, model_id, medialist)
    download_post_process(username, model_id, medialist, posts)
    return data


def download_picker(username, model_id, medialist):
    if len(medialist) == 0:
        logging.getLogger("shared").error(
            f"[bold]{username}[/bold] ({0} photos, {0} videos, {0} audios,  {0} skipped, {0} failed)"
        )
        return 0, 0, 0, 0, 0
    elif (
        system.getcpu_count() > 1
        and (
            len(medialist)
            >= config_data.get_threads() * constants.getattr("DOWNLOAD_THREAD_MIN")
        )
        and settings.not_solo_thread()
    ):
        return batchdownloader.process_dicts(username, model_id, medialist)
    else:
        return normaldownloader.process_dicts(username, model_id, medialist)


def remove_downloads_with_hashes(username, model_id):
    hash.remove_dupes_hash(username, model_id, "audios")
    hash.remove_dupes_hash(username, model_id, "images")
    hash.remove_dupes_hash(username, model_id, "videos")


def download_post_process(username, model_id, medialist, postlist):
    log = logging.getLogger("shared")
    if not settings.get_post_download_script():
        return
    try:
        mediadump = json.dumps(list(map(lambda x: x.media, medialist)))
        postdump = json.dumps(list(map(lambda x: x.post, postlist)))
        model_id = str(model_id)
        subprocess.run(
            [
                settings.get_post_download_script(),
                username,
                model_id,
                mediadump,
                postdump,
            ]
        )
    except Exception as e:
        log.traceback_(e)
        log.traceback_(traceback.format_exc())
