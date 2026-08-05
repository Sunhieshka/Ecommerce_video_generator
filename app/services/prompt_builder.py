from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re

from app.schemas import ProductRow, VideoConfig


COPYRIGHT_SAFE = (
    "Ensure all music, sound effects, visuals, characters, logos, brands, and video elements are "
    "fully original, generic, copyright-safe, and free from any identifiable copyrighted or legally "
    "protected references."
)

BRAND_EXCEPTION = (
    "The one exception: the product shown in the reference image, including its own branding and "
    "markings, is the advertiser's own property. Reproduce it exactly and never genericize it."
)

# ecommerceskills.md Step 4 rule 12 — constrain rotation/orbit to what the references cover,
# so the model doesn't invent unseen sides of the product.
UNSEEN_SIDES_CLAUSE = (
    "Sides, angles, or components not visible in the reference images must remain plain and "
    "consistent with the visible design language — do not add new details, seams, logos, or components."
)

# ecommerceskills.md Step 4 rule 13 — no opening/disassembly without an open-state reference,
# since the model will otherwise invent interiors and mutate the closed-state geometry.
NO_DISASSEMBLY_CLAUSE = (
    "Do not script opening, unscrewing, unzipping, disassembling, or removing any part of the "
    "product unless a reference image shows that open state. Substitute a hand lifting, tilting, "
    "or rotating the closed product instead."
)


def _format_component_lock(components: list[str] | None) -> str:
    """ecommerceskills.md Step 4 rule 2 — verbal component lock.

    Emits a block that names each component from the pre-extracted inventory and
    ties it to the reference images. Returns empty string if no components were
    extracted (e.g. LLM unavailable or extraction failed).
    """
    if not components:
        return ""
    lines = [
        "Component lock — every component listed below must remain identical to the reference images "
        "in every frame and every camera distance, including all close-ups. Zero design deviation, "
        "no redesign, no color shift, no morphing between shots, no flickering:",
    ]
    for component in components:
        lines.append(f"  - {component}")
    return "\n".join(lines)


def _format_style_block(*, aesthetic: str, palette: str, lighting: str, allow_jump_cuts: bool = False) -> str:
    """ecommerceskills.md Step 4 rule 8 — style block goes last: aesthetic + palette + camera + lighting."""
    cuts_rule = "Fast jump cuts permitted for UGC pacing." if allow_jump_cuts else "Smooth camera movements, no jump cuts."
    return (
        f"Style: {aesthetic}. Palette: {palette}. {cuts_rule} Lighting: {lighting}."
    )

STYLE_GUIDANCE = {
    "editorial": "Premium visuals with polished styling, clean framing, and premium motion.",
    "lifestyle": "Warm lifestyle storytelling with authentic movement and natural environmental context.",
    "studio": "Clean studio showcase with controlled lighting, product-led framing, and minimal background noise.",
    "ugc": "Native social-video pacing with approachable energy, human gesture, and product-first clarity.",
    "cinematic": "Smooth camera movement, balanced lighting, layered camera movement, and tactile product detail.",
}


STYLE_GUIDE_PATH = Path(__file__).resolve().parents[2] / "Doc" / "ecommerceskills.md"


@lru_cache(maxsize=1)
def _load_style_guide_text() -> str:
    if not STYLE_GUIDE_PATH.exists():
        raise RuntimeError(
            f"Mandatory style guide file is missing: {STYLE_GUIDE_PATH}. "
            "Restore ecommerceskills.md before generating prompts."
        )
    return STYLE_GUIDE_PATH.read_text(encoding="utf-8")


def _format_reference_labels(prefix: str, refs: list[str]) -> str:
    """Emit @image1, @image2, … tokens per ecommerceskills.md rule 1.

    prefix is retained for backwards compatibility but the guide's convention
    is to tag every reference with `@image<N>` regardless of type — the
    surrounding prose already labels what each image shows.
    """
    if not refs:
        return "None provided"
    token = "@image" if prefix.lower().startswith("image") else "@model_image"
    return ", ".join(f"{token}{index}" for index, _ in enumerate(refs, start=1))


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


