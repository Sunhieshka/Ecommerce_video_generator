from __future__ import annotations

import asyncio
import base64
import json
import mimetypes
import re
import uuid
from pathlib import Path

import httpx

from app.schemas import ProductExecutionStatus, ProductRow, VideoConfig
from app.services.asset_library import AssetLibraryService
from app.services.prompt_builder import build_prompt
from app.settings import Settings


# Banned phrases and their replacements from Seedance-2.0 Audio Guidelines section 1.2.
# Ordered longest-first so multi-word phrases match before their substrings would.
# Replacement of "" means remove the phrase entirely. Matching is case-insensitive on
# whole phrases (word-boundary anchored).
AUDIO_POLICY_REPLACEMENTS: list[tuple[str, str]] = [
    ("35mm editorial film", "refined visual tone"),
    ("premium editorial composition", "clean framing"),
    ("cinematic editorial composition", "clean framing"),
    ("atmospheric texture detail", "detailed fabric texture"),
    ("immersive visual storytelling", "visually balanced"),
    ("premium luxury campaign", "premium visuals"),
    ("trailer-like transitions", "smooth transitions"),
    ("emotional soundtrack wording", ""),
    ("dialogue / narration references", "no spoken content"),
    ("dialogue references", "no spoken content"),
    ("narration references", "no spoken content"),
    ("cinematic atmosphere", "refined visual tone"),
    ("atmospheric mood", "warm and modern"),
    ("emotionally refined", "elegant and balanced"),
    ("cinematic pacing", "smooth camera movement"),
    ("editorial film", "premium visuals"),
    ("filmic contrast", "soft contrast"),
    ("luxury campaign", "premium presentation"),
    ("moody minimalist", "dark minimalist"),
    ("atmospheric depth", "subtle depth"),
    ("cinematic light", "soft directional light"),
    ("refined visual depth", "natural depth"),
    ("Steadicam orbit", "smooth orbit movement"),
    ("softly silhouettes", "warm light across background"),
    ("immersive atmosphere", "calm and visually balanced"),
    ("dramatic lighting", "balanced lighting"),
    ("fade into", "transition to"),
    ("ASMR-like", ""),
    ("ambient drone", ""),
    ("cello textures", ""),
    ("musical peak", ""),
    ("SFX instructions", ""),
    ("silhouette", "clean shapes"),
]


def _sanitize_for_audio_policy(prompt: str) -> str:
    """Replace/remove banned phrases from Seedance-2.0 Audio Guidelines section 1.2.

    Runs right before Seedance submit so LLM-authored prompts (ugc-skill path) are
    also filtered, not just deterministic builders. Logs each replacement to stderr.
    """
    result = prompt
    for phrase, replacement in AUDIO_POLICY_REPLACEMENTS:
        pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
        matches = pattern.findall(result)
        if not matches:
            continue
        result = pattern.sub(replacement, result)
        if replacement == "":
            # Collapse whitespace left behind by removals (double spaces, orphan commas).
            result = re.sub(r"\s{2,}", " ", result)
            result = re.sub(r"\s+([,.;])", r"\1", result)
        print(
            f"[audio-policy] replaced {len(matches)} instance(s) of {phrase!r} -> {replacement!r}",
            flush=True,
        )
    return result


# Per-style pacing profiles — the single source of truth for how each spoken
# style is paced through the whole pipeline.
#
# Both the script generators (which write the dialogue) and the runtime
# articulation directive (which tells Seedance how to deliver it) MUST read
# from this table. Any drift between the two — e.g. a generator budgeting at
# 2.5 wps while the directive tells Seedance to deliver at 3 wps — causes
# Seedance to rush past the last spoken word and improvise gibberish to
# match the pace it was told to hit.
#
# Fields:
#   wps  — words per second the style is written and paced at.
#            UGC/UGC Skill: 3.0 (fast TikTok-style delivery, one breath).
#            Review/Presenter: 2.5 (conversational, natural pauses allowed).
#   vibe — one-line pace vibe injected into the articulation directive so
#            Seedance's delivery instruction matches the pacing math.
_STYLE_PACING: dict[str, dict[str, object]] = {
    "ugc":       {"wps": 3.0, "vibe": "upbeat and energetic — the creator speaks like a confident TikTok/Instagram influencer: quick, punchy, back-to-back lines with zero dead air or pauses between them"},
    "ugc skill": {"wps": 3.0, "vibe": "upbeat and energetic — the creator speaks like a confident TikTok/Instagram influencer: quick, punchy, back-to-back lines with zero dead air or pauses between them"},
    "review":    {"wps": 2.5, "vibe": "conversational and honest — the creator speaks like they're telling a friend about the product, natural pauses between lines are allowed as long as no non-speech sound fills them"},
    "presenter": {"wps": 2.5, "vibe": "warm, confident, and unhurried — the presenter speaks like a well-prepared creator delivering a scripted line, natural rhythm and slight pauses between sentences are allowed"},
}


