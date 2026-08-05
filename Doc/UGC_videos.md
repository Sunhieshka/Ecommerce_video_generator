name: UGC_videos description: Turn product info into a production-ready Seedance 2.0 UGC selfie-camera prompt. Uses verbose sectioned structure with tone-labeled voiceover lines, numbered shot beats, and explicit style/audio rules — the shape Seedance parses most reliably for spoken UGC content. Any missing detail (action, environment, ambience) is inferred by the model from product context. Every generated prompt ends with a subtitle-free / no-IP constraint block.

Seedance 2.0 UGC Prompt Builder — verbose format
This skill converts a product description into a production-ready Seedance 2.0 UGC prompt. UGC (user-generated content) here means a single continuous take: a phone held at arm's length, ONE fixed selfie framing, NO cuts, NO camera movement. The performer comes from the supplied reference image and the camera is fixed by the selfie framing, so both of those are locked before generation. The prompt's job is to give Seedance a well-structured brief with clear tone-labeled dialogue lines, explicit shot beats, and firm audio/style/quality rules.

Core principle
Seedance produces cleaner, more coherent spoken audio when the prompt is structured, labelled, and verbose enough to provide temporal scaffolding across the full video duration. Terse minimalist prompts leave gaps that Seedance fills with pauses or gibberish. So the required output is a sectioned document with named blocks, not a one-paragraph script.

Do NOT use camera-movement terms (push-in, pan, tracking, orbit) — the camera is fixed. Do NOT hard-code timestamps (e.g. "0-3s") — Seedance's timestamp support is unstable; let the performance pace itself through the ordered shot beats. Do NOT use "Shot 1 / Shot 2 / Shot 3" cut language; the numbered beats describe continuous action within the single take.

Expected INPUT
The user provides some or all of the following (labelled or freeform — interpret sensibly):
- Product name
- Product description (feature paragraphs)
- Requested style (should be "UGC")
- Target video duration in seconds
- Optional: performer name; if none is given, invent a simple everyday first name

Gap-filling rule
If action, environment, or ambience is missing, infer a natural fitting choice from the product's context and emotional tone. Dialogue is the one thing you must AUTHOR from the product description — extract 2-3 concrete benefits worth saying out loud, then phrase them as short, everyday, spoken sentences a real person would say to a phone camera. Do NOT copy-paste marketing sentences from the description; rewrite them as plain conversational English.

Dialogue rules (this is script-writing, not feature extraction)
The dialogue is the WHOLE point of a UGC video. Write it as a real person's monologue, not as a list of product specs read aloud. Follow this shape exactly:

- **Line 1 is a REACTION or HOOK, never a spec.** Open with the speaker's honest in-the-moment response. Good openers: "Okay so...", "Wait — ...", "I've been using this for a week and...", "You guys...", "Hear me out —...". Bad opener (do not write): "This product has 35-hour battery life."
- **Middle line(s) reveal the WHY** — the specific concrete moment or benefit that caused the reaction. Ground it in real use: what the speaker was doing, when they noticed, how it felt. Not a spec sheet.
- **Final line is a personal SIGN-OFF or recommendation.** Good closers: "Honestly, grab one.", "I'm not going back.", "Do yourself a favor.", "Ten out of ten."
- **Lines must THREAD** — each one flows out of the last with connective tissue (pronouns, "so...", "and honestly...", "the crazy part is...", "that's why..."). They are not bullets; they are ONE person talking in ONE continuous take.
- **First-person singular throughout** ("I", "me", "my"). The speaker has an opinion.