def build_prompt(
    product: ProductRow,
    config: VideoConfig,
    ugc_dialogue: list[str] | None = None,
    components: list[str] | None = None,
    review_dialogue: list[str] | None = None,
    presenter_script: str | None = None,
) -> str:
    style_guide = _load_style_guide_text()
    effective_style = (product.video_style or config.style).strip()
    effective_duration = product.duration_seconds or config.duration_seconds
    style_key = effective_style.lower()
    product_refs = _format_reference_labels("Image", product.product_image_refs)
    model_refs = _format_reference_labels("Model image", product.human_model_image_refs)
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
            ugc_dialogue=ugc_dialogue or [],
        )

    if style_key == "cinematic":
        return _build_cinematic_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
        )

    if style_key == "cgi showcase":
        return _build_cgi_showcase_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
        )

    if style_key == "review":
        return _build_review_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            model_refs=model_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
            review_dialogue=review_dialogue,
        )

    if style_key == "hook":
        return _build_hook_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
        )

    if style_key == "lifestyle scenes":
        return _build_lifestyle_scenes_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
        )

    if style_key == "presenter":
        return _build_presenter_prompt(
            product_name=product_name,
            product_description=product.product_description,
            product_refs=product_refs,
            model_refs=model_refs,
            effective_duration=effective_duration,
            aspect_ratio=config.aspect_ratio,
            sound_required=config.sound_required,
            components=components,
            presenter_script=presenter_script,
        )

    # Generic fallback for: Product Showcase, Virtual try-on, lifestyle, editorial, studio, etc.
    tone = config.tone_override.strip() if config.tone_override else "confident, clean, ecommerce-ready"
    style_direction = STYLE_GUIDANCE.get(style_key, effective_style)
    audio_direction = (
        "an original, fully copyright-safe instrumental music bed that matches the creative direction, "
        "plus subtle ambience and product sound design. Build gently and resolve on the final frame. "
        "Ensure all music, visuals, characters, logos, brands, and video elements are fully original, "
        "generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."
        if config.sound_required else "Do not generate background music."
    )
    lines = [
        "Create a product video based only on the supplied product details and reference images.",
        "Do not leave any placeholders or bracketed variables unresolved.",
        "",
        f"Product name: {product_name}",
        f"Product description: {product.product_description}",
        f"Product reference images: {product_refs}",
        "Reproduce the product exactly as shown in the reference: same shape, proportions, "
        "materials, colors, finish, and label artwork.",
        f"Human model references: {model_refs}",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        f"Creative direction: {style_direction}",
        f"Video tone: {tone}",
        f"Video duration: {effective_duration} seconds",
        f"Output resolution: {config.resolution}",
        f"Aspect ratio: {config.aspect_ratio}",
        "",
        "Generation goals:",
        "1. The product is fully in frame and clearly recognizable within the first second.",
        "2. Keep the product visually consistent with the reference imagery throughout.",
        "3. Use the human model references for pose, styling, and presentation cues.",
        "4. Include motion beats suited to a paid-social or marketplace product video.",
        f"5. Compose for a {config.aspect_ratio} frame, leaving clean negative space along the "
        "bottom third for text overlay.",
        "",
        "Shot structure:",
        "1. Hook shot that presents the product immediately.",
        "2. Mid-sequence showing fit, use, or product handling with the model.",
        "3. Closing shot with strongest product framing for conversion.",
        "",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "Do not add overlay graphics, captions, subtitles, watermarks, or on-screen text of any kind.",
        f"Audio: {audio_direction}",
        _format_style_block(
            aesthetic=effective_style,
            palette="product colors on a clean, uncluttered background",
            lighting="soft, natural, motivated by the environment; even exposure on the product",
        ),
        COPYRIGHT_SAFE,
        BRAND_EXCEPTION,
    ])
    return "\n".join(lines)


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
    ugc_dialogue: list[str],
) -> str:
    if ugc_dialogue and len(ugc_dialogue) >= 2:
        dialogue_line_1 = ugc_dialogue[0]
        dialogue_line_2 = ugc_dialogue[1]
        dialogue_line_3 = ugc_dialogue[2] if len(ugc_dialogue) >= 3 else None
    else:
        print(f"[prompt] UGC dialogue fallback for {product_name} (LLM dialogue unavailable or too few lines)", flush=True)
        dialogue_line_1, dialogue_line_2, dialogue_line_3 = _build_ugc_dialogue_lines(product_name, product_description)

    return "\n".join(
        [
            "Create a UGC-style product video based only on the supplied product details and reference images.",
            "Do not leave placeholders unresolved.",
            "",
            f"Product name: {product_name}",
            f"Product description: {product_description}",
            f"Product reference images: {product_refs}",
            "Reproduce the product exactly as shown in the reference: same shape, proportions, "
            "materials, colors, finish, and label artwork.",
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
            *(
                [f'On-camera dialogue (casual close): "{dialogue_line_3}"']
                if dialogue_line_3 else []
            ),
            "",
            "Shot structure:",
            "1. Hook selfie shot — the product is fully in frame and clearly recognizable within the first second.",
            "2. Mid-sequence jump cuts showing real use context and one clear product benefit per beat.",
            "3. Closing selfie/product framing with direct spoken recommendation and clear product visibility.",
            "",
            f"Compose for a {aspect_ratio} frame, leaving clean negative space along the bottom third for text overlay.",
            "Do not add overlay graphics, captions, subtitles, watermarks, or on-screen text of any kind.",
            COPYRIGHT_SAFE,
            BRAND_EXCEPTION,
        ]
    )


