from flask import Flask, render_template, request, make_response
from bson import ObjectId
from pymongo import MongoClient
from functools import wraps, update_wrapper
from datetime import datetime

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')  
db = client['tiktok_analysis']  
collection_influencer = db['user_api']  
collection_campaign = db['video_api'] 

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
    total_campaign_data = collection_campaign.count_documents({})
    influencers_data = collection_influencer.find()
    influencers_sorted = sorted(influencers_data, key=lambda x: x['statistic'][-1]['engagementRate'], reverse=True)
    top_5_influencers = influencers_sorted[:5]
    return render_template("home.html", total_influencer = total_influencer_data, influencers = top_5_influencers, total_campaign = total_campaign_data)

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
    campaigns_data = collection_campaign.find()

    # Create a list to store campaign details with video count
    campaigns = []

    # Calculate the count for each campaign
    for campaign_data in campaigns_data:
        campaign_name = campaign_data.get('namaCampaign', '')
        video_count = len(campaign_data.get('video', []))
        campaigns.append({
            'namaCampaign': campaign_name,
            'videoCount': video_count
        })

    return render_template("kampanye.html", campaigns=campaigns)

@app.route("/detail_kampanye")
@nocache
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

    if campaign_data:
        # Render template dengan data campaign yang ditemukan
        return render_template("detail_kampanye.html", campaign=campaign_data)
    else:
        # Handle kasus ketika campaign tidak ditemukan
        return render_template("error.html", message="Campaign not found")
if __name__ == '__main__':
    app.run(debug=True)
