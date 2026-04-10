def generate_map_url(lat: float, lng: float) -> str:
    return f"https://www.google.com/maps?q={lat},{lng}&output=embed"