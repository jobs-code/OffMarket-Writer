import io
import ollama
import streamlit as st
from PIL import Image

MODEL = "gemma3:4b"

st.set_page_config(page_title="OffMarket Writer", page_icon="🏠")
st.title("🏠 OffMarket Writer")
st.caption("Photos in, listing out. Runs 100% locally with Gemma 3. Your listings stay off-market until you say so.")


def shrink(file):
    img = Image.open(file).convert("RGB")
    img.thumbnail((896, 896))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=85)
    return buf.getvalue()


files = st.file_uploader(
    "Property photos (max 6)",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

c1, c2 = st.columns(2)
with c1:
    location = st.text_input("Neighborhood / city")
    price = st.text_input("Price")
    beds = st.text_input("Bedrooms")
with c2:
    baths = st.text_input("Bathrooms")
    sqft = st.text_input("Square footage")
    tone = st.selectbox(
        "Tone",
        ["Warm & inviting", "Luxury", "Concise & professional", "Investor-focused"],
    )
extra = st.text_area("Extra facts (parking, renovations, schools, etc.)")

if st.button("Generate listing", type="primary"):
    if not files:
        st.warning("Please upload at least one property photo.")
        st.stop()

    notes = []
    with st.spinner("Looking at photos..."):
        for i, f in enumerate(files[:6], 1):
            resp = ollama.chat(
                model=MODEL,
                messages=[{
                    "role": "user",
                    "content": (
    "Describe this real estate photo in 2-3 factual sentences. "
    "Start directly with the description, with no introduction. "
    "Do not use lists or labels. Mention the room type, materials, "
    "finishes, light, and notable features only if clearly visible. Do not guess."
),
                    "images": [shrink(f)],
                }],
            )
            notes.append(f"Photo {i}: {resp['message']['content'].strip()}")

    facts = f"""Location: {location}
Price: {price}
Bedrooms: {beds}
Bathrooms: {baths}
Square footage: {sqft}
Extra facts: {extra}"""

    prompt = f"""You are an expert real estate copywriter. Write a property listing in a {tone} tone.

PHOTO NOTES:
{chr(10).join(notes)}

AGENT-PROVIDED FACTS:
{facts}

Rules:
- Start with a short headline, then a 120-180 word description, then 5 bullet-point highlights.
- Use ONLY information from the photo notes and agent facts. Never invent features, numbers, or amenities.
- Follow fair housing rules: no language about the type of people who should or shouldn't live there (family, age, religion, race, etc.).
- Skip any field left blank.
- Do not add intros like "Here's the listing". Output only the listing.
- Avoid unsupported claims such as "secure", "luxury" or "newly renovated" unless stated in the agent facts."""

    with st.spinner("Writing listing..."):
        out = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
        listing = out["message"]["content"]

    with st.expander("What the AI saw in each photo"):
        st.write("\n\n".join(notes))

    st.subheader("Your listing")
    st.text_area("Copy-ready", listing, height=350)
    st.download_button("Download .txt", listing, file_name="listing.txt")