from flask import Flask, render_template, request, make_response, session, redirect, url_for
from bson import ObjectId
from pymongo import MongoClient
from functools import wraps, update_wrapper
from datetime import datetime
from flask_bcrypt import Bcrypt
import secrets
import json

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = secrets.token_hex(16) 

client = MongoClient('mongodb://localhost:27017/')  
db = client['tiktok_analysis']  
collection_influencer = db['user_api']  
collection_video = db['video_api'] 
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

    print("Tesss")

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
        return render_template('login.html', error='Invalid credentials')

@app.route('/logout')
def logout():
    # Clear the user session to log out the user
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/home")
@nocache
@login_required
def home():
    print("Session in home route:", session)
    total_influencer_data = collection_influencer.count_documents({})
    total_campaign_data = collection_video.count_documents({})
    influencers_data = collection_influencer.find().sort("statistic.engagementRate", -1)
    return render_template("home.html", total_influencer=total_influencer_data, influencers=influencers_data, total_campaign=total_campaign_data)

@app.route("/influencer")
@nocache
@login_required
def influencer():
    # Mengambil data influencer dari MongoDB dan mengurutkannya berdasarkan engagement rate
    influencers_data = collection_influencer.find().sort("statistic.engagementRate", -1)

    return render_template("influencer.html", influencers=influencers_data)

@app.route("/prediksi-influencer")
@nocache
# @login_required
def prediksi_influencer():
    influencer_id = request.args.get('influencer_id')
    
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
        print("Sorted last_7_statistics:", last_7_statistics)

        # Perbarui data influencer dengan statistik terakhir
        influencer_data['statistic'] = last_7_statistics

        # Ekstrak 'dateRetrieve' dari 'statistics' dan masukkan ke dalam array
        date_retrieve = [entry.get('dateRetrieve', '0') for entry in last_7_statistics]

        # Ekstrak 'engagementRate' dari 'statistics' dan masukkan ke dalam array
        engagement_rates = [entry.get('engagementRate', 0) for entry in last_7_statistics]

        # Ekstrak 'follower' dari 'statistics' dan masukkan ke dalam array
        followers = [entry.get('followerCount', 0) for entry in last_7_statistics]

        # Ekstrak 'like' dari 'statistics' dan masukkan ke dalam array
        likes = [entry.get('heartCount', 0) for entry in last_7_statistics]

        # Ekstrak 'views' dari 'statistics' dan masukkan ke dalam array
        views = [entry.get('totalPlayCount', 0) for entry in last_7_statistics]

        # Ekstrak 'comment' dari 'statistics' dan masukkan ke dalam array
        comments = [entry.get('totalCommentCount', 0) for entry in last_7_statistics]

        # Ekstrak 'share' dari 'statistics' dan masukkan ke dalam array
        shares = [entry.get('totalShareCount', 0) for entry in last_7_statistics]

        # # Ekstrak 'dateRetrieve' dari 'statistics' dan masukkan ke dalam array
        # date_retrieve = [entry.get('dateRetrieve', '0') for entry in last_7_statistics]

        # Change the date format to use double quotes
        date_retrieve = [date.replace("'", '"') for date in date_retrieve]

        print(date_retrieve)

        # Render template dengan data influencer yang ditemukan
        return render_template("prediksi-influencer.html", 
            influencer=influencer_data, 
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
@login_required
def kampanye():
    campaigns_data = collection_video.find()

    # # Create a list to store campaign details with video count
    # campaigns_data = []

    # # Calculate the count for each campaign
    # for campaign_data in campaigns_data:
    #     campaign_name = campaign_data.get('namaCampaign', '')
    #     video_count = len(campaign_data.get('video', []))
    #     campaigns.append({
    #         'namaCampaign': campaign_name,
    #         'videoCount': video_count
    #     })

    return render_template("kampanye.html", campaigns=campaigns_data)

@app.route("/detail_kampanye")
@nocache
@login_required
def detail_kampanye():
    return render_template("detail_kampanye.html")

if __name__ == '__main__':
    app.run(debug=True)
