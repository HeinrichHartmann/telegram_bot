import requests as req
import click
import sys
from pprint import pprint as pp
from pathlib import Path
import shutil
import random
import subprocess as sub


def _assert(cond, msg = "assertion failed"):
    if not cond:
        raise AssertionError(msg)

def _log(msg):
    print(msg, file=sys.stderr)

def _download(url, out_path):
    out_path = Path(out_path)
    out_dir = out_path.parents[0]
    if not out_dir.exists():
        _log(f"Creating {out_dir}")
        out_dir.mkdir(parents=True)
    if not out_dir.is_dir():
        raise Exception(f"Not a directory: {out_dir}")
    with req.get(url,stream=True) as res, open(out_path, "wb") as out:
        _log(f"Writing {out_path}")
        shutil.copyfileobj(res.raw, out)

def _group_gen():
    return f"GEN_{random.getrandbits(64)}"

def _call(*args):
    _log(f"Running {args} ... ")
    sub.check_call(args, stdout=sys.stderr, stderr=sys.stderr)
    _log(f"... done")


class TelegramBot(object):
    def __init__(self, token, dlfolder="./dl", offset = 0):
        self._token = token
        self._offset = offset
        self._offset_poll = None
        self._dl = Path(dlfolder)
        self.test()

    def _api_get_json(self, path, args = {}):
        res = req.get(f"https://api.telegram.org/bot{self._token}{path}", args)
        if not res.status_code == 200:
            raise Exception([res.status_code, res.headers, res.text ])
        jres = res.json()
        if not jres['ok']:
            raise Exception([res.status_code, res.headers, jres ])
        return jres['result']

    def test(self):
        self._api_get_json("/getMe")

    def poll_msg(self):
        lst = self._api_get_json(
            "/getUpdates",
            { "offset" : self._offset, "limit" : 1 }
        )
        if len(lst) == 0:
            return None
        msg = lst[0]
        pp(msg)
        self._offset_poll = msg['update_id']
        if 'edited_message' in msg:
            msg = msg['edited_message']
        elif 'message' in msg:
            msg = msg['message']
        # Generate a group_id if unset
        msg['media_group_id'] = "G_" + str(msg.get('media_group_id', _group_gen()))
        return msg

    def advance(self):
        _assert( self._offset_poll, "Poll offset unset" )
        self._offset = self._offset_poll + 1

    def pull(self):
        msg = self.poll_msg()
        if not msg:
            return
        self.dump()
        self.advance()
        return True

    def pull_group(self):
        msg = self.poll_msg()
        if not msg:
            return # nothing to do
        group_id = msg["media_group_id"]
        while(msg and group_id == msg["media_group_id"] ):
            self.dump(msg)
            self.advance()
            msg = self.poll_msg()
        self.create_group_pdf(group_id)

    def create_group_pdf(self, group_id):
        files = list(
            str(x) for x in Path(f"./dl/{group_id}/").rglob("*") if x.is_file() and not x.name.startswith(".")
        )
        if len(files) > 0:
            _call("convert", *files, f"./dl/{group_id}.pdf")
            _call("rm", "-r", f"./dl/{group_id}")

    def dump(self, msg):
        if 'photo' in msg:
            self.dump_photo(msg)
        elif 'document' in msg:
            self.dump_document(msg)
        else:
            self.dump_text(msg)

    def dump_photo(self, msg):
        _assert(msg)
        _assert('photo' in msg, "Not a photo")
        def best_photo():
            _fs = 0
            _i = 0
            for i, p in enumerate(msg["photo"]):
                if p["file_size"] > _fs:
                    _fs = p["file_size"]
                    _i  = i
            return msg["photo"][_i]
        p = best_photo()
        caption = msg.get("caption")
        caption = f"{caption} - " if caption else ""
        group_id = msg["media_group_id"]
        file_id = p["file_id"]
        file_path = self._api_get_json("/getFile", {"file_id" : p["file_id"]})["file_path"]
        tmp_path = self._dl / group_id / file_path
        _download(
            f"https://api.telegram.org/file/bot{self._token}/{file_path}",
            tmp_path.parents[0] / f"{tmp_path.stem}{caption}{tmp_path.suffix}"
        )

    def dump_document(self, msg):
        _assert(msg)
        _assert('document' in msg, "Not a document")
        group_id = msg["media_group_id"]
        doc = msg['document']
        file_id = doc["file_id"]
        file_name = doc['file_name']
        file_path = self._api_get_json("/getFile", {"file_id" : doc["file_id"]})["file_path"]
        out_path = self._dl / group_id / file_path
        _download(
            f"https://api.telegram.org/file/bot{self._token}/{file_path}",
            out_path.parents[0] / f"{out_path.stem} - {file_name}"
        )

    def dump_text(self, msg):
        pp(msg)

@click.group()
def cli():
    pass

@click.command()
@click.argument('token')
def pull(token):
    """Pull all documents from telegram bot"""
    # TOKEN = '1457322660:AAFjfUr5JPwWgaXWnJ-jAjGWQgjrs6PgNOQ'
    bot = TelegramBot(token)
    bot.pull_group()
    # while bot.pull():
    #     pass
    print("done")

cli.add_command(pull)
