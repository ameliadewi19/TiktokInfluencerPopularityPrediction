const { TiktokDL } = require("@tobyg74/tiktok-api-dl");
const fs = require("fs");

const inputArray = JSON.parse(process.argv[2]);

const downloadTikTokVideos = async (tiktokUrls) => {
  const results = [];

  for (const url of tiktokUrls) {
    let retryCount = 0;
    let success = false;
    let result;

    while (retryCount < 3 && !success) {
      try {
        result = await TiktokDL(url, {
          version: "v1" // version: "v1" | "v2" | "v3"
        });
        console.log(`Downloaded video from ${url}`);
        success = true;
      } catch (error) {
        console.error(`Error downloading video from ${url}:`, error);
        retryCount++;
      }
    }

    if (!success) {
      console.warn(`Failed to download video from ${url} after 3 attempts. Skipping.`);
    } else if (result.status !== 'error') {
      results.push(result);
    }
  }

  // Save the results to a JSON file
  const currentDate = new Date().toISOString().slice(0, 10);
  const filename = `./video_json/Video_Before_ETL.json`;

  // Filter out objects with status:error before saving to JSON
  const filteredResults = results.filter(result => result.status !== 'error');

  fs.writeFileSync(filename, JSON.stringify(filteredResults, null, 2));
  console.log("Results saved to video_results.json");
};

downloadTikTokVideos(inputArray);