def _build_cinematic_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
) -> str:
    audio_direction = (
        "an original, fully copyright-safe instrumental music bed that matches the brand style, "
        "plus subtle ambience and product sound design. Build gently and resolve on the final frame. "
        "Ensure all music, visuals, characters, logos, brands, and video elements are fully original, "
        "generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."
    )
    lines = [
        f"Refined product hero shot of the {product_name} from the reference image.",
        f"Product: {product_description}",
        "Reproduce the product exactly as shown in the reference: same shape, proportions, "
        "materials, colors, finish, and label artwork.",
        f"Product reference images: {product_refs}",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        "Camera: slow smooth push-in with shallow depth of field. One continuous take, smooth and steady, no cuts.",
        "Setting: clean seamless studio backdrop with soft directional key light.",
        "Lighting: soft key with gentle falloff and controlled specular highlights along the product edges. "
        "No blown highlights, no harsh shadows across the label.",
        f"The product is fully in frame and clearly recognizable within the first second and "
        f"remains the visual focus for the entire {effective_duration} seconds.",
        f"Compose for a {aspect_ratio} frame, leaving clean negative space along the bottom third for text overlay.",
        "Do not add, remove, or restyle any product feature. Do not morph or deform the product.",
        "Keep the product's own branding, logos, and markings exactly as they appear in the "
        "reference, correctly spelled and undistorted.",
        "Do not add overlay graphics, captions, subtitles, watermarks, or any branding that is "
        "not already on the product. No hands or people in frame.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "End on a steady, well-composed final frame suitable for a landing-page loop.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="refined product hero, premium and understated",
        palette="product colors on a clean seamless studio backdrop",
        lighting="soft directional key with gentle falloff, controlled specular highlights along product edges",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)


def _build_cgi_showcase_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
) -> str:
    audio_direction = (
        "an original, fully copyright-safe electronic or orchestral music bed with crisp sound design "
        "marking each VFX beat. Build energy through the reveal and resolve cleanly on the final hero frame. "
        "Ensure all music, visuals, characters, logos, brands, and video elements are fully original, "
        "generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."
    )
    lines = [
        f"Photoreal CGI product showcase of the {product_name} from the reference image, rendered "
        "like a high-end VFX commercial.",
        f"Product: {product_description}",
        "Treat the product as a hyper-real CG hero asset: raytraced reflections, accurate "
        "refraction, physically based materials, and micro-surface detail visible at macro range.",
        "Reproduce the product exactly as shown in the reference: same shape, proportions, "
        "materials, colors, finish, and label artwork.",
        f"Product reference images: {product_refs}",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        "Camera: a weightless motion-control move that arcs around the product and pushes into "
        "macro detail, then pulls back to a locked hero angle. One continuous, perfectly smooth "
        "take with no cuts and no handheld shake.",
        "Setting: an abstract CG void — an infinite seamless gradient stage with a subtly "
        "reflective floor and no real-world props.",
        "Effects: fine weightless particulate and dust motes drifting through light beams, with "
        "soft volumetric rays raking across the stage. Effects orbit and reveal the product; "
        "they never obscure, cover, or overlap it.",
        "The impossible physics belong to the camera, the environment, and the effects — never "
        "to the product itself, which stays physically intact, rigid, and photoreal throughout.",
        f"The product is fully in frame and clearly recognizable within the first second and "
        f"remains the visual focus for the entire {effective_duration} seconds.",
        f"Compose for a {aspect_ratio} frame, leaving clean negative space along the bottom third for text overlay.",
        "Do not add, remove, or restyle any product feature. Do not morph, melt, shatter, or deform the product.",
        "Keep the product's own branding, logos, and markings exactly as they appear in the "
        "reference, correctly spelled and undistorted.",
        "Do not add overlay graphics, captions, subtitles, watermarks, or any branding that is "
        "not already on the product. No hands or people in frame.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "Render quality: sharp focus on the product, clean anti-aliased edges, no CG artifacts, "
        "no flicker, no waxy or plastic-looking surfaces.",
        "End on a locked, well-composed hero frame — the final beauty render.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="high-end VFX commercial, photoreal CG hero asset",
        palette="product colors on an abstract CG void with subtly reflective floor",
        lighting="soft volumetric rays with controlled specular highlights and clean anti-aliased edges",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)