Constraints (still enforced):
- Line count: 4 lines for duration ≥14s, 3 lines for 10–13s, 2 lines for <10s. Real UGC creators pace 3–5 punchy beats across a 15s clip — too few lines leaves unnatural gaps and Seedance fills them with filler noise.
- Total spoken words across all lines: approximately 3 words per second (e.g. 15s video ≈ 45 words total, 10s video ≈ 30 words). This matches real creator pacing; going significantly over causes Seedance to slur or rush, going significantly under leaves dead air.
- Each line short — one clear thought, no subordinate clauses splitting the sentence in half.
- Plain everyday English. AVOID brand names, model numbers, technical jargon, hyphenated compound words, and long or unfamiliar words — Seedance mispronounces these.
- Extract real concrete benefits from the description — do not invent facts.
- Externalize the emotion as concrete physical action (leaning in, tapping the product, brief pause with a smile), not abstract feeling words ("excited", "happy").
- Keep dialogue in ONE consistent language.

Required OUTPUT format (return exactly this shape, filling in every value)

Create a UGC-style product video using the supplied reference images. Do not leave any placeholders unresolved.

Product name: <PRODUCT NAME>
Video duration: <N> seconds
Aspect ratio: 9:16 vertical
Camera: fixed selfie framing, phone held at arm's length, static shot with slight natural handheld shake, performer looking straight into the lens. No camera movement of any kind — no push-in, pan, tracking, or orbit.
Performer: define the person in @Image 1 as <NAME>. <NAME> is on-camera the entire take. No other people appear.

UGC mandatory style rules:
- Natural handheld selfie aesthetic with authentic creator energy.
- Soft phone-camera look, slightly grainy, intimate tone.
- Avoid polished commercial, studio, or advertising visuals.
- Face stays stable without deformation; smooth natural motion, no flicker.

Spoken audio is mandatory (never silent, never music-only). Each line below is spoken on camera by <NAME> as a single continuous take, in this order:

Voiceover (natural, conversational tone): "<DIALOGUE LINE 1>"
(action while speaking line 1: <short concrete physical action, e.g. holds the product up between fingers, gives a small casual smile>)

Voiceover (friendly, confident tone): "<DIALOGUE LINE 2>"
(action while speaking line 2: <short concrete physical action, e.g. taps the product once, leans slightly closer to the lens>)

On-camera dialogue (casual close): "<DIALOGUE LINE 3>"
(action while speaking line 3: <short concrete physical action, e.g. gives a small nod to the camera, tilts the product for a clearer view>)

Shot structure (one continuous selfie take, no cuts):
1. Hook: <NAME> appears in fixed selfie framing with the product already visible, and delivers dialogue line 1 immediately.
2. Middle beat: <NAME> demonstrates or gestures with the product while delivering dialogue line 2. One clear physical action tied to the spoken benefit.
3. Close: <NAME> holds the product in a clear final framing and delivers dialogue line 3 as a direct casual recommendation.

Environment: <one line — location + lighting/tone, e.g. bright sunlit bedroom with soft daylight from a side window>.

Background music: original, generic, copyright-safe, quiet enough not to compete with the spoken dialogue.
Ambient sound: <one short ambience cue, e.g. quiet room-tone>.

Speech delivery (strict): all spoken dialogue must be voiced in clear, fluent English with correct pronunciation of every word. No mumbling, no slurring, no filler sounds ("uh", "um", humming, throat noises), no invented or nonsense words, no muttered or unintelligible syllables. Every syllable must be audible and understandable. Pace is upbeat and energetic — the creator speaks like a confident TikTok/Instagram influencer: quick, punchy, back-to-back lines with zero dead air or pauses between them. Each line flows directly into the next with no gap. No slow or drawn-out delivery. CRITICAL: the audio track must contain ONLY the quoted dialogue lines and background music/ambience. Absolutely NO gibberish, no nonsense syllables, no unintelligible muttering, no invented words, no filler noise of any kind between or around the spoken lines. Silence is preferable to any non-speech noise. Every sound in the audio must be either a clearly spoken word from the quoted lines, a named background music element, or a named ambient sound. Nothing else.

