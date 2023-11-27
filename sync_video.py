import subprocess
import json
from datetime import datetime
import pymongo


def run_js_file(js_file_path, input_array):
    try:
        result = subprocess.run(
            ["node", js_file_path, json.dumps(input_array)],
            capture_output=True,
            text=True,
            check=True,
        )
        print("JavaScript Output:", result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error running JavaScript:", e)
        print("JavaScript Error Output:", e.stderr)


def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(data, file_path):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def save_to_mongodb(data, id_campaign, collection):
    existing_document = collection.find_one({"idCampaign": id_campaign})

    if existing_document:
        # Update the existing document with the new data
        collection.update_one({"idCampaign": id_campaign}, {"$set": data})
        print(f"Successfully updated data for campaign {id_campaign}.")
    else:
        # Insert the new data if the document doesn't exist
        try:
            result = collection.insert_one(data)
            print(f"Successfully inserted data for campaign {id_campaign}.")
        except Exception as e:
            print(f"Failed to insert data for campaign {id_campaign}. Error: {str(e)}")


def sync_video(campaign_data, collection):
    
    js_file_path = "./video.js"

    video_url = [video["video_url"] for video in campaign_data.get("video", [])]
    
    run_js_file(js_file_path, video_url)
    date_today = datetime.now().strftime("%Y-%m-%d")

    data = read_json_file(
        f"./video_json/Video_Before_ETL.json"
    )

    id_campaign = campaign_data.get("idCampaign")
    nama_campaign = campaign_data.get("namaCampaign")
    videos = []
    selected_data = []

    for index, item in enumerate(data):
        play_count = item["result"]["statistics"]["playCount"]
        like_count = item["result"]["statistics"]["likeCount"]
        comment_count = item["result"]["statistics"]["commentCount"]
        share_count = item["result"]["statistics"]["shareCount"]

        engagement_rate = (
            ((like_count + comment_count + share_count) / play_count)
            if play_count > 0
            else 0
        )

        video_data = {
            "id": item["result"]["id"],
            "description": item["result"]["description"],
            "username": item["result"]["author"]["username"],
            "playCount": play_count,
            "commentCount": comment_count,
            "shareCount": share_count,
            "likeCount": like_count,
            "engagementRate": engagement_rate,
            "video_url": video_url[index],
            "dateRetrieve": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        videos.append(video_data)

    selected_fields = {
        "idCampaign": id_campaign,
        "namaCampaign": nama_campaign,
        "video": videos,
    }
    selected_data = [selected_fields]

    write_json_file(selected_data, f"./video_json/Video_After_ETL.json")

    data_to_save = read_json_file(f"./video_json/Video_After_ETL.json")

    for item in data_to_save:
        id_campaign = item.get("idCampaign")
        save_to_mongodb(item, id_campaign, collection)
