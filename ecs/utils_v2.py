from io import BytesIO

import requests
import streamlit as st
from ddgs import DDGS
from PIL import Image


@st.cache_data(show_spinner=False)
def get_character_image(name: str) -> str:
    queries = [
        f'"{name}" headshot',
        f'"{name}" character close-up',
        f'"{name}" movie still portrait',
    ]
    bad = {
        "logo",
        "symbol",
        "poster",
        "banner",
        "wallpaper",
        "funko",
        "nocookie",
        "static",
    }

    for q in queries:
        try:
            for hit in DDGS().images(
                q,
                region="us-en",
                safesearch="moderate",
                size="Large",
                type_image="transparent",
                max_results=20,
            ):
                url = hit["image"]
                if any(tok in url.lower() for tok in bad) or hit.get("width", 0) < 400:
                    continue
                response = requests.get(url)
                if (
                    response.status_code != 200
                ):  # sometimes Streamlit won't show the image
                    continue  # if you get the url, but Streamlit will show the image
                else:  # if you give it the image content
                    print(
                        f"image url: {url}", flush=True
                    )  # flush for ECS task -> Cloudwatch logs
                    try:  # sometimes image won't load up correctly
                        Image.open(BytesIO(response.content))
                    except Exception as e:
                        print(
                            f"image url still broken: {url}", flush=True
                        )  # flush for ECS task -> Cloudwatch logs
                        continue
                    return url
        except Exception as e:
            st.warning(f"DDGS failed on '{q}': {e}")
            raise e
