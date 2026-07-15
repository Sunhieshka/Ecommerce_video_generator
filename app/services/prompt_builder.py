from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from app.schemas import ProductRow, VideoConfig


STYLE_GUIDANCE = {
    "editorial": "Luxury editorial campaign with polished styling, sharp framing, and premium motion.",
    "lifestyle": "Warm lifestyle storytelling with authentic movement and natural environmental context.",
    "studio": "Clean studio showcase with controlled lighting, product-led framing, and minimal background noise.",
    "ugc": "Native social-video pacing with approachable energy, human gesture, and product-first clarity.",
    "cinematic": "Cinematic motion, dramatic lighting, layered camera movement, and tactile product detail.",
}


STYLE_GUIDE_PATH = Path(__file__).resolve().parents[2] / "ecommerceskills.md"


@lru_cache(maxsize=1)
def _load_style_guide_text() -> str:
    if not STYLE_GUIDE_PATH.exists():
        raise RuntimeError(
            f"Mandatory style guide file is missing: {STYLE_GUIDE_PATH}. "
            "Restore ecommerceskills.md before generating prompts."
        )
    return STYLE_GUIDE_PATH.read_text(encoding="utf-8")


def _format_reference_labels(prefix: str, refs: list[str]) -> str:
    if not refs:
        return "None provided"
    return ", ".join(f"{prefix} {index}" for index, _ in enumerate(refs, start=1))


def _extract_description_fragments(description: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", description).strip()
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    fragments: list[str] = []
    for sentence in sentences:
        normalized = sentence.strip(" .,!?:;")
        if not normalized:
            continue
        normalized = normalized[0].lower() + normalized[1:] if len(normalized) > 1 else normalized.lower()
        fragments.append(normalized)
        if len(fragments) == 3:
            break

    if not fragments:
        comma_parts = [part.strip(" .,!?:;") for part in cleaned.split(",") if part.strip(" .,!?:;")]
        fragments.extend(part[0].lower() + part[1:] if len(part) > 1 else part.lower() for part in comma_parts[:3])
    return fragments


def _build_ugc_dialogue_lines(product_name: str, product_description: str) -> tuple[str, str, str]:
    fragments = _extract_description_fragments(product_description)
    feature_1 = fragments[0] if fragments else f"this {product_name.lower()} feels genuinely useful day to day"
    feature_2 = fragments[1] if len(fragments) > 1 else "it looks good on camera and is easy to use in real life"
    feature_3 = fragments[2] if len(fragments) > 2 else f"this {product_name.lower()} is one of those picks you keep reaching for"

    line_1 = f"I tried this {product_name}, and I immediately noticed that {feature_1}."
    line_2 = f"What sold me is that {feature_2}."
    line_3 = f"Honestly, {feature_3}, so I would absolutely recommend it."
    return line_1, line_2, line_3


def build_prompt(product: ProductRow, config: VideoConfig) -> str:
    style_guide = _load_style_guide_text()
    effective_style = (product.video_style or config.style).strip()
    effective_duration = product.duration_seconds or config.duration_seconds
    style_key = effective_style.lower()
    style_direction = STYLE_GUIDANCE.get(style_key, effective_style)
    product_refs = _format_reference_labels("Image", product.product_image_refs)
    model_refs = _format_reference_labels("Model image", product.human_model_image_refs)
    tone = config.tone_override.strip() if config.tone_override else "confident, clean, ecommerce-ready"
    product_name = product.product_name if not product.product_name.upper().startswith("ROW-") else "Product"
    if style_key == "ugc":
        return _build_ugc_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            model_refs=model_refs,
            effective_duration=effective_duration,
            resolution=config.resolution,
            aspect_ratio=config.aspect_ratio,
            style_guide_excerpt=(
                "UGC rules enforced from ecommerceskills.md: "
                "avoid polished commercial visuals; mandatory spoken audio with quoted tone annotation; "
                "never silent or music-only."
            )
            if "UGC anti-polish clause" in style_guide and "UGC voiceover is mandatory" in style_guide
            else "UGC rules enforced from mandatory style guide file.",
        )

    return "\n".join(
        [
            "Create a product video based only on the supplied product details and reference images.",
            "Do not leave any placeholders or bracketed variables unresolved.",
            "",
            f"Product name: {product_name}",
            f"Product description: {product.product_description}",
            f"Product reference images: {product_refs}",
            f"Human model references: {model_refs}",
            "",
            f"Creative direction: {style_direction}",
            f"Video tone: {tone}",
            f"Video duration: {effective_duration} seconds",
            f"Output resolution: {config.resolution}",
            f"Aspect ratio: {config.aspect_ratio}",
            f"Sound required in output: {'yes' if config.sound_required else 'no'}",
            "",
            "Generation goals:",
            "1. Keep the product visually consistent with the reference imagery.",
            "2. Use the human model references for pose, styling, and presentation cues.",
            "3. Show the product clearly in the opening two seconds and maintain ecommerce clarity throughout.",
            "4. Include motion beats suited to a paid-social or marketplace product video.",
            "5. Ensure the final prompt is ready to send directly to a video generation model.",
            "6. Ensure music is fully original, generic, copyright-safe, and free from any identifiable copyrighted or legally protected references.",
            "",
            "Shot structure:",
            "1. Hook shot that presents the product immediately.",
            "2. Mid-sequence showing fit, use, or product handling with the model.",
            "3. Closing shot with strongest product framing for conversion.",
        ]
    )


def _build_ugc_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    model_refs: str,
    effective_duration: int,
    resolution: str,
    aspect_ratio: str,
    style_guide_excerpt: str,
) -> str:
    dialogue_line_1, dialogue_line_2, dialogue_line_3 = _build_ugc_dialogue_lines(product_name, product_description)

    return "\n".join(
        [
            "Create a UGC-style product video based only on the supplied product details and reference images.",
            "Do not leave placeholders unresolved.",
            "",
            f"Product name: {product_name}",
            f"Product description: {product_description}",
            f"Product reference images: {product_refs}",
            f"Human model references: {model_refs}",
            "",
            f"Video duration: {effective_duration} seconds",
            f"Output resolution: {resolution}",
            f"Aspect ratio: {aspect_ratio}",
            "",
            "UGC mandatory style rules:",
            style_guide_excerpt,
            "Use natural handheld/selfie aesthetics with authentic creator energy.",
            "Avoid polished commercial or studio-style visuals.",
            "",
            "Spoken audio is mandatory (never silent, never music-only):",
            f'Voiceover (natural, conversational tone): "{dialogue_line_1}"',
            f'Voiceover (friendly, confident tone): "{dialogue_line_2}"',
            f'On-camera dialogue (casual close): "{dialogue_line_3}"',
            "",
            "Shot structure:",
            "1. Hook selfie shot showing product immediately with natural hand movement.",
            "2. Mid-sequence jump cuts showing real use context and one clear product benefit per beat.",
            "3. Closing selfie/product framing with direct spoken recommendation and clear product visibility.",
            "",
            "Audio rule: Ensure music is fully original, generic, copyright-safe, and free from any identifiable copyrighted or legally protected references.",
        ]
    )
