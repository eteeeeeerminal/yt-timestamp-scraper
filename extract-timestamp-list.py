import json
from dataclasses import asdict

from infoclass import VideoInfo, CommentInfo, TimeStamp
from utils import aligned_json_dump

video_info_dict = json.load(open("comment_info.json", encoding='utf-8'))
video_info_list = [VideoInfo.from_json(v) for v in video_info_dict]

timestamp_list = sum(map(TimeStamp.from_videoinfo, video_info_list), [])
ts_dict = [asdict(ts) for ts in timestamp_list]
aligned_json_dump(ts_dict, "timestamps.json")
