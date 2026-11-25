"""Cloud first (Harish, 25 Nov; AGENT.md 16.6): the nightly fetch tries the laptop list, uploads what it got to
Drive from-laptop/, and stops at the first YouTube refusal. No network, no keys. Run: python -m tests.test_autofetch"""
import os
import sys

from engine import autofetch as A
from tests.test_control_room import check


class Drive:
    def __init__(self):
        self.up = []

    def upload(self, path, folder, name=None):
        self.up.append((folder, name))


def main():
    todo = {"trailers": [{"film": "New Film", "url": None}], "topup": ["Old Film"], "study": ["https://www.youtube.com/shorts/abc"],
            "songs": [{"key": "song_a", "song": "A", "link": None}, {"key": "song_b", "song": "B", "link": "https://www.instagram.com/reel/x"}]}
    order = [k for k, _ in A.jobs(todo)]
    check(order == ["trailer", "song", "study", "trailer"], "most useful first; Instagram songs stay for the laptop")
    A.laptop.todo = lambda d: todo
    A.laptop.sort_drop = lambda d: None
    A.helper = lambda: None
    A.ytdlp_cmd = lambda c=None: ["yt-dlp"]
    calls = []

    def ok_then_refused(h, cmd, kind, item, out):
        calls.append(kind)
        if len(calls) == 1:
            open(os.path.join(out, "New Film - trailer [id].mp4"), "w").close()
            return True, "saved"
        return False, "ERROR: Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies"
    A.run_one = ok_then_refused
    os.environ.pop("YOUTUBE_COOKIES", None)
    d = Drive()
    res = A.run(d)
    check(res["got"] == 1 and res["tried"] == 2 and "no YOUTUBE_COOKIES" in res["note"], "stops at the first refusal, says why")
    check(d.up == [("from-laptop", "New Film - trailer [id].mp4")], "what it got goes to Drive from-laptop/")
    os.environ["YOUTUBE_COOKIES"] = "# Netscape HTTP Cookie File"
    calls.clear()
    res = A.run(Drive())
    check(res["signed_in"] and "expired" in res["note"], "signed in but refused: says the cookies may have expired")
    os.environ.pop("YOUTUBE_COOKIES", None)


if __name__ == "__main__":
    main()
    print("ALL OK" if not check.failed else f"{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)
