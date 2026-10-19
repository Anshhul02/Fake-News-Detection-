"""
============================================================
EVIDENCE ANALYZER
============================================================

Converts SHAP / Grad-CAM evidence into a simple,
human-readable explanation.

Evidence Type:
    VISUAL
    TEXT
    BOTH
    UNKNOWN

This module does not use the classification threshold
to explain the evidence.

It only describes which modality contributed most
strongly to the model's decision.
============================================================
"""

from typing import Dict, Any


# ============================================================
# HELPERS
# ============================================================

def _safe_float(value, default=0.0):

    try:
        return float(value)

    except Exception:
        return float(default)


# ============================================================
# GENERATE HUMAN-READABLE EXPLANATION
# ============================================================

def generate_human_explanation(
    label: str,
    visual_shap: float,
    text_shap: float,
    gradcam_available: bool = False,
    gradcam_frames: int = 0,
) -> Dict[str, Any]:

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    label = str(label).strip().upper()

    visual_shap = abs(
        _safe_float(visual_shap)
    )

    text_shap = abs(
        _safe_float(text_shap)
    )

    # ========================================================
    # TOTAL SHAP CONTRIBUTION
    # ========================================================

    total_shap = (
        visual_shap +
        text_shap
    )

    # ========================================================
    # CONTRIBUTION PERCENTAGES
    # ========================================================

    if total_shap > 0:

        visual_percentage = (
            visual_shap /
            total_shap
        ) * 100.0

        text_percentage = (
            text_shap /
            total_shap
        ) * 100.0

    else:

        visual_percentage = 0.0
        text_percentage = 0.0

    # ========================================================
    # DETERMINE EVIDENCE TYPE
    # ========================================================

    if total_shap <= 0:

        evidence_type = "UNKNOWN"

    elif visual_percentage >= 60:

        evidence_type = "VISUAL"

    elif text_percentage >= 60:

        evidence_type = "TEXT"

    else:

        evidence_type = "BOTH"

    # Keep dominant_modality as an alias for compatibility
    dominant_modality = evidence_type

    # ========================================================
    # HUMAN-READABLE REASON
    # ========================================================

    if label == "FAKE":

        # ----------------------------------------------------
        # VISUAL EVIDENCE
        # ----------------------------------------------------

        if evidence_type == "VISUAL":

            human_reason = (
                "The main concern came from the visual content "
                "of the video. The visual patterns contributed "
                "more strongly to the suspicious classification "
                "than the spoken content."
            )

            if gradcam_available:

                human_reason += (
                    " The visual analysis also identified "
                    "specific areas of the video that influenced "
                    "the model's decision."
                )

        # ----------------------------------------------------
        # TEXT EVIDENCE
        # ----------------------------------------------------

        elif evidence_type == "TEXT":

            human_reason = (
                "The main concern came from the spoken content "
                "of the video. The information extracted from "
                "the speech contributed more strongly to the "
                "suspicious classification than the visual "
                "content."
            )

        # ----------------------------------------------------
        # BOTH
        # ----------------------------------------------------

        elif evidence_type == "BOTH":

            human_reason = (
                "The main concern came from both the visual "
                "content and the spoken information. Both "
                "sources contributed noticeably to the "
                "suspicious classification."
            )

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        else:

            human_reason = (
                "The video showed patterns in its visual and "
                "spoken content that contributed to the "
                "suspicious classification."
            )

    # ========================================================
    # REAL
    # ========================================================

    else:

        # ----------------------------------------------------
        # VISUAL
        # ----------------------------------------------------

        if evidence_type == "VISUAL":

            human_reason = (
                "The visual content provided the strongest "
                "evidence supporting the classification. "
                "The visual patterns were more consistent with "
                "authentic news video content."
            )

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        elif evidence_type == "TEXT":

            human_reason = (
                "The spoken content provided the strongest "
                "evidence supporting the classification. "
                "The extracted information was more consistent "
                "with authentic news video content."
            )

        # ----------------------------------------------------
        # BOTH
        # ----------------------------------------------------

        elif evidence_type == "BOTH":

            human_reason = (
                "Both the visual content and spoken information "
                "supported the classification. Together, they "
                "showed patterns more consistent with authentic "
                "news video content."
            )

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        else:

            human_reason = (
                "The combined visual and spoken information "
                "was more consistent with authentic news "
                "video content."
            )

    # ========================================================
    # MODALITY EXPLANATION
    # ========================================================

    modality_explanation = {

        "visual": (
            "Visual content contributed "
            f"{visual_percentage:.2f}% to the available "
            "explanation evidence."
        ),

        "text": (
            "Spoken content contributed "
            f"{text_percentage:.2f}% to the available "
            "explanation evidence."
        ),

        "dominant": evidence_type
    }

    # ========================================================
    # RESULT
    # ========================================================

    result = {

        # ----------------------------------------------------
        # HUMAN EXPLANATION
        # ----------------------------------------------------

        "human_reason":
            human_reason,

        "human_readable_explanation":
            human_reason,

        # ----------------------------------------------------
        # IMPORTANT:
        # THIS WAS MISSING IN YOUR OLD VERSION
        # ----------------------------------------------------

        "evidence_type":
            evidence_type,

        # Keep this for compatibility
        "dominant_modality":
            dominant_modality,

        # ----------------------------------------------------
        # MODALITY EXPLANATION
        # ----------------------------------------------------

        "modality_explanation":
            modality_explanation,

        # ----------------------------------------------------
        # CONTRIBUTIONS
        # ----------------------------------------------------

        "visual_contribution":
            round(
                visual_percentage,
                2
            ),

        "text_contribution":
            round(
                text_percentage,
                2
            ),

        # ----------------------------------------------------
        # GRAD-CAM
        # ----------------------------------------------------

        "gradcam_support":
            bool(
                gradcam_available
            ),

        "gradcam_frames":
            int(
                gradcam_frames
            ),

        # ----------------------------------------------------
        # EXPLANATION TYPE
        # ----------------------------------------------------

        "explanation_type":
            "SHAP + Grad-CAM evidence",

        # ----------------------------------------------------
        # RESEARCH LIMITATION
        # ----------------------------------------------------

        "explanation_note": (
            "This explanation describes model evidence "
            "that contributed to the classification. "
            "It does not independently prove that the "
            "video has been manipulated or that its claims "
            "are false."
        )
    }

    # ========================================================
    # DEBUG
    # ========================================================

    print()
    print("=" * 60)
    print("EVIDENCE ANALYSIS")
    print("=" * 60)

    print(
        f"Label: {label}"
    )

    print(
        f"Visual contribution: "
        f"{visual_percentage:.2f}%"
    )

    print(
        f"Text contribution: "
        f"{text_percentage:.2f}%"
    )

    print(
        f"Evidence Type: "
        f"{evidence_type}"
    )

    print(
        f"Grad-CAM available: "
        f"{gradcam_available}"
    )

    print("=" * 60)

    return result