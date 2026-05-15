import streamlit as st
from utils.ocr import extract_text_from_image
from utils.matcher import find_medicine
from PIL import Image

st.set_page_config(page_title="Medicine Identifier", layout="centered")

st.title("💊 Medicine Identifier AI App")
st.write("Upload medicine image to detect name, composition, uses")

uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)

    with st.spinner("Processing image..."):
        # save temporarily
        temp_path = "temp_image.jpg"
        image.save(temp_path)

        # OCR
        extracted_text = extract_text_from_image(temp_path)

        st.subheader("📄 Extracted Text")
        st.write(extracted_text)

        # Matching
        result = find_medicine(extracted_text)

        if result:
            st.success("Medicine Found!")

            st.write("### 💊 Name:", result["medicine_name"])
            st.write("### 🧪 Composition:", result["composition"])
            st.write("### 💡 Uses:", result["uses"])
            st.write("### ⚠️ Side Effects:", result["side_effects"])
            st.write("### 🏭 Manufacturer:", result["manufacturer"])
            st.write("### 🎯 Confidence:", result["confidence"])
        else:
            st.error("Medicine not found in database")