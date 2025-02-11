import pytesseract
import os
import requests
import concurrent.futures
import logging
from io import BytesIO
from pdf2image import convert_from_bytes
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_pdf_to_images(pdf_url, threadNumber):
    response = requests.get(pdf_url)
    pdf_content = BytesIO(response.content)
    pages = convert_from_bytes(pdf_content.getvalue())
    for i, page in enumerate(pages):
        page.save(f"page_{i}_{threadNumber}.jpg", "JPEG")
    # print("done")
    return len(pages)


def perform_ocr_on_pdf(pdf_url, threadNumber):
    num_pages = convert_pdf_to_images(pdf_url, threadNumber)
    results = []
    # chars_to_remove = [
    #     "*",
    #     ".",
    #     "|",
    #     "`",
    #     "_",
    #     "»",
    #     "~",
    #     "'",
    #     ",",
    #     "#",
    #     "“",
    #     '"',
    #     "\\",
    #     "/",
    #     "\n",
    #     "‘",
    # ]
    # trans_table = str.maketrans("", "", "".join(chars_to_remove))
    for i in range(num_pages):
        image_path = f"page_{i}_{threadNumber}.jpg"
        image = Image.open(image_path)
        # text = pytesseract.image_to_string(image)
        # --psm 6 --oem 3
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        text = " ".join(data["text"])
        confidences = [int(conf) for conf in data["conf"] if conf != "-1"]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        # print(text)
        results.append(
            {
                "page": i + 1,
                "text": text,
                # "clean_text": text.translate(trans_table),
                "confidence": round(avg_confidence, 2),
            }
        )
        image.close()
        os.remove(image_path)
    return results


def parallel_ocr(pdf_url, num_runs=3):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_runs) as executor:
        futures = [
            executor.submit(perform_ocr_on_pdf, pdf_url, i) for i in range(num_runs)
        ]
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
    return results


def parse_text_from_ocr(file_url):
    try:
        human_messages = []
        if file_url.lower().endswith(".pdf"):
            ocr_results = perform_ocr_on_pdf(file_url, 0)
            logger.info(f"parse_text_from_ocr ocr_results: {ocr_results}")
            human_messages = [
                HumanMessage(content=result["text"]) for result in ocr_results
            ]
        else:
            ocr_results = perform_ocr_on_image(file_url)
            logger.info(f"parse_text_from_ocr ocr_results: {ocr_results}")
            human_messages = [HumanMessage(content=ocr_results)]
        model = ChatOpenAI(model="gpt-4")
        messages = [
            SystemMessage(
                content="You will get a list of strings as an input where each element in the list represents text extracted from a pdf invoice. Your task is to extract line items from the text list in json format. Each object inside the JSON array should include key called item which is the name of the item, expiry_date which is the expiry date in ISO format if exists, lot_no which is the log number of the item if exists, and quantity which is the number of items for that line item."
            ),
            SystemMessage(
                content="This strings you will get as input are extracted from a PDF file using OCR so there might be some mistakes in recognizing characters or spelling mistakes, correct those mistakes if you find them."
            ),
            SystemMessage(
                content="Your output should strictly be a valid JSON object and nothing else"
            ),
            # *[HumanMessage(content=result["text"]) for result in ocr_results],
            *human_messages,
        ]
        logger.info(f"parse_text_from_ocr messages {human_messages}")
        model_response = model.invoke(messages)
        logger.info(f"parse_text_from_ocr model_response: {model_response}")
        parser = JsonOutputParser()
        parser_response = parser.invoke(model_response)
        logger.info(f"parse_text_from_ocr parser_response: {parser_response}")
        # print(res)
        # print()
        return parser_response
    except Exception as e:
        logging.error("")
        logging.error("")
        logging.error(f"++++ Error parse_text_from_ocr: {e}")
        logging.error("")
        logging.error("")
        return []


app = Flask(__name__)


def perform_ocr_on_image(image_url):
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    # if image.mode != "RGB":
    #     image = image.convert("RGB")
    config = r"--oem 3 --psm 6 -l eng"
    text = pytesseract.image_to_string(image, config=config)
    return text


def extract_batch_number_from_image(image_url):
    text = perform_ocr_on_image(image_url)
    model = ChatOpenAI(model="gpt-4")
    messages = [
        SystemMessage(
            content="Your input will be a string that is extracted from an image of a medication vial that has a batch number on it. Your task is to extract the batch number from the string and return it in a JSON object with a key called batch_number. If you can't find the batch number, return an empty string."
        ),
        SystemMessage(
            content="Your output should strictly be a valid JSON object and nothing else"
        ),
        HumanMessage(content=text),
    ]
    response = model.invoke(messages)
    parser = JsonOutputParser()
    res = parser.invoke(response)
    return res


@app.route("/extract-batch-number-from-image")
def extract_batch_number_from_image_route():
    image_url = request.args.get("image_url", default=None, type=str)
    if image_url is None:
        return jsonify({"error": "image_url is required"}), 400
    results = extract_batch_number_from_image(image_url)
    return jsonify({"results": results}), 200


@app.route("/extract-text-from-image")
def extract_text_from_image_route():
    image_url = request.args.get("image_url", default=None, type=str)
    if image_url is None:
        return jsonify({"error": "image_url is required"}), 400
    results = perform_ocr_on_image(image_url)
    return jsonify({"results": results}), 200


@app.route("/extract-text-from-pdf")
def extract_text_from_pdf_route():
    pdf_url = request.args.get("pdf_url", default=None, type=str)
    if pdf_url is None:
        return jsonify({"error": "pdf_url is required"}), 400
    results = perform_ocr_on_pdf(pdf_url, 0)
    return jsonify({"results": results}), 200


@app.route("/extract-line-items-from-fusion-invoice")
def extract_line_items_from_fusion_invoice_route():
    pdf_url = request.args.get("pdf_url", default=None, type=str)
    if pdf_url is None:
        return jsonify({"error": "pdf_url is required"}), 400
    results = parse_text_from_ocr(pdf_url)
    return jsonify({"results": results}), 200


@app.route("/status")
def status_route():
    return jsonify({"status": "ok", "count": 1}), 200


if __name__ == "__main__":
    app.run(debug=False, port=8000)


# https://dardocstorageaccount.blob.core.windows.net/dardocpictures/MaryanAlameriprescription.pdf
# parse_text_from_ocr(
#     "https://dardocstorageaccount.blob.core.windows.net/dardocpictures/F2226069%20Del_0001.pdf"
# )
