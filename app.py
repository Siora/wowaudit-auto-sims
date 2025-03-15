import urllib.request
import urllib.error
import urllib.parse
import json
import re
import os
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

WOWAUDIT_API_TOKEN = os.environ['WOWAUDIT_API_TOKEN']
POLL_INTERVAL = 30
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
RAIDBOTS_VERSION = "live"

def http_request(method, url, headers=None, data=None):
    """
    Synchronously perform an HTTP request.
    Data (if provided) should be a string; it is encoded to bytes.
    """
    if data is not None:
        if isinstance(data, str):
            data = data.encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req) as resp:
        resp_data = resp.read().decode('utf-8')
        return json.loads(resp_data)

async def async_http_request(method, url, headers=None, data=None):
    """
    Wrap the synchronous http_request in an asyncio thread.
    """
    return await asyncio.to_thread(http_request, method, url, headers, data)

async def get_region():
    url = "https://wowaudit.com/v1/team"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": WOWAUDIT_API_TOKEN
    }
    try:
        data = await async_http_request("GET", url, headers)
        match = re.search(r"https://wowaudit\.com/([^/]+)/", data["url"])
        if match:
            return match.group(1)

        return None
    except Exception as e:
        print(f"Error fetching team: {e}")
        return None

async def get_latest_raid():
    url = "https://wowaudit.com/api/instances?kind=live"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": WOWAUDIT_API_TOKEN
    }
    try:
        data = await async_http_request("GET", url, headers)
        for raid in data:
            if raid["current"]:
                return raid

        return None
    except Exception as e:
        print(f"Error fetching team: {e}")
        return None

async def get_characters():
    """
    Retrieve the list of characters from the wowaudit API.
    """
    url = "https://wowaudit.com/v1/characters"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": WOWAUDIT_API_TOKEN
    }
    try:
        data = await async_http_request("GET", url, headers)
        return data
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

def start_sim_with_browser(region, realm, char_name, raid, difficulty):
    """Starts a Raidbots simulation using a headless browser and returns the sim_id."""
    url = f"https://www.raidbots.com/simbot/droptimizer?region={region}&realm={realm}&name={char_name}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    print(f"Navigate to raidbots.com")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    time.sleep(5)  # Wait for page to load

    # Execute JavaScript to select the raid and difficulty
    script = '''
    document.querySelectorAll('#instanceList .Box').forEach((e) => {
        if (e.innerText.toLowerCase() == "#instance#") {
            e.click();
        }
    });
    '''
    script = script.replace("#instance#", raid["name"].lower())

    print("Select raid " + raid["name"])
    driver.execute_script(script)
    time.sleep(10)

    script = '''
        Array.from(document.querySelectorAll(".Heading")).find((e) => e.innerText.toLowerCase() === "raid difficulty")
            .closest(".Box").querySelectorAll('.Text:first-child').forEach((e) => {
                if (e.innerText.toLowerCase() == "#difficulty#") {
                    e.closest(".Box").click();
                }
            });
        '''
    script = script.replace("#difficulty#", difficulty.lower())

    print("Select difficulty " + difficulty)
    driver.execute_script(script)
    time.sleep(10)

    script = '''
        document.querySelectorAll('.Button').forEach((e) => { if (e.innerText.toLowerCase() == "run droptimizer") { e.click(); } })
        '''

    print("Start sim")
    driver.execute_script(script)
    time.sleep(10)

    sim_url = driver.current_url
    driver.quit()

    sim_id = sim_url.split("/")[-1]  # Extract sim_id from URL
    return sim_id

async def poll_sim(sim_id, character_name, difficulty):
    """
    Poll the raidbots sim status periodically and print progress.
    Completion is determined when the response returns {"message": "No job found"}.
    """
    url = f"https://www.raidbots.com/api/job/{sim_id}"
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT
    }
    while True:
        try:
            response = await async_http_request("GET", url, headers)
            # Check if the sim has completed.
            if isinstance(response, dict) and response.get("message") == "No job found":
                print(f"Sim {difficulty} {sim_id} for {character_name} completed.")
                break

            # If job details are available, print progress.
            if "job" in response:
                job = response["job"]
                state = job.get("state", "unknown")
                progress = job.get("progress", "unknown")
                total = "unknown"
                position = "unknown"
                if "queue" in response:
                    total = response["queue"].get("total", "unknown")
                    position = response["queue"].get("position", "unknown")
                print(
                    f"Sim {difficulty} {sim_id} for {character_name} is {state} (queue {position}/{total}) with progress {progress}")
            else:
                print(f"Sim {difficulty} {sim_id} for {character_name} progress: {response}")

        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Sim {difficulty} {sim_id} for {character_name} completed.")
                break
            else:
                print(f"Unexpected HTTP error for sim {difficulty} {sim_id}: {e}")

        await asyncio.sleep(POLL_INTERVAL)


async def upload_wishlist(character, report_id):
    """
    Upload the wishlist to wowaudit after sim completion.
    """
    url = "https://wowaudit.com/v1/wishlists"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": WOWAUDIT_API_TOKEN
    }
    payload = {
        "report_id": report_id,
        "character_id": character["id"],
        "character_name": character["name"],
        "configuration_name": "Single Target",
        "replace_manual_edits": True,
        "clear_conduits": True
    }
    data_str = json.dumps(payload)
    try:
        response = await async_http_request("POST", url, headers, data_str)
        print(f"Wishlist uploaded for {character['name']}: {response}")
    except Exception as e:
        print(f"Error uploading wishlist for {character['name']}: {e}")


async def process_character(region, character, raid):
    """
    Process a single character:
      - Fetch gear from raidbots.
      - Start a sim.
      - Poll until the sim is complete.
      - Upload the wishlist to wowaudit.
    """
    name = character["name"]
    realm = character["realm"]
    character_name = f"{name}-{realm}"
    print(f"Processing character: {character_name}")

    for difficulty in ["normal", "heroic", "mythic"]:
        sim_id = start_sim_with_browser(region, realm, name, raid, difficulty)
        if not sim_id:
            print(f"Sim {difficulty} response for {character_name} missing simId.")
            break

        print(f"Sim {difficulty} started for {character_name}, sim_id: {sim_id}")
        await poll_sim(sim_id, character_name, difficulty)
        await upload_wishlist(character, sim_id)


async def main():
    """
    Main function: fetch all characters and start processing them concurrently.
    """
    region = await get_region()
    if not region:
        raise "No region found"

    raid = await get_latest_raid()
    if not raid:
        raise "No raid found"

    raid_name = raid["name"]
    print(f"Run for raid {raid_name} on region {region}")

    characters = await get_characters()
    if not characters:
        print("No characters to process.")
        return

    # Create a task for each character.
    tasks = [asyncio.create_task(process_character(region, character, raid)) for character in characters if character["role"] != "Heal"]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
