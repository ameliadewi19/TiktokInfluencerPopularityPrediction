import subprocess
import json
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
import pymongo

def run_js_file(js_file_path):
    try:
        result = subprocess.run(
            ["node", js_file_path], capture_output=True, text=True, check=True
        )
        print("JavaScript Output:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error running JavaScript:", e)
        print("JavaScript Error Output:", e.stderr)
        return None


def download_and_save_avatar(url, username):
    response = requests.get(url)

    if response.status_code == 200:
        image = Image.open(BytesIO(response.content))
        image_path = (
            f"./static/avatar/{username}_avatar.jpg"  # Replace with the desired path
        )
        image.save(image_path)
        return image_path
    else:
        print(f"Failed to download avatar for {username}")
        return None


def process_json_data(data):
    # Inisialisasi list untuk menyimpan data terpilih
    selected_data = []
    total_playcount = 0  # Inisialisasi total playCount
    total_commentcount = 0  # Inisialisasi total playCount
    total_sharecount = 0  # Inisialisasi total playCount

    # Loop melalui data JSON
    for (
        username,
        user_data,
    ) in data.items():  # Menggunakan .items() untuk mengakses kunci dan data
        heartCount = user_data["result"]["stats"]["heartCount"]
        followerCount = user_data["result"]["stats"]["followerCount"]

        engagement_rate = ((heartCount) / followerCount) if followerCount > 0 else 0

        statistic_data = {
            "followerCount": followerCount,
            "heartCount": heartCount,
            "totalPlayCount": total_playcount,
            "totalCommentCount": total_commentcount,
            "totalShareCount": total_sharecount,
            "engagementRate": engagement_rate,
            "dateRetrieve": date_today,
        }
        avatar_url = user_data["result"]["users"]["avatarMedium"]
        avatar_path = download_and_save_avatar(avatar_url, username)

        selected_fields = {
            "username": user_data["result"]["users"]["username"],
            "nickname": user_data["result"]["users"]["nickname"],
            "avatar": avatar_path,
            "statistic": [statistic_data],  # Add the statistic data once,
        }
        selected_data.append(selected_fields)

    # Simpan data yang terpilih ke file JSON baru
    with open(f"./IMPLEMENTASI/Data_After_ETL/user_ETL_{date_today}.json", "w") as file:
        json.dump(selected_data, file, indent=4)

    print("Data telah disimpan json")

    # Baca data dari file JSON
    with open(
        f"./IMPLEMENTASI/Data_After_ETL/user_ETL_{date_today}.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    # Inisialisasi koneksi MongoDB
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["tiktok_analysis"]  # Ganti dengan nama database Anda
    collection = db["user_api"]  # Ganti dengan nama koleksi Anda

    for item in data:
        username = item.get("username")

        # Cari dokumen dengan username yang sama
        existing_document = collection.find_one({"username": username})

        if existing_document:
            # Jika username sudah ada, update array "statistic"
            new_statistic_data = item.get("statistic")
            collection.update_one(
                {"username": username},
                {"$push": {"statistic": {"$each": new_statistic_data}}},
            )
            print(f"Berhasil memperbarui data untuk pengguna {username}.")
        else:
            try:
                # Jika username belum ada, masukkan data baru
                result = collection.insert_one(item)
                print(f"Berhasil memasukkan data untuk pengguna {username}.")
            except Exception as e:
                print(
                    f"Gagal memasukkan data untuk pengguna {username}. Error: {str(e)}"
                )


js_file_path = "./IMPLEMENTASI/try.js"  # Ganti dengan path yang sesuai
js_output = run_js_file(js_file_path)

# Melanjutkan eksekusi setelah file JavaScript selesai dijalankan
if js_output is not None:
    # Data JSON yang diberikan
    date_today = datetime.now().strftime("%Y-%m-%d")
    with open(
        f"./IMPLEMENTASI/Data_Before_ETL/tiktok_results_{date_today}.json",
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    # Panggil fungsi untuk memproses data JSON
    process_json_data(data)