REVIEW_LINE_TONES = [
    ("Voiceover (time-anchored opener, natural tone)", "lifts the product into frame and glances briefly down at it before speaking"),
    ("On-camera dialogue (honest positive, impressed tone)", "tilts the product toward the light and gives a small nod"),
    ("On-camera dialogue (small caveat, matter-of-fact tone)", "turns the product slightly in hand, small shrug"),
    ("On-camera dialogue (personal recommendation, warm sign-off)", "settles the product back to chest height and holds eye contact with the lens"),
]


def _build_review_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    model_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
    review_dialogue: list[str] | None = None,
) -> str:
    voice_style = "warm, conversational, and genuinely enthusiastic without sounding scripted"
    audio_direction = (
        f"the presenter's own voice speaking the review live on camera, lip-synced to their mouth "
        f"movements, {voice_style}, over quiet natural room tone. Exactly one voice in the mix: "
        "no separate narrator or voiceover layered over the on-camera speech. "
        "Do not generate background music."
    )
    lines = [
        f"Single-take user-generated review video: one real person on camera, talking straight to "
        f"the viewer about the {product_name}. It should feel like an authentic creator post filmed "
        "on a phone, not a polished studio commercial.",
        f"Product: {product_description}",
        f"Product reference images: {product_refs}",
        f"Human model references: {model_refs}",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        f"Presenter: the person shown in the human model reference, casually dressed, filming "
        "themselves at home. Their face, hands, and upper body are visible throughout, and they "
        f"physically hold and handle the {product_name} as they talk about it.",
        f"Reproduce the {product_name} exactly as shown in the reference image: same shape, "
        "proportions, materials, colors, finish, and label artwork. It is a real physical object "
        "in the presenter's hands, held steady and readable whenever it is in frame.",
        "Camera: handheld front-facing phone camera held at arm's length, chest-up framing with "
        "small natural sway, one continuous take, no cuts.",
        "Setting: a lived-in home interior with soft daylight from a nearby window and everyday "
        "clutter falling softly out of focus behind the presenter.",
        f"Delivery: {voice_style}. The presenter speaks the lines below back-to-back with natural "
        "pauses between them, small gestures tied to each line, and eye contact with the lens; "
        "their lip movements match the words they say exactly.",
        f"Both the presenter and the {product_name} are clearly visible within the first second "
        f"and hold the frame for the entire {effective_duration} seconds.",
    ])

    # Verbatim tone-annotated script block. If review_dialogue is empty (LLM
    # unavailable or extraction failed), fall back to a generic on-camera
    # continuous-speech instruction so the prompt still submits.
    if review_dialogue:
        lines.extend(["", "Spoken script (delivered on camera by the presenter in this exact order, verbatim, back-to-back):"])
        for idx, line in enumerate(review_dialogue):
            tone_label, action = REVIEW_LINE_TONES[idx] if idx < len(REVIEW_LINE_TONES) else REVIEW_LINE_TONES[-1]
            lines.append(f'{tone_label}: "{line}"')
            lines.append(f"(action while speaking: {action})")
        lines.append(
            "The presenter says nothing else. Lip movements must match these words exactly, "
            "frame by frame — do not paraphrase, reorder, truncate, or ad-lib."
        )
    else:
        print(f"[prompt] Review dialogue fallback for {product_name} (LLM dialogue unavailable or too few lines)", flush=True)
        lines.append(
            "The presenter speaks a short honest first-person review (opener → honest positive "
            "→ personal recommendation), quoted verbatim would be lip-synced exactly."
        )

    lines.extend([
        f"Compose for a {aspect_ratio} frame, keeping the presenter's face off dead center and "
        "leaving clean space near the bottom for text overlay.",
        "Do not add, remove, or restyle any product feature. Do not morph or deform the product, "
        "and do not swap it for a different item mid-shot.",
        "Keep the product's own branding, logos, and markings exactly as they appear in the "
        "reference, correctly spelled and undistorted.",
        "Do not add overlay graphics, captions, subtitles, watermarks, or on-screen text of any kind.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "End with the presenter holding the product still and facing the lens, on a clean final frame.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="single-take handheld creator review, phone-camera authenticity",
        palette="natural home-interior tones + product colors held steady",
        lighting="soft daylight from a nearby window, even exposure on the face and product",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)


def _build_hook_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
) -> str:
    audio_direction = (
        "an original, fully copyright-safe music bed that hits on the opening frame and drives the energy, "
        "plus natural ambience and product sound design. Keep it punchy — no slow build. "
        "Ensure all music, visuals, characters, logos, brands, and video elements are fully original, "
        "generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."
    )
    lines = [
        f"Scroll-stopping opening hook: the first {effective_duration} seconds of a short-form "
        f"social ad for the {product_name}.",
        f"Product: {product_description}",
        f"Product reference images: {product_refs}",
        "Reproduce the product exactly as shown in the reference: same shape, proportions, "
        "materials, colors, finish, and label artwork.",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        "This clip is the hook alone — the first beat of an ad, not the whole ad. No CTA, no "
        "price card, no sign-off.",
        "Shoot ONE of these opening angles — choose the strongest fit for this product:",
        "1. Problem in motion — open on the exact frustration the audience lives with, shown "
        "happening in one unbroken beat, never narrated.",
        "2. Pattern interrupt — open mid-action on an unexpected, arresting image that stops the "
        "scroll a beat before the viewer understands what is being sold.",
        "3. Result first — open on the finished, obviously desirable outcome and let the viewer "
        "work backwards to the product.",
        "4. Tactile demo — open on a tight macro of the product doing the one thing it does best, "
        "close enough to see the material and the mechanism.",
        "",
        "The hook must read in the first 1.5 seconds — open on the strongest frame with no logo "
        "sting, no slow build, no establishing shot.",
        f"The {product_name} is on screen and recognizable by the two-second mark.",
        f"Compose for a {aspect_ratio} frame with the subject centred and clear of caption zones "
        "along the bottom third.",
        "Do not add overlay graphics, captions, subtitles, watermarks, or on-screen text of any kind.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "End on a frame that reads as unfinished — the hook hands off to the next beat rather than resolving.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="scroll-stopping opening beat, first frame carries the message",
        palette="product colors held bold and centred against a clean or high-contrast environment",
        lighting="punchy, high-contrast, motivated by the chosen opening angle",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)


