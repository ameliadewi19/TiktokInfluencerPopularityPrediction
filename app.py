from flask import Flask, render_template, request, make_response, session, redirect, url_for, jsonify, send_file, flash, get_flashed_messages
from bson import ObjectId
from pymongo import MongoClient
from functools import wraps, update_wrapper
from datetime import datetime, timedelta
from flask_bcrypt import Bcrypt
import secrets
import json
import bson
import regresi
import generate_dummy
import os
from apscheduler.schedulers.background import BackgroundScheduler
from sync_video import sync_video

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = secrets.token_hex(16) 

client = MongoClient('mongodb://localhost:27017/')  
db = client['tiktok_analysis']  
collection_influencer = db['user_api']  
collection_campaign = db['video_api'] 
collection_user = db['user'] 

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    return update_wrapper(no_cache, view)

def format_number(value):
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    else:
        return str(value)

app.jinja_env.filters['format_number'] = format_number

def format_percentage(value):
    rounded_value = round(value, 2)
    return '{:.2f}%'.format(rounded_value)

app.jinja_env.filters['format_percentage'] = format_percentage

# Check if the user is logged in before accessing certain routes
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session or not session['user_id']:
            print("User not logged in")
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

@app.route("/")
@app.route("/login")
def login():
    print("Login process initiated 1")
    return render_template("login.html")

@app.route('/login_process', methods=['POST'])
def login_process():
    print("Login process initiated 2")
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        # If username or password is empty, redirect with an empty_fields parameter
        return redirect(url_for('login', empty_fields=True))

    # Query the database for the user with the provided username
    user_data = collection_user.find_one({'username': username})

    if user_data and bcrypt.check_password_hash(user_data['password'], password):
        # If the user exists and the password is correct, log in the user
        session['user_id'] = str(user_data['_id'])  # Store user ID in the session
        session['username'] = username  # Store the username in the session
        print("Login successful. User ID:", session['user_id'])
        print("Session after login:", session)
        return redirect(url_for('home'))
    else:
        print("Login failed")
        # If the user doesn't exist or the password is incorrect, show an error
        return redirect(url_for('login', login_error=True))

@app.route('/logout')
def logout():
    # Clear the user session to log out the user
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/home")
@nocache
# @login_required
def home():
    print("Session in home route:", session)
    total_influencer_data = collection_influencer.count_documents({})
    total_campaign_data = collection_campaign.count_documents({})
    influencers_data = collection_influencer.find()
    influencers_sorted = sorted(influencers_data, key=lambda x: x['statistic'][-1]['engagementRate'], reverse=True)
    top_5_influencers = influencers_sorted[:5]
    return render_template("home.html", total_influencer=total_influencer_data, influencers=top_5_influencers, total_campaign=total_campaign_data)

@app.route("/influencer")
@nocache
# @login_required
def influencer():
    # Mengambil data influencer dari MongoDB dan mengurutkannya berdasarkan engagement rate
    influencers_data = collection_influencer.find().sort("statistic.engagementRate", -1)

    latest_data = get_influencer_latest()
    date_retrieve = latest_data[0]['statistic']['dateRetrieve']
    date_retrieve_datetime = datetime.strptime(date_retrieve, '%Y-%m-%d')
    formatted_date = date_retrieve_datetime.strftime('%A, %d %B %Y')

    return render_template("influencer.html", influencers=influencers_data, date_retrieve=formatted_date)

