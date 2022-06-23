import re
from dataclasses import dataclass
from xml.etree.ElementTree import Comment

@dataclass
class CommentInfo:
    text_display: str
    text_original: str

    @classmethod
    def from_response_comment(cls, response_comment: dict):
        comment_snippet = response_comment["snippet"]
        return cls(
            text_display = comment_snippet["textDisplay"],
            text_original = comment_snippet["textOriginal"]
        )

    @classmethod
    def response_item_to_comment_dict(cls, response_item: dict) -> list[dict]:
        comment_list = []
        comment_list.append(response_item["snippet"]["topLevelComment"])
        replies = response_item.get("replies", [])
        if replies:
            replies = replies["comments"]
        comment_list += replies
        return comment_list

    @classmethod
    def response_item_to_comments(cls, response_item: dict):
        c_dict = cls.response_item_to_comment_dict(response_item)
        return list(map(cls.from_response_comment, c_dict))

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(
            text_display = json_dict["text_display"],
            text_original = json_dict["text_original"]
        )

@dataclass
class VideoInfo:
    id: str
    title: str
    description: str
    comments: list[CommentInfo]

    @classmethod
    def from_response_snippet(cls, response_snippet:dict):
        snippet_content = response_snippet.get("snippet", response_snippet)
        return cls(
            id=snippet_content["resourceId"]["videoId"],
            title=snippet_content["title"],
            description=snippet_content["description"],
            comments=[]
        )

    @classmethod
    def from_json(cls, json_dict: dict):
        return cls(
            id = json_dict["id"],
            title = json_dict["title"],
            description = json_dict["description"],
            comments = [CommentInfo.from_json(c) for c in json_dict["comments"]]
        )

@dataclass
class TimeStamp:
    video_id: str
    link: str
    timestamp: str
    text: str

    def normalize(self):
        self.link = self.link.replace("&amp;", "&")
        self.text = self.text.strip()

    @classmethod
    def from_text(cls, video_id: str, text: str):
        pattern = "<a href=\\\"(https://www.youtube.com/watch\?v=[\w]+\&amp;t=[\w]+)\\\">([\d:]+)</a>"
        timestamp_pattern = re.compile(pattern)

        timestamp_list: list[TimeStamp] = []
        line_list = text.split("<br>")
        for line in line_list:
            timestamp = timestamp_pattern.search(line)
            if timestamp is None:
                continue
            comment = timestamp_pattern.sub("", line)
            timestamp_list.append(cls(
                video_id = video_id,
                link = timestamp[1],
                timestamp = timestamp[2],
                text = comment
            ))

        return timestamp_list

    @classmethod
    def from_videoinfo(cls, video_info: VideoInfo):
        # 行でぶつぎりにしてから、タイムスタンプを抽出するようにする
        timestamp_list: list[TimeStamp] = TimeStamp.from_text(video_info.id, video_info.description)
        for comment in video_info.comments:
            timestamp_list.extend(TimeStamp.from_text(video_info.id, comment.text_display))

        [ts.normalize() for ts in timestamp_list]
        return timestamp_list