def _build_lifestyle_scenes_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
) -> str:
    audio_direction = (
        "an original, fully copyright-safe instrumental music bed with consistent tempo and instrumentation "
        "across all scenes, plus ambience that suits each setting. Keep the musical identity the same so "
        "scenes cut together as one campaign. "
        "Ensure all music, visuals, characters, logos, brands, and video elements are fully original, "
        "generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."
    )
    lines = [
        f"Lifestyle product video showing the {product_name} across multiple real-world scenes.",
        f"Product: {product_description}",
        f"Product reference images: {product_refs}",
        "Every scene shows the exact same physical product — the same single unit, not a similar one. "
        "Treat the reference image as ground truth: match clean shapes, proportions, materials, "
        "finish, surface texture, color, and label artwork precisely.",
        "The setting is the only thing that changes between scenes. The product does not change "
        "with it — never restyled, recolored, resized, or swapped for a variant.",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        "Camera: steady handheld move — a slow orbit or push-in that keeps the product centred "
        "and readable. One continuous take, smooth and steady, no cuts.",
        "Lighting: soft key with gentle falloff and controlled specular highlights along the "
        "product edges. Let the scene motivate the light direction but keep the product's own "
        "colors reading the same as in the reference — no color cast on the body or label.",
        "Show the product across three environments suited to its real-world use — indoors, "
        "outdoors, and on-the-go. Dress each scene naturally; keep the product untouched.",
        f"The {product_name} is fully in frame and clearly recognizable within the first second "
        f"and remains the visual focus for the entire {effective_duration} seconds.",
        f"Compose for a {aspect_ratio} frame, leaving clean negative space along the bottom third for text overlay.",
        "Do not add, remove, or restyle any product feature. Do not morph or deform the product.",
        "Keep the product's own branding, logos, and markings exactly as they appear in the "
        "reference, correctly spelled and undistorted.",
        "Do not add overlay graphics, captions, subtitles, watermarks, or on-screen text of any kind.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "End on a steady, well-composed final frame with the product held still and centred.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="warm lifestyle storytelling with authentic movement",
        palette="product colors held identical across scenes, each setting supplying its own environment tones",
        lighting="motivated by each scene, gentle falloff, no color cast on the product body or label",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)