@app.route("/prediksi-influencer")
@nocache
# @login_required
def prediksi_influencer():
    influencer_id = request.args.get('influencer_id')
    lastPage = request.args.get('lastPage')
    
    # Ubah influencer_id menjadi tipe ObjectId
    try:
        influencer_id = ObjectId(influencer_id)
    except Exception as e:
        # Handle kesalahan jika influencer_id tidak valid
        print(f"Error converting influencer_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid influencer ID")

    # Cari influencer berdasarkan ID
    influencer_data = collection_influencer.find_one({"_id": influencer_id})

    if influencer_data:
        print("test")
        # Ambil hanya 7 data terakhir untuk statistik
        last_7_statistics = influencer_data.get('statistic', [])[-7:]

        # Konversi string tanggal ke objek datetime
        last_7_statistics = sorted(last_7_statistics, key=lambda x: datetime.strptime(x.get('dateRetrieve'), '%Y-%m-%d'))

        # Print the sorted list for debugging
        # print("Sorted last_7_statistics:", last_7_statistics)

        # Perbarui data influencer dengan statistik terakhir
        influencer_data['statistic'] = last_7_statistics

        # Ekstrak 'dateRetrieve' dari 'statistics' dan masukkan ke dalam array
        date_retrieve = [entry.get('dateRetrieve', '0') for entry in last_7_statistics]

        # Hitung nilai predict_engagement (sesuaikan dengan logika bisnis Anda)

        # Ekstrak 'engagementRate' dari 'statistics' dan masukkan ke dalam array
        engagement_rates = [entry.get('engagementRate', 0) for entry in last_7_statistics]

        # Ekstrak 'follower' dari 'statistics' dan masukkan ke dalam array
        followers = [entry.get('followerCount', 0) for entry in last_7_statistics]
        predict_follower = regresi.perform_linear_regression(influencer_data['statistic'], "followerCount")
        predict_follower = next(iter(predict_follower))
        predict_follower_int = int(predict_follower)
        followers.append(predict_follower_int)

        # Ekstrak 'like' dari 'statistics' dan masukkan ke dalam array
        likes = [entry.get('heartCount', 0) for entry in last_7_statistics]
        predict_likes = regresi.perform_linear_regression(influencer_data['statistic'], "heartCount")
        predict_likes = next(iter(predict_likes))
        predict_likes_int = int(predict_likes)
        likes.append(predict_likes_int)

        # Ekstrak 'views' dari 'statistics' dan masukkan ke dalam array
        views = [entry.get('totalPlayCount', 0) for entry in last_7_statistics]
        predict_views = regresi.perform_linear_regression(influencer_data['statistic'], "totalPlayCount")
        predict_views = next(iter(predict_views))
        predict_views_int = int(predict_views)
        views.append(predict_views_int)

        # Ekstrak 'comment' dari 'statistics' dan masukkan ke dalam array
        comments = [entry.get('totalCommentCount', 0) for entry in last_7_statistics]
        predict_comments = regresi.perform_linear_regression(influencer_data['statistic'], "totalCommentCount")
        predict_comments = next(iter(predict_comments))
        predict_comments_int = int(predict_comments)
        comments.append(predict_comments_int)

        # Ekstrak 'share' dari 'statistics' dan masukkan ke dalam array
        shares = [entry.get('totalShareCount', 0) for entry in last_7_statistics]
        predict_shares = regresi.perform_linear_regression(influencer_data['statistic'], "totalShareCount")
        predict_shares = next(iter(predict_shares))
        predict_shares_int = int(predict_shares)
        shares.append(predict_shares_int)

        # hitung engagement rate
        predict_engagement = (predict_likes_int + predict_comments_int + predict_shares_int) / predict_views_int
        engagement_rates.append(predict_engagement)

        # Change the date format to use double quotes
        date_retrieve = [date.replace("'", '"') for date in date_retrieve]

        # Ambil tanggal terakhir dari array
        last_date_str = date_retrieve[-1]
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        next_date = last_date + timedelta(days=1)
        next_date_str = next_date.strftime('%Y-%m-%d')

        date_retrieve.append(next_date_str)

        # Render template dengan data influencer yang ditemukan
        return render_template("prediksi-influencer.html", 
            influencer=influencer_data, lastPage = lastPage, 
            engagement_rates=engagement_rates, 
            date_retrieve=date_retrieve, 
            followers=followers, 
            likes=likes, 
            views=views, 
            comments=comments, 
            shares=shares)
    else:
        # Handle kasus ketika influencer tidak ditemukan
        return render_template("error.html", message="Influencer not found")


@app.route("/kampanye")
@nocache
# @login_required
def kampanye():
    campaigns_data = collection_campaign.find()

    # Create a list to store campaign details with video count
    campaigns = []
    campaign_ids = []  # Initialize an empty list to store campaign IDs

    # Calculate the count for each campaign
    for campaign_data in campaigns_data:
        campaign_name = campaign_data.get('namaCampaign', '')
        video_count = len(campaign_data.get('video', []))
        id = campaign_data.get('_id', '')

        # Append campaign details to the campaigns list
        campaigns.append({
            'namaCampaign': campaign_name,
            'videoCount': video_count,
            'id': id,
        })

        # Append campaign ID to the campaign_ids list
        campaign_ids.append(id)
    
    flash_messages = get_flashed_messages(with_categories=True)

    return render_template("kampanye.html", campaigns=campaigns, campaign_ids=campaign_ids)


