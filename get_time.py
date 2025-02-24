import requests
import datetime
from dotenv import load_dotenv
import os

load_dotenv()
TRACKT_API_KEY = os.getenv("TRACKT_API_KEY")
HEADERS = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "trakt-api-key": TRACKT_API_KEY
}


def format_date(dt):
    # Remove leading zeros from hour using string manipulation instead of %-I
    hour = dt.strftime("%I").lstrip("0")
    suffix = lambda n: str(n) + ("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))
    return dt.strftime(f"%A {suffix(dt.day)} of %b at {hour}:%M%p")


def get_show_poster(slug):
    resp = requests.get(f"https://api.trakt.tv/shows/{slug}?extended=images", headers=HEADERS)
    if resp.status_code == 200:
        poster = resp.json().get("images", {}).get("poster", "")
        if isinstance(poster, dict):
            poster = poster.get("thumb") or poster.get("full", "")
        elif isinstance(poster, list):
            poster = poster[0] if poster else ""
        return f"https:{poster}" if poster and not poster.startswith("http") else poster
    return None


def get_show_slug(show_name):
    resp = requests.get(f"https://api.trakt.tv/search/show?query={show_name}", headers=HEADERS)
    data = resp.json() if resp.status_code == 200 else []
    return data[0]["show"]["ids"]["slug"] if data and "show" in data[0] else None


def get_episode_details(slug, season, episode):
    resp = requests.get(f"https://api.trakt.tv/shows/{slug}/seasons/{season}/episodes/{episode}?extended=full",
                        headers=HEADERS)
    return resp.json() if resp.status_code == 200 else {}


def get_next_episode(slug):
    resp = requests.get(f"https://api.trakt.tv/shows/{slug}/seasons?extended=full,episodes", headers=HEADERS)
    if resp.status_code != 200:
        return None

    episodes = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for season in resp.json():
        s_num = season.get("number")
        for ep in season.get("episodes", []):
            air_date = ep.get("first_aired")
            if not air_date:
                air_date = get_episode_details(slug, s_num, ep.get("number")).get("first_aired")
            if not air_date:
                continue

            try:
                air_dt = datetime.datetime.fromisoformat(air_date.replace("Z", "+00:00"))
                if air_dt > now:
                    episodes.append({
                        "season": s_num,
                        "episode": ep.get("number"),
                        "title": ep.get("title", "N/A"),
                        "air_time": air_dt
                    })
            except ValueError:
                continue

    return min(episodes, key=lambda x: x["air_time"]) if episodes else None


def get_show_info(show_name):
    slug = get_show_slug(show_name)
    if not slug:
        return {"name": show_name, "poster": "", "next_episode": "Show not found"}

    poster_url = get_show_poster(slug) or f"https://via.placeholder.com/300x450?text={show_name}"
    next_ep = get_next_episode(slug)

    if next_ep:
        # Pass the ISO format string directly
        next_episode_str = next_ep["air_time"].isoformat()
    else:
        next_episode_str = ""

    return {
        "name": show_name,
        "poster": poster_url,
        "next_episode": next_episode_str
    }