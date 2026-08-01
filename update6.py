import base64
import os

import requests

jojo = requests.get(
    "https://www.zhihu.com/api/v4/sticker-groups/1114161698310770688"
).json()["data"]["stickers"]

mapping = {
    item["title"]: {"desc": item["title"], "url": f"/assets/zhihu/{item['title']}.webp"}
    for item in jojo
}
with open("zhihu.json", "w", encoding="utf-8") as f:
    import json

    json.dump(mapping, f, ensure_ascii=False, indent=4)

os.makedirs("zhihu", exist_ok=True)

for item in jojo:
    content = base64.b64decode(
        item["static_image_url"][len("data:image/png;base64,") :]
    )
    with open(os.path.join("zhihu", item["title"] + ".png"), "wb") as f:
        f.write(content)