@app.route("/detail_kampanye")
@nocache
# @login_required
def detail_kampanye():
    campaign_id = request.args.get('campaign_id')

    try:
        campaign_id = ObjectId(campaign_id)
    except Exception as e:
        # Handle kesalahan jika campaign_id tidak valid
        print(f"Error converting campaign_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid Campaign ID")

    # Cari campaign berdasarkan ID
    campaign_data = collection_campaign.find_one({"_id": campaign_id})

    formatted_date = '-'  # Default value for formatted_date

    if campaign_data and 'video' in campaign_data and campaign_data['video']:

        date_retrieve = campaign_data['video'][0].get('dateRetrieve', None)

        # Check if date_retrieve is not None and not an empty string
        if date_retrieve:
            date_retrieve_datetime = datetime.strptime(date_retrieve, '%Y-%m-%d %H:%M:%S')
            formatted_date = date_retrieve_datetime.strftime('%A, %d %B %Y')

    flash_messages = get_flashed_messages(with_categories=True)

    return render_template("detail_kampanye.html", campaign=campaign_data, formatted_date=formatted_date)


@app.route('/save_posts', methods=['POST'])
@nocache
def save_posts():
    campaign_id = request.args.get('campaign_id')

    try:
        campaign_id = ObjectId(campaign_id)
    except Exception as e:
        print(f"Error converting campaign_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid Campaign ID")

    if request.method == 'POST':
        video_urls = request.form.getlist('videoURLs[]')

        try:
            collection_campaign.update_one(
                {"_id": campaign_id},
                {"$push": {"video": {"$each": [{"video_url": url} for url in video_urls]}}}
            )

            # Get count of videos before the update
            campaign_data_before = collection_campaign.find_one({"_id": campaign_id})
            countbefore = len(campaign_data_before.get('video', []))

            sync_video_route()

            # Get count of videos after the update
            campaign_data_after = collection_campaign.find_one({"_id": campaign_id})
            countafter = len(campaign_data_after.get('video', []))

            if countbefore != countafter:
                # If counts are different, show a flash message
                flash("Failed to retrieve data for new URLs.", "error")

            return redirect(url_for('detail_kampanye', campaign_id=campaign_id))

        except Exception as e:
            print(f"Error updating campaign: {e}")
            flash("Error updating campaign", "error")
            return redirect(url_for('detail_kampanye', campaign_id=campaign_id))


        

@app.route('/add_campaign', methods=['POST'])
def add_campaign():
    if request.method == 'POST':
        name = request.form.get('addCampaignName')

        # Ambil idCampaign terakhir dari database
        last_campaign = collection_campaign.find_one(sort=[("idCampaign", -1)])
        if last_campaign:
            last_id = last_campaign['idCampaign']
        else:
            last_id = 0

        # Tambahkan 1 untuk mendapatkan idCampaign baru
        new_id = last_id + 1

        # Simpan ke database MongoDB dengan idCampaign yang baru
        collection_campaign.insert_one({'idCampaign': new_id, 'namaCampaign': name})

    return redirect(url_for('kampanye'))

@app.route("/edit_kampanye", methods=["POST"])
@nocache
def edit_kampanye():
    campaign_id = request.args.get('campaign_id')

    try:
        campaign_id = ObjectId(campaign_id)
    except Exception as e:
        print(f"Error converting campaign_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid Campaign ID")

    if request.method == "POST":
        edited_campaign_name = request.form.get('edited_campaign_name')

        try:
            campaign_id = ObjectId(campaign_id)
        except Exception as e:
            print(f"Error converting campaign_id to ObjectId: {e}")
            return render_template("error.html", message="Invalid Campaign ID")

        try:
            collection_campaign.update_one({"_id": campaign_id}, {"$set": {"namaCampaign": edited_campaign_name}})
            return redirect(url_for('kampanye'))
        except Exception as e:
            print(f"Error editing campaign")
            return redirect(url_for('kampanye'))


@app.route("/edit_video", methods=["POST"])
@nocache
def edit_video():
    campaign_id = request.args.get('campaign_id')
    video_url= request.args.get('video_url')

    try:
        campaign_id = ObjectId(campaign_id)
    except Exception as e:
        # Handle kesalahan jika campaign_id tidak valid
        print(f"Error converting campaign_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid Campaign ID")

    if request.method == "POST":
        edited_video_url = request.form.get('edited_video_url')

        try:
            collection_campaign.update_one(
                {'_id': campaign_id, 'video.video_url': video_url},
                {'$set': {'video.$.video_url': edited_video_url}}
            )
            # Redirect to the page displaying the campaigns
            return redirect(url_for('detail_kampanye', campaign_id=campaign_id))
        except Exception as e:
            print(f"Error editing campaign: {e}")
            return redirect(url_for('detail_kampanye', campaign_id=campaign_id))