def _build_presenter_prompt(
    *,
    product_name: str,
    product_description: str,
    product_refs: str,
    model_refs: str,
    effective_duration: int,
    aspect_ratio: str,
    sound_required: bool,
    components: list[str] | None = None,
    presenter_script: str | None = None,
) -> str:
    # Prefer the LLM-authored script; fall back to a fragment-based script only
    # when the LLM is unavailable or returned empty.
    if presenter_script:
        script = presenter_script
    else:
        print(f"[prompt] Presenter script fallback for {product_name} (LLM script unavailable or empty)", flush=True)
        fragments = _extract_description_fragments(product_description)
        benefit_1 = fragments[0] if fragments else "it is a great everyday product"
        benefit_2 = fragments[1] if len(fragments) > 1 else "the quality is immediately obvious"
        # Deliberately avoid injecting the raw product_name at the start —
        # for products whose "name" is derived from a spec-sheet header
        # (e.g. "Style: Full Sleeve"), reading it aloud sounds absurd.
        script = (
            f"If you want one that actually delivers, this is it. "
            f"What I love about it is that {benefit_1}. "
            f"And {benefit_2}. Honestly, I'd recommend picking one up."
        )
    audio_direction = (
        "the presenter's own speaking voice delivering the script verbatim, recorded clean and "
        "close, with no background chatter competing with the dialogue. "
        "Do not generate background music."
    )
    lines = [
        f"Talking-head presenter video for the {product_name}.",
        f"Product: {product_description}",
        f"Product reference images: {product_refs}",
        f"Human model references: {model_refs}",
    ]
    component_lock = _format_component_lock(components)
    if component_lock:
        lines.extend(["", component_lock])
    lines.extend([
        "",
        f"The person from the human model reference is on screen for the entire {effective_duration} "
        "seconds, facing camera and speaking directly to the lens.",
        "Reproduce the presenter exactly as shown in the reference: same face, bone structure, "
        "skin tone, hair, and wardrobe. Do not restyle, de-age, or substitute the person.",
        "The presenter speaks the following script word for word, and says nothing else:",
        f'"{script}"',
        "Lip-sync fidelity to that exact script is the single most important requirement. Mouth "
        "shapes, jaw, and tongue must track the spoken words frame by frame. Do not paraphrase, "
        "reorder, truncate, or ad-lib any part of the script.",
        "Delivery: warm, confident, and conversational, at an unhurried natural presenter pace.",
        "Performance: natural micro-expressions, relaxed blinking, small head movements, and "
        "unforced hand gestures that punctuate sentences. Hold eye contact with the lens.",
        "Camera: locked-off eye-level medium close-up, chest-up framing, with a very slow "
        "almost imperceptible push-in. One continuous take, no cuts.",
        "Setting: clean, uncluttered modern interior a few feet behind the presenter, softly "
        "out of focus.",
        "Lighting: soft key from the front with gentle fill, a clean catchlight in the eyes, "
        "and even exposure on the face. No blown highlights, no harsh shadow across the mouth.",
        f"Compose for a {aspect_ratio} frame, keeping the face in the upper third and leaving "
        "clean space for a lower-third caption added later.",
        "Do not add overlay graphics, burned-in captions, subtitles, watermarks, or on-screen text.",
        UNSEEN_SIDES_CLAUSE,
        NO_DISASSEMBLY_CLAUSE,
        "End on a steady, composed final frame with the presenter still and settled, mouth closed.",
    ])
    if sound_required:
        lines.append(f"Audio: {audio_direction}")
    else:
        lines.append("Audio: Do not generate background music.")
    lines.append(_format_style_block(
        aesthetic="talking-head presenter, chest-up framing with locked-off eye-level camera",
        palette="clean uncluttered interior tones + presenter wardrobe + product colors",
        lighting="soft frontal key with gentle fill, clean catchlight in the eyes, even exposure on the face",
    ))
    lines.append(COPYRIGHT_SAFE)
    lines.append(BRAND_EXCEPTION)
    return "\n".join(lines)
