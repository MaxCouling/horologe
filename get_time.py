import requests
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TRACKT_API_KEY = os.getenv("TRACKT_API_KEY")
# Set up your Trakt API headers
HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": TRACKT_API_KEY
}


def get_show_slug(show_name):
    """Search for a show and return its slug.
       Uses: GET /search/show?query={show_name}"""
    url = f"https://api.trakt.tv/search/show?query={show_name}"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print("Error searching for show.")
        return None
    data = resp.json()
    if data and "show" in data[0]:
        return data[0]["show"]["ids"]["slug"]
    return None


def get_seasons(slug):
    """Retrieve all seasons with episode data using extended=full,episodes.
       Uses: GET /shows/{slug}/seasons?extended=full,episodes"""
    url = f"https://api.trakt.tv/shows/{slug}/seasons?extended=full,episodes"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code != 200:
        print("Error retrieving seasons.")
        return []
    return resp.json()


def get_episode_details(slug, season, episode):
    """Fallback: Retrieve detailed info for a single episode.
       Uses: GET /shows/{slug}/seasons/{season}/episodes/{episode}?extended=full"""
    url = f"https://api.trakt.tv/shows/{slug}/seasons/{season}/episodes/{episode}?extended=full"
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json()
    return {}


def flatten_episodes(seasons_data, slug):
    """Flatten seasons into a single list of episodes.
       If an episode's 'first_aired' value is missing, it falls back to a per-episode call."""
    episodes = []
    for season in seasons_data:
        s_num = season.get("number")
        for ep in season.get("episodes", []):
            air = ep.get("first_aired")
            if not air or air == "N/A":
                detailed = get_episode_details(slug, s_num, ep.get("number"))
                air = detailed.get("first_aired", None)
            episodes.append({
                "season": s_num,
                "episode": ep.get("number"),
                "title": ep.get("title", "N/A"),
                "first_aired": air  # Expected as an ISO string (UTC)
            })
    episodes.sort(key=lambda x: (x["season"] or 0, x["episode"] or 0))
    return episodes


def print_episodes(episodes):
    print("All Episodes:")
    for ep in episodes:
        season = ep["season"]
        episode = ep["episode"]
        title = ep["title"]
        air = ep["first_aired"] if ep["first_aired"] else "N/A"
        print(f"S{season:02}E{episode:02}: {title} - Airs on {air}")


def determine_next_episode(episodes):
    """Return the first episode whose air time (UTC) is in the future.
       The air time is converted from its ISO string to an aware datetime object in UTC."""
    now = datetime.datetime.now(datetime.timezone.utc)
    next_ep = None
    for ep in episodes:
        air_str = ep.get("first_aired")
        if air_str:
            try:
                # Replace "Z" with "+00:00" to produce an aware datetime in UTC
                utc_dt = datetime.datetime.fromisoformat(air_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if utc_dt > now:
                if next_ep is None or utc_dt < next_ep["utc_dt"]:
                    next_ep = {"episode_info": ep, "utc_dt": utc_dt}
    return next_ep


def get_time(show_name):
    show_name = show_name.strip()
    slug = get_show_slug(show_name)
    if not slug:
        print("Show not found!")
        return

    seasons_data = get_seasons(slug)
    if not seasons_data:
        print("No season data available!")
        return

    episodes = flatten_episodes(seasons_data, slug)
    if not episodes:
        print("No episode data available!")
        return

    print_episodes(episodes)
    next_ep = determine_next_episode(episodes)

    if next_ep:
        ep_info = next_ep["episode_info"]
        utc_dt = next_ep["utc_dt"]
        # Convert UTC time to local time (using the system's local timezone)
        local_dt = utc_dt.astimezone()
        print("\nNext upcoming episode:")
        print(f"  S{ep_info['season']:02}E{ep_info['episode']:02}: {ep_info['title']}")
        print(f"  Air time (UTC):   {utc_dt.isoformat()}")
        print(f"  Air time (Local): {local_dt.isoformat()}")
        return [ep_info, utc_dt.isoformat(), local_dt.isoformat()]
    else:
        #print("No upcoming episodes found. All episodes have aired.")
        return("No upcoming episodes found. All episodes have aired.")