@app.route('/delete_kampanye', methods=['GET'])
@nocache
def delete_kampanye():
    campaign_id = request.args.get('campaign_id')

    try:
        campaign_id = ObjectId(campaign_id)
        collection_campaign.delete_one({'_id': campaign_id})
        return redirect(url_for('kampanye'))
    except Exception as e:
        print(f"Error deleting campaign")
        return redirect(url_for('kampanye'))

@app.route('/delete_video', methods=['GET'])
@nocache
def delete_video():
    campaign_id = request.args.get('campaign_id')
    video_url = request.args.get('video_url')

    try:
        campaign_id = ObjectId(campaign_id)
        collection_campaign.update_one(
            {'_id': campaign_id},
            {'$pull': {'video': {'video_url': video_url}}}
        )
        return redirect(url_for('detail_kampanye', campaign_id=campaign_id))
    except Exception as e:
        print(f"Error deleting video: {e}")
        return redirect(url_for('detail_kampanye', campaign_id=campaign_id))

@app.route('/sync_influencer')
@nocache
def sync_influencer():
    latest_data = get_influencer_latest()
    latest_data_jsonify = jsonify(latest_data)

    # date_retrieve = latest_data[0]['statistic']['dateRetrieve']
    
    # Save the latest data to a JSON file
    save_path = 'latest_data_influencer.json'
    with open(save_path, 'w') as json_file:
        json_file.write(latest_data_jsonify.get_data(as_text=True))

    # Call the generate_dummy function
    generate_dummy.generate_dummy()   

    # Inside your route function
    return redirect(url_for('influencer'))

def get_influencer_latest():
    # Aggregate to get the latest statistic for each document
    pipeline = [
        {"$unwind": "$statistic"},
        {"$sort": {"statistic.dateRetrieve": -1}},
        {"$group": {
            "_id": "$_id",
            "username": {"$first": "$username"},
            "nickname": {"$first": "$nickname"},
            "avatar": {"$first": "$avatar"},
            "statistic": {"$first": "$statistic"}
        }},
        {"$project": {
            "_id": {"$toString": "$_id"},
            "username": 1,
            "nickname": 1,
            "avatar": 1,
            "statistic": 1
        }}
    ]

    cursor = collection_influencer.aggregate(pipeline)

    # Convert the cursor to a list of documents
    latest_data = list(cursor)

    return latest_data

    # # Iterate through the cursor to print or process the results
    # for document in cursor:
    #     print(f"Latest data for {document['username']}: {document}")

def job():
    print("sync influencers")
    sync_influencer()
    

scheduler = BackgroundScheduler()
scheduler.add_job(job, trigger="cron", hour=2, minute=00)
scheduler.start()

@app.route('/sync_video')
@nocache
def sync_video_route():
    campaign_id = request.args.get('campaign_id')

    try:
        campaign_id = ObjectId(campaign_id)
    except Exception as e:
        print(f"Error converting campaign_id to ObjectId: {e}")
        return render_template("error.html", message="Invalid Campaign ID")

    try:
        # Get the existing campaign data before the sync
        campaign_data_before = collection_campaign.find_one({"_id": campaign_id})
        
        # Store the count before the sync
        countbefore = len(campaign_data_before.get('video', []))

        # Attempt to sync the video data
        try:
            sync_video(campaign_data_before, collection_campaign)
        except Exception as sync_error:
            print(f"Error during sync_video: {sync_error}")

            flash("There was an error during video sync.", "warning")
            
            # Redirect to the campaign details page
            return redirect(url_for('detail_kampanye', campaign_id=campaign_id))

        # Get the campaign data after the sync
        campaign_data_after = collection_campaign.find_one({"_id": campaign_id})
        
        # Store the count after the sync
        countafter = len(campaign_data_after.get('video', []))

        # Check if the video count changed
        if countbefore != countafter:
            flash("There was an error with some URLs.", "error")

        # Redirect to the campaign details page
        return redirect(url_for('detail_kampanye', campaign_id=campaign_id))

    except Exception as e:
        print(f"Error updating campaign: {e}")
        flash("Error updating campaign", "error")
        return redirect(url_for('detail_kampanye', campaign_id=campaign_id))



@app.route('/sync_campaign')
@nocache
def sync_campaign():
    campaign_ids = request.args.getlist('campaign_ids')

    for campaign_id in campaign_ids:
        try:
            campaign_id_obj = ObjectId(campaign_id)
        except Exception as e:
            print(f"Error converting campaign_id to ObjectId: {e}")
            return render_template("error.html", message="Invalid Campaign ID")

        campaign_data = collection_campaign.find_one({"_id": campaign_id_obj})
        sync_video(campaign_data, collection_campaign)

    return redirect(url_for('kampanye'))

    

if __name__ == '__main__':
    app.run(debug=True)
