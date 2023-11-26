# import json
# import random
# import datetime
# import pymongo

# def generate_dummy_values(user_data):
#     for user in user_data:
#         random_PlayCount = random.randint(1000, 20000)
#         random_CommentCount = random.randint(1000, 10000)
#         random_ShareCount = random.randint(1000, 5000)
#         random_heartCount = random.randint(1000, 15000)
#         random_followerCount = random.randint(1000, 5000)

#         # Update values in the source dataset
#         user_statistic = user["statistic"]
#         user_statistic["totalPlayCount"] = random_PlayCount
#         user_statistic["totalCommentCount"] = random_CommentCount
#         user_statistic["totalShareCount"] = random_ShareCount
#         user_statistic["heartCount"] = random_heartCount
#         user_statistic["followerCount"] = random_followerCount

#         # Additional logic for handling edge cases
#         if user_statistic["totalPlayCount"] == 0:
#             user_statistic["totalPlayCount"] = (
#                 user_statistic["heartCount"] + random_PlayCount
#             )

#         if user_statistic["totalCommentCount"] == 0:
#             user_statistic["totalCommentCount"] = (
#                 user_statistic["followerCount"] / 20
#             ) + random_CommentCount

#         if user_statistic["totalShareCount"] == 0:
#             user_statistic["totalShareCount"] = (
#                 user_statistic["followerCount"] / 30
#             ) + random_ShareCount

#         user_statistic["engagementRate"] = (
#             user_statistic["heartCount"]
#             + user_statistic["totalShareCount"]
#             + user_statistic["totalCommentCount"]
#         ) / user_statistic["totalPlayCount"]

#         if user_statistic["engagementRate"] > 20:
#             user_statistic["engagementRate"] /= 100

# def update_mongo_values(collection, item):
#     username = item.get("username")
#     new_statistic_data = item.get("statistic", {})

#     if not new_statistic_data:
#         print(f"Skipping user {username} - no statistic data.")
#         return

#     current_date = datetime.datetime.now().strftime("%Y-%m-%d")

#     existing_document = collection.find_one({"username": username})

#     if existing_document:
#         existing_statistic_list = existing_document.get("statistic", [])

#         if not existing_statistic_list:
#             # If existing_statistic_list is empty, just insert new data with the current date
#             new_statistic_data["dateRetrieve"] = current_date
#             try:
#                 result = collection.insert_one(item)
#                 print(f"Successfully inserted data for user {username}.")
#             except Exception as e:
#                 print(f"Failed to insert data for user {username}. Error: {str(e)}")
#             return

#         # Check if data for the current date already exists
#         existing_dates = [stat.get("dateRetrieve") for stat in existing_statistic_list]

#         if current_date in existing_dates:
#             # Update existing entry for the current date
#             collection.update_one(
#                 {"username": username, "statistic.dateRetrieve": current_date},
#                 {"$set": {"statistic.$": new_statistic_data}},
#             )
#             print(f"Successfully updated data for user {username} on {current_date}.")
#         else:
#             # Add new statistic data with the current date
#             new_statistic_data["dateRetrieve"] = current_date
#             existing_statistic_list.append(new_statistic_data)
#             collection.update_one(
#                 {"username": username},
#                 {"$set": {"statistic": existing_statistic_list}},
#             )

#             new_avatar = item.get("avatar")
#             if new_avatar:
#                 collection.update_one(
#                     {"username": username},
#                     {"$set": {"avatar": new_avatar}},
#                 )

#             print(f"Successfully updated data for user {username} on {current_date}.")
#     else:
#         # Insert new data with the current date
#         new_statistic_data["dateRetrieve"] = current_date
#         try:
#             result = collection.insert_one(item)
#             print(f"Successfully inserted data for user {username}.")
#         except Exception as e:
#             print(f"Failed to insert data for user {username}. Error: {str(e)}")

# def generate_dummy():
#     print("Generating dummy values...")
#     with open("latest_data_influencer.json", "r") as file:
#         source_data = json.load(file)

#     client = pymongo.MongoClient("mongodb://localhost:27017/")
#     db = client["tiktok_analysis"]
#     collection = db["user_api"]

#     for item in source_data:
#         generate_dummy_values([item])
#         update_mongo_values(collection, item)

#     print("Values updated successfully.")

import json
import random
import datetime
import pymongo