def _scripting_seconds(duration_seconds: int) -> int:
    """Seedance uses -1 to mean 'model chooses duration'. Script generators
    still need a concrete number to word-budget against, so pin -1 to 15s
    (the current Seedance 2.0 cap for UGC-family styles).
    """
    return 15 if duration_seconds == -1 else duration_seconds


def _pacing_math(style_key: str, duration_seconds: int) -> tuple[int, float, int, int]:
    """Single source of truth for pacing math across generators + directive.

    Returns (scripting_seconds, wps, word_budget, line_count).

    - scripting_seconds: how many seconds of screen time we're writing for.
    - wps: words per second the style is paced at (from _STYLE_PACING).
    - word_budget: total spoken words across all lines. int(...) not round(...)
      so it skews slightly conservative — never tells Seedance to hit a pace
      faster than the script was written for.
    - line_count: how many discrete dialogue beats the script should have.
      Matches ecommerceskills.md Template C's opening/feature/signoff shape:
      shorter clips get fewer, more punchy beats; longer clips get an
      additional middle beat so there's a real arc.
    """
    scripting_seconds = _scripting_seconds(duration_seconds)
    pacing = _STYLE_PACING.get(style_key.lower(), _STYLE_PACING["ugc"])
    wps = float(pacing["wps"])
    word_budget = int(scripting_seconds * wps)
    if scripting_seconds < 10:
        line_count = 2
    elif scripting_seconds < 14:
        line_count = 3
    else:
        line_count = 4
    return scripting_seconds, wps, word_budget, line_count


def _ugc_articulation_directive(duration_seconds: int, style_key: str = "ugc") -> str:
    scripting_seconds, wps, word_budget, _ = _pacing_math(style_key, duration_seconds)
    vibe = _STYLE_PACING.get(style_key.lower(), _STYLE_PACING["ugc"])["vibe"]
    return (
        "Speech delivery (strict): all dialogue is spoken in clear, fluent English with correct "
        "pronunciation of every word. No mumbling, no slurring, no filler sounds (\"uh\", \"um\", "
        "humming, throat noises), no invented or nonsense syllables. "
        f"Pace is {vibe}. Each line flows into the next; no slow or drawn-out delivery within a line. "
        f"Total spoken words across all lines must not exceed {word_budget} words "
        f"({scripting_seconds} seconds × {wps} words/sec) — keep lines short enough that they fit "
        "at this pace without rushing. If a line is shorter than this budget allows, hold silence "
        "after the final syllable rather than extending the delivery or improvising extra sound. "
        "CRITICAL: the audio track must contain ONLY the quoted dialogue lines and background music/ambience. "
        "Absolutely NO gibberish, no nonsense syllables, no unintelligible muttering, no invented words, "
        "no filler noise of any kind between or around the spoken lines, and no trailing sound past "
        "the final spoken word. Silence is preferable to any non-speech noise. Every sound in the audio "
        "must be either a clearly spoken word from the quoted lines, a named background music element, "
        "or a named ambient sound. Nothing else.\n\n"
        "No on-screen text: do NOT generate any captions, subtitles, auto-captions, burned-in "
        "text, lower thirds, chyrons, watermarks, logos, on-screen dialogue transcription, or "
        "any other text overlay of any kind. The video frame must contain no rendered text "
        "whatsoever."
    )


class LLMProvider:
    async def generate_prompt(self, product: ProductRow, config: VideoConfig) -> str:
        raise NotImplementedError


class SeedanceProvider:
    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        raise NotImplementedError


class OpenAICompatibleLLMProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_prompt(self, product: ProductRow, config: VideoConfig) -> str:
        style_key = (product.video_style or config.style).strip().lower()
        effective_duration = product.duration_seconds or config.duration_seconds

        # UGC Skill path: LLM generates the full Seedance prompt using UGC_videos.md as system prompt
        if style_key == "ugc skill" and self.settings.llm_api_base and self.settings.llm_api_key:
            return await self._generate_ugc_skill_prompt(
                product_name=product.product_name,
                product_description=product.product_description,
                duration_seconds=effective_duration,
                aspect_ratio=config.aspect_ratio,
            )

        ugc_dialogue: list[str] | None = None
        if style_key == "ugc" and self.settings.llm_api_base and self.settings.llm_api_key:
            ugc_dialogue = await self._generate_ugc_dialogue(
                product_name=product.product_name,
                product_description=product.product_description,
                duration_seconds=effective_duration,
            )

        review_dialogue: list[str] | None = None
        if style_key == "review" and self.settings.llm_api_base and self.settings.llm_api_key:
            review_dialogue = await self._generate_review_script(
                product_name=product.product_name,
                product_description=product.product_description,
                duration_seconds=effective_duration,
            )

        presenter_script: str | None = None
        if style_key == "presenter" and self.settings.llm_api_base and self.settings.llm_api_key:
            presenter_script = await self._generate_presenter_script(
                product_name=product.product_name,
                product_description=product.product_description,
                duration_seconds=effective_duration,
            )

        # Component inventory (ecommerceskills.md Step 1) — non-UGC styles only.
        # UGC and UGC Skill deliberately skip: UGC uses a fixed template with
        # no macro close-ups; UGC Skill authors its own scene from UGC_videos.md.
        components: list[str] | None = None
        if style_key not in {"ugc", "ugc skill"} and self.settings.llm_api_base and self.settings.llm_api_key:
            components = await self._extract_component_inventory(
                product_name=product.product_name,
                product_description=product.product_description,
            )

        fallback_prompt = build_prompt(
            product,
            config,
            ugc_dialogue=ugc_dialogue,
            components=components,
            review_dialogue=review_dialogue,
            presenter_script=presenter_script,
        )
        # Polish is disabled globally. The deterministic builders in prompt_builder.py
        # already emit fully-formed Seedance prompts with the ecommerceskills.md
        # universal rules baked in (component lock, unseen sides, no disassembly,
        # style block, copyright clauses). The polish LLM had no context about
        # style-specific rules and consistently drifted output toward markdown
        # tables, hardcoded timestamps, emoji headers, and (for UGC) multi-shot
        # jump cuts — all of which Seedance parses worse than plain prose.
        return fallback_prompt

    async def _generate_ugc_skill_prompt(
        self,
        product_name: str,
        product_description: str,
        duration_seconds: int,
        aspect_ratio: str,
    ) -> str:
        ugc_skill_path = Path(__file__).resolve().parents[2] / "Doc" / "UGC_videos.md"
        system = ugc_skill_path.read_text(encoding="utf-8")

        scripting_seconds = _scripting_seconds(duration_seconds)
        user = (
            f"Product name: {product_name}\n"
            f"Product description: {product_description}\n"
            f"Requested style: UGC\n"
            f"Target video duration: {scripting_seconds} seconds\n"
            f"Aspect ratio: {aspect_ratio}\n"
            "IMPORTANT: You cannot see the reference images. Do not assume the "
            "performer's gender, age, or appearance. Use a gender-neutral name "
            "(e.g. Alex, Sam, Jordan, Robin, Casey) and they/them pronouns throughout. "
            "Do not use gendered terms like 'her smile', 'his hand', 'she leans' — "
            "use 'their smile', 'their hand', 'they lean'. "
            "If the product description mentions a real brand name (e.g. JBL, Apple, "
            "Sony), do NOT reproduce or reference that brand in the prompt. Refer to "
            "it only as 'the product' or 'the speaker' or 'the phone' generically."
        )

        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _generate_ugc_dialogue(
        self,
        product_name: str,
        product_description: str,
        duration_seconds: int,
    ) -> list[str]:
        scripting_seconds, _, word_budget, line_count = _pacing_math("ugc", duration_seconds)
        # Each line gets an equal share of the word budget
        words_per_line = word_budget // line_count

        system = (
            "You write short-form UGC voiceover SCRIPTS — the exact words a real "
            "creator would say into their phone camera about a product they just "
            "tried. This is script-writing, not feature-extraction. Output ONLY "
            "the numbered lines — no intro, no explanation, no headers, no extra text."
        )
        user = (
            f"Product: {product_name}\n"
            f"Description: {product_description}\n\n"
            f"Write a {scripting_seconds}-second first-person UGC voiceover for this product "
            f"as {line_count} spoken lines said back-to-back by ONE creator in ONE continuous "
            "take. It must sound like a real person talking to their phone, not an ad read.\n\n"
            "Script shape (this is the whole point — follow it):\n"
            "- Line 1 is a REACTION or HOOK, never a spec. Open with the speaker's honest, "
            "in-the-moment response. Good openers: 'Okay so...', 'Wait — ...', 'I've been "
            "using this for a week and...', 'You guys...', 'Hear me out —...'. Bad: 'This product "
            "has 35-hour battery life.'\n"
            "- Middle line(s) reveal the WHY behind the reaction — the specific concrete moment "
            "or benefit that caused it. Ground it in real use: what they were doing, when they "
            "noticed, how it felt. Not a spec sheet.\n"
            "- Final line is a personal SIGN-OFF or recommendation. Good closers: 'Honestly, "
            "grab one.', 'I'm not going back.', 'Do yourself a favor.', 'Ten out of ten.'\n"
            "- Lines must THREAD — each one flows out of the last with connective tissue "
            "(pronouns, 'so...', 'and honestly...', 'the crazy part is...', 'that's why...'). "
            "They are not bullets; they are ONE person talking.\n"
            "- First-person singular throughout ('I', 'me', 'my'). The speaker has an opinion.\n\n"
            "Hard constraints:\n"
            f"- Total words across ALL lines: at most {word_budget} words (this fits {scripting_seconds}s at natural pace).\n"
            f"- Each line: at most {words_per_line} words. Short beats sound punchier.\n"
            "- Plain everyday English. No brand names, model numbers, technical jargon, "
            "hyphenated compound words, or numbers with units the speaker wouldn't naturally say.\n"
            "- Extract real concrete benefits from the description — do not invent facts.\n\n"
            "Worked example (different product, same shape):\n"
            "Product: reusable water bottle with vacuum insulation, keeps drinks cold 24h.\n"
            "Script:\n"
            "1. Okay I've had this bottle a full day.\n"
            "2. The ice from this morning is still ice.\n"
            "3. And the outside stays completely dry.\n"
            "4. Honestly just get one.\n\n"
            "Notice: line 1 reacts ('okay I've had...'), line 2 reveals the why ('the ice... still ice'), "
            "line 3 threads with 'And', line 4 signs off with 'Honestly just get one.' That is the shape.\n\n"
            f"Now write EXACTLY {line_count} lines for the product above, following this shape. "
            "Numbered output only:\n"
            + "\n".join(f"{i}. <line>" for i in range(1, line_count + 1))
        )

        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()

            lines = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                # Strip leading "1. " "2. " etc.
                cleaned = re.sub(r"^\d+\.\s*", "", line).strip().strip('"')
                if cleaned:
                    lines.append(cleaned)
            if len(lines) >= 2:
                return lines[:line_count]
        except Exception as exc:
            print(f"[llm] _generate_ugc_dialogue failed: {exc}", flush=True)
        return []


    async def _generate_review_script(
        self,
        product_name: str,
        product_description: str,
        duration_seconds: int,
    ) -> list[str]:
        """Reviewer voiceover lines — same reaction/why/thread/sign-off shape
        as UGC, but tuned for review pacing: 2.5 wps (creators reviewing pause,
        hold the product up, look at it) and slightly longer lines.
        """
        scripting_seconds, _, word_budget, line_count = _pacing_math("review", duration_seconds)
        words_per_line = word_budget // line_count

        system = (
            "You write short-form product REVIEW voiceover scripts — the exact "
            "words a real creator would say holding the product on camera. "
            "Reviews sound honest, not shilled. Output ONLY the numbered lines "
            "— no intro, no headers, no explanation."
        )
        user = (
            f"Product: {product_name}\n"
            f"Description: {product_description}\n\n"
            f"Write a {scripting_seconds}-second first-person REVIEW voiceover as "
            f"{line_count} spoken lines said back-to-back by ONE creator holding "
            "the product on camera. It must sound like a real honest review, not "
            "an ad read.\n\n"
            "Review shape (follow it exactly):\n"
            "- Line 1: TIME-ANCHORED OPENER — how long they've had/used it. "
            "Good: 'Okay I've been using this for about a week now.', "
            "'I've had this in my rotation for a few weeks.', "
            "'Been trying this out and I have thoughts.'. Bad: 'This product has X spec.'\n"
            "- Middle line(s): the HONEST POSITIVE — one specific real-use moment "
            "or benefit that surprised the creator. Ground it in what they were "
            "doing when they noticed. NOT a spec list.\n"
            "- Optional (if 4 lines): a SMALL CAVEAT that makes the review sound "
            "honest — a mild trade-off, a preference, a 'this is best for X kind "
            "of person' comment. It must be actual criticism or contrast, not a "
            "usage instruction (do NOT write 'just remember to shake it', 'you "
            "have to charge it first', or any other how-to tip — those are "
            "manuals, not reviews). Good caveats: 'It's a bit pricey for what it "
            "is.', 'Wish it came in more colors.', 'Not for you if you prefer "
            "matte finishes.', 'Takes a day to get used to.', 'Only downside is "
            "the size.'. Never trash the product; add credibility through mild "
            "honest limitation.\n"
            "- Final line: a PERSONAL RECOMMENDATION. Good: 'I'd genuinely "
            "recommend it.', 'Worth every penny.', 'I'm keeping this one.', "
            "'Do it.'\n"
            "- Lines must THREAD with connective tissue: pronouns, 'so...', "
            "'the thing is...', 'and honestly...', 'that said...'.\n"
            "- First-person singular throughout ('I', 'me', 'my'). Speaker has "
            "an opinion.\n"
            "- Choose a PERSONA from the product category (skincare creator, tech "
            "reviewer, menswear guy, home-goods reviewer, etc.) and write in "
            "that voice. Different products should sound like different creators.\n\n"
            "Hard constraints:\n"
            f"- Total words across ALL lines: at most {word_budget} words "
            f"(fits {scripting_seconds}s at review pace, ~2.5 wps).\n"
            f"- Each line: at most {words_per_line} words. Slightly longer than "
            "UGC — reviews breathe more.\n"
            "- Plain everyday English. No brand names, model numbers, technical "
            "jargon, hyphenated words, or numbers with units the speaker wouldn't "
            "naturally say.\n"
            "- Extract real concrete benefits from the description — do not invent facts.\n\n"
            "Worked example (different product, same shape):\n"
            "Product: reusable water bottle with vacuum insulation, keeps drinks cold 24h.\n"
            "Script:\n"
            "1. Been using this bottle every day for a month.\n"
            "2. I put ice in it in the morning and it's still ice at dinner.\n"
            "3. Not gonna lie, it's heavier than my old one.\n"
            "4. But honestly, worth it, I'd get it again.\n\n"
            "Notice: line 1 time-anchors, line 2 gives the honest positive with "
            "a real moment, line 3 adds a caveat that makes it feel real, line 4 "
            "signs off with recommendation. That is the shape.\n\n"
            f"Now write EXACTLY {line_count} lines for the product above, "
            "following this shape. Numbered output only:\n"
            + "\n".join(f"{i}. <line>" for i in range(1, line_count + 1))
        )
        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()
            lines: list[str] = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                cleaned = re.sub(r"^\d+\.\s*", "", line).strip().strip('"')
                if cleaned:
                    lines.append(cleaned)
            if len(lines) >= 2:
                return lines[:line_count]
        except Exception as exc:
            print(f"[llm] _generate_review_script failed: {exc}", flush=True)
        return []

    async def _generate_presenter_script(
        self,
        product_name: str,
        product_description: str,
        duration_seconds: int,
    ) -> str:
        """Talking-head presenter script — one flowing spoken paragraph, said
        verbatim by the model in one continuous take. Different from Review
        (which is a handheld phone review); Presenter is a produced
        talking-head with a written script the presenter reads.
        """
        # Presenter delivers as one flowing paragraph, not numbered lines,
        # so line_count is unused here — we only need the word budget.
        scripting_seconds, _, word_budget, _ = _pacing_math("presenter", duration_seconds)

        system = (
            "You write talking-head presenter scripts for ecommerce videos — "
            "the exact words a presenter reads to camera in one continuous take. "
            "Output ONLY the script as a single paragraph — no numbered lines, "
            "no intro, no headers, no explanation, no quote marks around it."
        )
        # Aim for 80-100% of the word budget — the LLM tends to undershoot
        # when only given a max, so give it a target too.
        target_low = int(word_budget * 0.8)
        user = (
            f"Product: {product_name}\n"
            f"Description: {product_description}\n\n"
            f"Write a {scripting_seconds}-second presenter script the model reads "
            "to camera in one continuous flow. Warm, confident, conversational "
            "tone — like a well-prepared creator, not a formal narrator.\n\n"
            "Shape:\n"
            "- Hook the viewer in the first sentence with the product's most "
            "compelling benefit (never open with the raw product name — "
            "certainly never with a spec-sheet header like 'Style:' or 'Fabric:').\n"
            "- Middle: 2-3 sentences on the specific concrete benefits — what "
            "makes it worth having, in plain human language. Use real detail "
            "from the description; don't just gesture at 'quality' abstractly.\n"
            "- Close with a soft personal recommendation ('honestly worth a look', "
            "'I'd grab one', 'give it a try').\n"
            "- Sentences flow into each other naturally — this is one continuous "
            "spoken paragraph, not bullet points.\n\n"
            "Hard constraints:\n"
            f"- Aim for {target_low}–{word_budget} words total. At {scripting_seconds}s of screen time "
            "the presenter has room for a real script — do NOT undershoot the budget; "
            "short scripts leave dead air that Seedance fills with filler noise.\n"
            "- Plain everyday English. Do NOT read out spec-sheet headers like "
            "'Style:', 'Fabric:', 'Comfort:' — translate them into normal "
            "human sentences.\n"
            "- No brand names, model numbers, technical jargon, hyphenated words, "
            "or numbers with units the presenter wouldn't naturally say aloud.\n"
            "- Extract real concrete benefits from the description — do not "
            "invent facts.\n"
            "- No 'welcome to my channel' or similar throat-clearing. Start "
            "directly with the hook.\n\n"
            "Worked example (different product, same shape, ~25 words for 10s):\n"
            "Product: reusable water bottle, keeps drinks cold 24h, vacuum insulated.\n"
            "Script: If you want a bottle that actually holds ice all day, this is the one. "
            "The insulation genuinely works, it fits any cup holder, and the lid seals "
            "tight in a bag. Honestly worth picking up.\n\n"
            "Now write the script for the product above. Plain paragraph, no "
            "numbering, no quotes around it:"
        )
        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()
            # Strip surrounding quotes if the model added them despite instructions
            return raw.strip().strip('"').strip("'").strip()
        except Exception as exc:
            print(f"[llm] _generate_presenter_script failed: {exc}", flush=True)
            return ""

    async def _extract_component_inventory(
        self,
        product_name: str,
        product_description: str,
    ) -> list[str]:
        """Extract distinct physical components per ecommerceskills.md Step 1.

        Small parts (lids, caps, straps, hinges, ports, buttons) are where AI
        video models drift most in close-ups. Naming and verbally describing
        each one in the prompt reduces drift dramatically.
        """
        system = (
            "You extract a product's distinct physical components from a description. "
            "For each component, write ONE short line: '<component name>: <one-line "
            "verbal description of shape/material/geometry>'. Include only components "
            "the description clearly implies exist. Do not invent parts. Output ONLY "
            "the numbered lines — no headers, no intro, no explanation."
        )
        user = (
            f"Product: {product_name}\n"
            f"Description: {product_description}\n\n"
            "List 3-8 distinct physical components with one-line verbal descriptions. "
            "Examples of components: lid/cap, spout/nozzle, strap, zipper pull, clasp, "
            "hinge, buttons, ports, stitching, base, dial/bezel, band, lens, temple, "
            "sole/upper/lacing, handle, wheels. Skip generic 'body' or 'exterior'.\n\n"
            "Output format (numbered, one per line):\n"
            "1. <component>: <one-line description>\n"
            "2. <component>: <one-line description>\n"
            "..."
        )
        url = self.settings.llm_api_base.rstrip("/") + "/chat/completions"
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"].strip()
            components: list[str] = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                cleaned = re.sub(r"^\d+\.\s*", "", line).strip()
                if cleaned:
                    components.append(cleaned)
            return components[:8]
        except Exception as exc:
            print(f"[llm] _extract_component_inventory failed: {exc}", flush=True)
            return []


