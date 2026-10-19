import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel


MODEL_NAME = "bert-base-uncased"

_tokenizer = None
_bert = None


def load_bert():

    global _tokenizer
    global _bert

    if _tokenizer is None:

        print("Loading BERT tokenizer...")

        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

    if _bert is None:

        print("Loading BERT model...")

        _bert = AutoModel.from_pretrained(
            MODEL_NAME
        )

        _bert.eval()

    return _tokenizer, _bert


def extract_text_features(text: str):

    tokenizer, model = load_bert()

    if not text or not text.strip():
        text = "No speech detected."

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():

        outputs = model(**inputs)

    # CLS embedding = 768 dimensions
    features = outputs.last_hidden_state[
        :, 0, :
    ]

    features = features.cpu().numpy()[0]

    features = np.asarray(
        features,
        dtype=np.float32
    )

    print(
        f"BERT feature dimension: "
        f"{len(features)}"
    )

    return features