def generate_dummy_values(user_data):
    for user in user_data:
        random_PlayCount = random.randint(1000, 20000)
        random_CommentCount = random.randint(1000, 10000)
        random_ShareCount = random.randint(1000, 5000)
        random_heartCount = random.randint(1000, 15000)
        random_followerCount = random.randint(1000, 5000)

        # Update values in the source dataset
        user_statistic = user["statistic"]
        user_statistic["totalPlayCount"] = random_PlayCount
        user_statistic["totalCommentCount"] = random_CommentCount
        user_statistic["totalShareCount"] = random_ShareCount
        user_statistic["heartCount"] = random_heartCount
        user_statistic["followerCount"] = random_followerCount

        # Additional logic for handling edge cases
        if user_statistic["totalPlayCount"] == 0:
            user_statistic["totalPlayCount"] = (
                user_statistic["heartCount"] + random_PlayCount
            )

        if user_statistic["totalCommentCount"] == 0:
            user_statistic["totalCommentCount"] = (
                user_statistic["followerCount"] / 20
            ) + random_CommentCount

        if user_statistic["totalShareCount"] == 0:
            user_statistic["totalShareCount"] = (
                user_statistic["followerCount"] / 30
            ) + random_ShareCount

        user_statistic["engagementRate"] = (
            user_statistic["heartCount"]
            + user_statistic["totalShareCount"]
            + user_statistic["totalCommentCount"]
        ) / user_statistic["totalPlayCount"]

        if user_statistic["engagementRate"] > 20:
            user_statistic["engagementRate"] /= 100


def update_values(source_data, target_data):
    for source_user in source_data:
        source_username = source_user["username"]

        for target_user in target_data:
            if target_user["username"] == source_username:
                # Update values
                target_user_statistic = target_user["statistic"]
                target_user_statistic["totalPlayCount"] += source_user["statistic"]["totalPlayCount"]
                target_user_statistic["totalCommentCount"] += source_user["statistic"]["totalCommentCount"]
                target_user_statistic["totalShareCount"] += source_user["statistic"]["totalShareCount"]
                target_user_statistic["heartCount"] += source_user["statistic"]["heartCount"]
                target_user_statistic["followerCount"] += source_user["statistic"]["followerCount"]

                # Extract the source date_retrieve
                source_date_retrieve_str = source_user["statistic"]["dateRetrieve"]
                source_date_retrieve = datetime.datetime.strptime(source_date_retrieve_str, "%Y-%m-%d")

                # Add one day to the source date_retrieve
                target_date_retrieve = source_date_retrieve + datetime.timedelta(days=1)

                # Convert the target date_retrieve to string format
                target_date_retrieve_str = datetime.datetime.now().strftime("%Y-%m-%d")

                # Update the target_user
                target_user_statistic["dateRetrieve"] = target_date_retrieve_str

                # Additional logic for handling edge cases
                if target_user_statistic["totalPlayCount"] == 0:
                    target_user_statistic["totalPlayCount"] = (
                        target_user_statistic["heartCount"] + source_user["statistic"]["totalPlayCount"]
                    )

                if target_user_statistic["totalCommentCount"] == 0:
                    target_user_statistic["totalCommentCount"] = (
                        target_user_statistic["followerCount"] / 20
                    ) + source_user["statistic"]["totalCommentCount"]

                if target_user_statistic["totalShareCount"] == 0:
                    target_user_statistic["totalShareCount"] = (
                        target_user_statistic["followerCount"] / 30
                    ) + source_user["statistic"]["totalShareCount"]

                target_user_statistic["engagementRate"] = (
                    target_user_statistic["heartCount"]
                    + target_user_statistic["totalShareCount"]
                    + target_user_statistic["totalCommentCount"]
                ) / target_user_statistic["totalPlayCount"]

                if target_user_statistic["engagementRate"] > 20:
                    target_user_statistic["engagementRate"] /= 100

def generate_dummy():
    print("Generating dummy values...")
    with open("latest_data_influencer.json", "r") as file:
        source_data = json.load(file)

    with open("latest_data_influencer.json", "r") as file:
        target_data = json.load(file)

    generate_dummy_values(source_data)
    update_values(source_data, target_data)

    with open("latest_data_influencer.json", "w") as file:
        json.dump(target_data, file, indent=2)

    print("Values updated successfully.")

    with open("latest_data_influencer.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["tiktok_analysis"]
    collection = db["user_api"]

    for item in data:
        username = item.get("username")
        existing_document = collection.find_one({"username": username})

        if existing_document:
            new_statistic_data = item.get("statistic")

            # Find the existing statistic with the same date
            existing_statistic = next(
                (stat for stat in existing_document["statistic"] if stat["dateRetrieve"] == new_statistic_data["dateRetrieve"]),
                None
            )

            if existing_statistic:
                # Update the existing statistic
                existing_statistic.update(new_statistic_data)
            else:
                # Add the new statistic if not found
                collection.update_one(
                    {"username": username},
                    {"$push": {"statistic": new_statistic_data}},
                )

            new_avatar = item.get("avatar")
            if new_avatar:
                collection.update_one(
                    {"username": username},
                    {"$set": {"avatar": new_avatar}},
                )

            print(f"Berhasil memperbarui data untuk pengguna {username}.")
        else:
            try:
                result = collection.insert_one(item)
                print(f"Berhasil memasukkan data untuk pengguna {username}.")
            except Exception as e:
                print(f"Gagal memasukkan data untuk pengguna {username}. Error: {str(e)}")