class PromptOnlySeedanceProvider(SeedanceProvider):
    """Saves the generated prompt to a JSON file and marks the product done — never calls Seedance."""

    def __init__(self, videos_dir: Path) -> None:
        self.videos_dir = videos_dir

    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        artifact_path = self.videos_dir / f"{product.id}_prompt.json"
        artifact = {
            "mode": "prompt_only",
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.product_name,
            "video_style": product.video_style,
            "duration_seconds": config.duration_seconds,
            "prompt": prompt,
        }
        artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
        return {
            "provider_job_id": f"prompt-only-{product.id}",
            "output_path": str(artifact_path),
            "download_url": None,
            "status": "completed",
        }


class HTTPSeedanceProvider(SeedanceProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.asset_library = AssetLibraryService(settings)
        base_url = settings.ark_api_base or settings.seedance_api_base
        if not settings.seedance_api_key:
            raise RuntimeError("Seedance credentials are not configured.")
        try:
            from byteplussdkarkruntime import Ark
        except ImportError as exc:  # pragma: no cover - guarded for environments without live SDK deps
            raise RuntimeError("byteplus-python-sdk-v2 is required for live Seedance generation.") from exc

        self.client = Ark(api_key=settings.seedance_api_key, base_url=base_url) if base_url else Ark(
            api_key=settings.seedance_api_key
        )

    async def generate_video(
        self,
        product: ProductExecutionStatus,
        prompt: str,
        config: VideoConfig,
        product_assets: list[str],
        model_assets: list[str],
        batch_reference_images: list[str],
        batch_reference_videos: list[str],
        audio_files: list[str],
    ) -> dict[str, str | None]:
        resolved_model_assets = [await self.asset_library.ensure_reference_image_asset(asset) for asset in model_assets]
        reference_images = [value for value in [*product_assets, *resolved_model_assets, *batch_reference_images] if value]
        reference_videos = [value for value in batch_reference_videos if value]
        reference_audio = [value for value in audio_files if value]
        ratio_map = {
            "16:9": "16:9",
            "9:16": "9:16",
            "1:1": "1:1",
            "4:3": "4:3",
            "3:4": "3:4",
            "21:9": "21:9",
        }
        ratio = ratio_map.get(config.aspect_ratio, "16:9")

        style_key = (config.style or "").strip().lower()
        if style_key in {"ugc", "ugc skill", "review", "presenter"} and config.sound_required:
            # Skip append if the prompt already contains a speech-delivery block
            # (UGC Skill template embeds its own copy). Duplicate/near-duplicate
            # instructions reduce Seedance's adherence — one clean copy is better.
            if "Speech delivery (strict)" not in prompt:
                prompt = prompt.rstrip() + "\n\n" + _ugc_articulation_directive(config.duration_seconds, style_key)

        prompt = _sanitize_for_audio_policy(prompt)

        content_items = _build_seedance_content(
            prompt=prompt,
            reference_images=reference_images,
            reference_videos=reference_videos,
            reference_audio=reference_audio,
        )

        payload = {
            "model": self.settings.seedance_model,
            "content": content_items,
            "generate_audio": config.sound_required,
            "ratio": ratio,
            "duration": config.duration_seconds,
            "resolution": config.resolution,
            "watermark": False,
        }
        task_response = await self._create_task_with_asset_retry(payload)
        task_data = task_response.model_dump() if hasattr(task_response, "model_dump") else json.loads(task_response.to_json())
        task_id = str(task_data.get("id") or task_data.get("task_id") or task_data.get("job_id") or uuid.uuid4())
        final_data = await self._wait_for_task(task_id)
        final_status = str(final_data.get("status") or "").lower()
        if final_status != "succeeded":
            error_message = None
            if isinstance(final_data.get("error"), dict):
                error_message = final_data["error"].get("message")
            raise RuntimeError(error_message or f"Seedance task ended with status: {final_status or 'unknown'}")

        content = final_data.get("content") if isinstance(final_data.get("content"), dict) else {}
        download_url = content.get("video_url") or content.get("file_url") or content.get("last_frame_url")
        usage = final_data.get("usage") if isinstance(final_data.get("usage"), dict) else {}
        token_consumption = _extract_token_consumption(usage)
        token_unit_price = _seedance_token_unit_price_per_million(
            resolution=config.resolution,
            includes_input_video=bool(reference_videos),
        )
        estimated_price_usd = _estimate_price_usd(token_unit_price, token_consumption)

        return {
            "provider_job_id": task_id,
            "output_path": None,
            "download_url": download_url,
            "token_consumption": token_consumption,
            "token_unit_price_per_million": token_unit_price,
            "estimated_price_usd": estimated_price_usd,
            "status": "completed",
        }

    async def _wait_for_task(self, task_id: str) -> dict[str, object]:
        delay_seconds = max(1, self.settings.seedance_poll_interval_seconds)
        timeout_seconds = max(delay_seconds, self.settings.seedance_timeout_seconds)
        max_attempts = max(1, (timeout_seconds + delay_seconds - 1) // delay_seconds)
        for _ in range(max_attempts):
            task = await asyncio.to_thread(self.client.content_generation.tasks.get, task_id=task_id)
            data = task.model_dump() if hasattr(task, "model_dump") else json.loads(task.to_json())
            status = str(data.get("status") or "").lower()
            if status in {"succeeded", "failed", "cancelled"}:
                return data
            await asyncio.sleep(delay_seconds)

        raise RuntimeError(
            f"Seedance task timed out before completion after waiting {timeout_seconds} seconds."
        )

    async def _create_task_with_asset_retry(self, payload: dict[str, object]) -> object:
        max_attempts = 12
        delay_seconds = 10
        last_error: Exception | None = None

        for attempt in range(max_attempts):
            try:
                return await asyncio.to_thread(self.client.content_generation.tasks.create, **payload)
            except Exception as exc:  # noqa: BLE001
                if not _is_asset_processing_error(exc) or attempt == max_attempts - 1:
                    raise
                last_error = exc
                await asyncio.sleep(delay_seconds)

        if last_error is not None:
            raise last_error
        raise RuntimeError("Unable to create Seedance task.")


def _to_ark_asset_url(reference: str) -> str:
    if reference.startswith(("http://", "https://", "data:")):
        return reference

    path = Path(reference)
    if not path.exists():
        return reference

    mime_type, _ = mimetypes.guess_type(str(path))
    if not mime_type:
        mime_type = "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_seedance_content(
    *,
    prompt: str,
    reference_images: list[str],
    reference_videos: list[str],
    reference_audio: list[str],
) -> list[dict[str, object]]:
    content_items: list[dict[str, object]] = [{"type": "text", "text": prompt}]
    for image_reference in reference_images:
        content_items.append(
            {
                "type": "image_url",
                "image_url": {"url": _to_ark_asset_url(image_reference)},
                "role": "reference_image",
            }
        )
    for video_reference in reference_videos:
        content_items.append(
            {
                "type": "video_url",
                "video_url": {"url": _to_ark_asset_url(video_reference)},
                "role": "reference_video",
            }
        )
    for audio_reference in reference_audio:
        content_items.append(
            {
                "type": "audio_url",
                "audio_url": {"url": _to_ark_asset_url(audio_reference)},
                "role": "reference_audio",
            }
        )
    return content_items


def _is_asset_processing_error(error: Exception) -> bool:
    message = str(error).lower()
    return "asset is still processing" in message or "not available yet" in message


def _extract_token_consumption(usage: dict[str, object]) -> int | None:
    for key in ("total_tokens", "completion_tokens", "tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(round(value))
    return None


def _seedance_token_unit_price_per_million(*, resolution: str, includes_input_video: bool) -> float | None:
    _ = resolution
    return 4.3 if includes_input_video else 7.0


def _estimate_price_usd(token_unit_price_per_million: float | None, token_consumption: int | None) -> float | None:
    if token_unit_price_per_million is None or token_consumption is None:
        return None
    return round(token_unit_price_per_million * token_consumption / 1_000_000, 6)


def build_providers(settings: Settings) -> tuple[LLMProvider, SeedanceProvider]:
    llm_provider = OpenAICompatibleLLMProvider(settings)
    if settings.seedance_mode == "prompt_only":
        seedance_provider: SeedanceProvider = PromptOnlySeedanceProvider(settings.videos_dir)
    else:
        seedance_provider = HTTPSeedanceProvider(settings)
    return llm_provider, seedance_provider
