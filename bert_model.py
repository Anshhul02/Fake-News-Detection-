import torch
from transformers import AutoTokenizer, AutoModel


# ============================================================
# BERT FEATURE EXTRACTOR
# ============================================================

class BERTFeatureExtractor:

    def __init__(self, model_name="bert-base-uncased"):

        print("Loading BERT model...")

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"Using device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        self.model = AutoModel.from_pretrained(
            model_name
        )

        self.model = self.model.to(
            self.device
        )

        self.model.eval()

        print("BERT loaded successfully.")

    # ========================================================
    # EXTRACT FEATURES
    # ========================================================

    def extract_features(self, text):

        if not text or not text.strip():

            raise ValueError(
                "Transcript is empty."
            )

        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=512
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():

            outputs = self.model(
                **inputs
            )

        # CLS token representation
        cls_embedding = outputs.last_hidden_state[
            :, 0, :
        ]

        # IMPORTANT:
        # Convert (1, 768) -> (768,)
        features = (
            cls_embedding
            .squeeze(0)
            .cpu()
            .numpy()
            .astype("float32")
        )

        print(
            "BERT feature dimension:",
            len(features)
        )

        return features


# ============================================================
# GLOBAL EXTRACTOR
# ============================================================

_bert_extractor = None


def get_bert_extractor():

    global _bert_extractor

    if _bert_extractor is None:

        _bert_extractor = BERTFeatureExtractor()

    return _bert_extractor


# ============================================================
# FUNCTION EXPECTED BY prediction_service.py
# ============================================================

def extract_text_features(text: str):

    extractor = get_bert_extractor()

    return extractor.extract_features(
        text
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    extractor = BERTFeatureExtractor()

    sample_text = """
    Scientists have announced a new discovery
    that could change the way people understand
    climate change.
    """

    features = extractor.extract_features(
        sample_text
    )

    print(
        "BERT feature shape:",
        features.shape
    )