No on-screen text: do NOT generate any captions, subtitles, auto-captions, burned-in text, lower thirds, chyrons, watermarks, logos, on-screen dialogue transcription, or any other text overlay of any kind. The video frame must contain no rendered text whatsoever.

Generate unique assets — image, video and audio — that are original and free from any IP: no copyrighted content, real brands, logos, or identifiable public figures.

Output rules
- Return ONLY the finished prompt as plain text the user can paste directly into Seedance — no code fences, no headers before or after, no explanation.
- Fill in every angle-bracketed placeholder (<NAME>, <PRODUCT NAME>, <N>, <DIALOGUE LINE 1..3>, <action while speaking...>, environment, ambient sound). Leave no bracket unresolved.
- Use exactly the section headers shown, in the exact order shown. Do not rename them, do not reorder them, do not add new sections.
- Use 4 dialogue lines when duration ≥ 14 seconds (add a second middle beat between the friendly-tone line and the on-camera close); use 3 lines when duration is 10-13 seconds; use 2 lines when duration < 10 seconds (drop the middle Voiceover line and its action).

Worked example
INPUT: Product name "Compact Wireless Earbuds". Description mentions 35-hour battery, small pocketable case, 10-minute quick charge for 2 hours playback. Requested style: UGC. Target duration: 15 seconds. Performer name: not given — invent one.

OUTPUT:
Create a UGC-style product video using the supplied reference images. Do not leave any placeholders unresolved.

Product name: Compact Wireless Earbuds
Video duration: 15 seconds
Aspect ratio: 9:16 vertical
Camera: fixed selfie framing, phone held at arm's length, static shot with slight natural handheld shake, performer looking straight into the lens. No camera movement of any kind — no push-in, pan, tracking, or orbit.
Performer: define the person in @Image 1 as Maya. Maya is on-camera the entire take. No other people appear.

UGC mandatory style rules:
- Natural handheld selfie aesthetic with authentic creator energy.
- Soft phone-camera look, slightly grainy, intimate tone.
- Avoid polished commercial, studio, or advertising visuals.
- Face stays stable without deformation; smooth natural motion, no flicker.

Spoken audio is mandatory (never silent, never music-only). Each line below is spoken on camera by Maya as a single continuous take, in this order:

Voiceover (natural, conversational tone — REACTION opener): "Okay I've had these earbuds a full week."
(action while speaking line 1: holds the earbud case up between her fingers with a soft casual smile)

Voiceover (friendly, confident tone — WHY beat): "I've only charged them once and they still work."
(action while speaking line 2: taps the top of the case once, leans slightly closer to the lens)

Voiceover (casual, matter-of-fact tone — THREADED benefit): "And the case fits right in my jeans."
(action while speaking line 3: slips the case into her pocket, small nod to the lens)

On-camera dialogue (personal SIGN-OFF): "Honestly, just get a pair."
(action while speaking line 4: gives a small shrug and a genuine smile to the camera)

Shot structure (one continuous selfie take, no cuts):
1. Hook: Maya appears in fixed selfie framing with the earbud case already visible, and delivers dialogue line 1 (the reaction opener) immediately.
2. Reveal beat: Maya taps the case and leans in while delivering dialogue line 2 (the why). One clear physical action tied to the spoken benefit.
3. Threaded beat: Maya slips the case into her pocket while delivering dialogue line 3.
4. Sign-off: Maya settles the framing and delivers dialogue line 4 as a direct personal recommendation with a small shrug and smile.

Environment: bright sunlit bedroom, soft natural daylight from a side window.

Background music: original, generic, copyright-safe, quiet enough not to compete with the spoken dialogue.
Ambient sound: quiet room-tone.

(Speech delivery and no-on-screen-text blocks omitted here — the template above already declares them once; do NOT include a second copy of either block in the generated output. The single copy from the template is what the model sees.)

Generate unique assets — image, video and audio — that are original and free from any IP: no copyrighted content, real brands, logos, or identifiable public figures.
