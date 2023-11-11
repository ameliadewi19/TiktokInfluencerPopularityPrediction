from flask import Flask, render_template, request, make_response
from bson import ObjectId
from pymongo import MongoClient
from functools import wraps, update_wrapper
from datetime import datetime

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')  
db = client['tiktok_analysis']  
collection_influencer = db['user_api']  
collection_video = db['video_api'] 

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

@app.route("/")
@app.route("/login")
@nocache
def login():
    return render_template("login.html")

@app.route("/home")
@nocache
def home():
    total_influencer_data = collection_influencer.count_documents({})
    total_campaign_data = collection_video.count_documents({})
    influencers_data = collection_influencer.find().sort("statistic.engagementRate", -1).limit(5)
    return render_template("home.html", total_influencer = total_influencer_data, influencers = influencers_data, total_campaign = total_campaign_data)

@app.route("/influencer")
@nocache
def influencer():
    influencers_data = collection_influencer.find()
    return render_template("influencer.html", influencers=influencers_data)

@app.route("/prediksi-influencer")
@nocache
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
        # Render template dengan data influencer yang ditemukan
        return render_template("prediksi-influencer.html", influencer=influencer_data)
    else:
        # Handle kasus ketika influencer tidak ditemukan
        return render_template("error.html", message="Influencer not found")

@app.route("/kampanye")
@nocache
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
def detail_kampanye():
    return render_template("detail_kampanye.html")

if __name__ == '__main__':
    app.run(debug=True)
