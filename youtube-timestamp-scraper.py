# 1. チャンネルID からアップロード動画一覧の ID を取得
#   - アップロード動画の一覧のIDはチャンネルIDの戦闘のUCをUUにしたものかも, 後回しってことで
# 2. アップロード動画一覧の ID から動画のID を全部取得
#   - nextPageToken, id, title, description までとる
#   - title に"歌"が入ってないのは歌枠じゃないだろうから除外
#   - description にタイムスタンプが入ってる場合は, 多分それで事足りるのでスキップ
# 3. アップロード動画一覧から, 概要欄とコメント欄をすべて取得
# 4. 取得したデータをこねくり回して, 動画内時間コメントと曲名のセットのリストを作成
#   - テキストディスプレイの方で, リンクを抜き出して, &amp; ⇨ & にすればよさげ

import json
import os
from dataclasses import asdict

from apiclient import discovery
from dotenv import load_dotenv

from infoclass import VideoInfo, CommentInfo
from utils import aligned_json_dump

load_dotenv()

API_KEY = os.getenv('API_KEY')
youtube = discovery.build('youtube', 'v3', developerKey = API_KEY)

users = json.load(open('user_ids.json'))

def user_id_to_uploads_list_id(user_id: str) -> str:
    # 勘で変換してるだけなので, 今後使えなくなるかも
    # 使えなくなった場合は, API でチャンネルの ContentDetails とかを叩くこと

    # channel id は 先頭がUC
    # アップロード済みの再生リストは, 先頭がUUそれ以外は channel id と一致
    if user_id[:2] == "UC":
        user_id = list(user_id)
        user_id[1] = "U"
        user_id = "".join(user_id)
    elif user_id[:2] == "UU":
        pass
    else:
        return None

    return user_id

uploads_id = map(user_id_to_uploads_list_id, users)

def get_video_info_in_playlist(playlist_id: str) -> list[VideoInfo]:
    # 参考: https://zenn.dev/yorifuji/articles/youtube-data-api-python
    video_info_list = []

    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=100,
        playlistId=playlist_id,
        fields="nextPageToken,items/snippet(title,description,resourceId/videoId)"
    )

    while request:
        response = request.execute()
        video_info_list.extend(list(map(VideoInfo.from_response_snippet, response["items"])))
        request = youtube.playlistItems().list_next(request, response)

    return video_info_list

# video info の取得
video_info_list: list[VideoInfo] = []
for upload_id in uploads_id:
    video_info_list += get_video_info_in_playlist(upload_id)

vi_dict = [asdict(vi) for vi in video_info_list]
aligned_json_dump(vi_dict, "video_info.json")

# comment の取得
def get_comments(video_id: str) -> list[CommentInfo]:
    comment_list = []

    comment_field = "snippet(videoId,textDisplay,textOriginal)"
    top_comment_f = f"items/snippet/topLevelComment/{comment_field}"
    replies_f = f"items/replies/comments/{comment_field}"

    request = youtube.commentThreads().list(
        part="snippet,replies",
        maxResults=100,
        videoId=video_id,
        fields=f"nextPageToken,{top_comment_f},{replies_f}"
    )

    while request:
        response = request.execute()
        c_mat = list(map(CommentInfo.response_item_to_comments, response["items"]))
        comment_list.extend(sum(c_mat, []))
        request = youtube.commentThreads().list_next(request, response)

    return comment_list

comment_info_list: list[CommentInfo] = []
for video_info in video_info_list:
    try:
        video_info.comments = get_comments(video_info.id)
    except:
        pass

vi_dict = [asdict(vi) for vi in video_info_list]
aligned_json_dump(vi_dict, "comment_info.json")
