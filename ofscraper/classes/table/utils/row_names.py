ROW_NAMES = (
    "Number",
    "Download_Cart",
    "UserName",
    "Downloaded",
    "Unlocked",
    "other_posts_with_media",
    "Length",
    "Mediatype",
    "Post_Date",
    "Post_Media_Count",
    "Responsetype",
    "Price",
    "Post_ID",
    "Media_ID",
    "Text",
)

def row_names():
    for ele in ROW_NAMES:
        yield ele.lower()
