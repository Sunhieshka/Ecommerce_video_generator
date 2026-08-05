---
name: ecommerce-video-prompts
description: Generate production-ready AI video generation prompts (Seedance-style) for ecommerce products across multiple styles — UGC/vlog, studio product showcase, lifestyle ad, fashion catalogue, timestamped feature showcase, and long-format multi-shot videos with text overlays and motion graphics. Use this skill whenever the user shares product images and/or a product description and wants a video prompt, product video, ad video, UGC video, catalogue video, or showcase video generated for it — even if they don't say "prompt" explicitly. Also use when the user asks to convert product listings, spec sheets, or reference images into video generation prompts.
---

# Ecommerce Video Prompt Generator

This skill turns **product inputs (reference images + product description/specs)** into a **finished, copy-paste-ready video generation prompt** in one of several proven styles. Every output follows the master formula:

> **Prompt Formula:** Subject + Motion + Environment (Optional) + Camera Movement/Cut (Optional) + Dialogues (Optional) + Aesthetic Description (Optional) + Audio (Optional)

---

## Step 1 — Understand the product from the inputs

Before writing anything, extract from the provided images and description:

| What to extract | Why it matters |
|---|---|
| **Product category** (beauty, clothing, electronics, appliance, shoes, bag, eyewear, furniture, etc.) | Determines which template family to use |
| **Exact visual identity**: colorway, materials, textures, finish, hardware, logo text and placement, ports/buttons, stitching, silhouette | Must be locked to references in the prompt ("exact colorway, sole, lacing, and logo matching the reference") |
| **Key features & benefits** (from the description/specs): battery life, elasticity, IP rating, laptop sleeve, spring hinges, etc. | These become the demonstrated features, taglines, text overlays, and voiceover lines |
| **Brand text present on the product** | Reference it only as it appears in the images — never invent text |
| **Number of reference images available** | Assign each an `@imageN` tag and state what each one shows |
| **Component inventory** (see below) | Small parts are where AI video models drift — each must be individually locked |

**Component inventory (mandatory):** List every distinct physical component of the product and write a one-line verbal description of each, grounded strictly in what the reference images show. Examples: lid/cap (type: screw-top / flip-top / straw; handle loop shape; color), spout/nozzle, strap, zipper pull, clasp, buttons, ports, stitching, base. For each component also record **which @image shows it and from what angle**. Components NOT clearly visible in any reference (e.g., the top of a lid, the back panel, an interior) go on a "not covered" list — these drive Step 3's shot restrictions.

If the target style, duration, model demographics, or platform are unclear, ask ONE short clarifying question. Otherwise, infer sensibly (defaults: 10s product showcase for hard goods; UGC for beauty/fashion/phones aimed at social).

## Step 2 — Choose the style

| Style | Best for | Duration | People? |
|---|---|---|---|
| **A. UGC vlog (montage)** | Beauty, personal care | 10–15s | Yes, selfie aesthetic |
| **B. UGC TikTok multi-shot** | Clothing, fashion | 15–30s | Yes, fast cuts, dialogue |
| **C. UGC single continuous selfie** | Phones, gadgets, "talking review" | 10–20s | Yes, one shot, no product close-ups |
| **D. Studio turntable showcase** | Mobiles, bags, watches, any hero product | 8–12s | **No** people/hands/faces |
| **E. Timestamped feature showcase** | Bags, eyewear, furniture, home | 10–15s | Hands only (optional) |
| **F. Lifestyle ecommerce ad** | Appliances, home, large goods | 10s | Yes, model interacts with product |
| **G. Fashion catalogue** | Shoes, apparel | 10–15s | Yes, editorial poses |
| **H. Technical/comparative beauty** | Foundation shades, swatches | 12s | Body part only (forearm) |
| **I. Long-format multi-shot** | Electronics with many features | 30–45s (3× shots) | No; overlays + motion graphics |

## Step 3 — Fill the chosen template

Use the templates below. Replace every `[BRACKETED PLACEHOLDER]` with product-specific content extracted in Step 1. Keep the structural sentences intact — they are tuned for the video model.

---

### A. UGC vlog montage (Beauty)

```
Use the provided [PRODUCT NAME] product reference image @image1 to generate a
vlog-style UGC video. Maintain a natural handheld selfie aesthetic, realistic
lighting, and authentic creator energy. Avoid polished commercial or
studio-style visuals. Structure the video as a fast "[PRODUCT NAME/CATEGORY]
throughout my day" montage with natural jump cuts (1–2 seconds per scene):
Voiceover (natural, conversational tone): "[DIALOGUE LINE 1]… [DIALOGUE LINE 2].
And it just works [CONTEXT/USE-CASE, e.g., everywhere, on the go, day and
night] — [SITUATION 1], [SITUATION 2], even [SITUATION 3]. [CLOSING
DESCRIPTOR, e.g., Super comfortable / Totally worth it / Can't go back]."
In the end, model must be of [ETHNICITY] ethnicity and have
[ETHNICITY/REGIONAL] accent.
```

### B. UGC TikTok multi-shot (Clothing)

```
Create a fast-paced, TikTok-style video with the model's natural, upbeat voice
speaking quickly, similar to a friend sharing something. A [AGE]-year-old
[ETHNICITY] [GENDER] holds her phone, taking a selfie from the camera, wearing
[PRODUCT/OUTFIT] from a reference image.

Shot 1: Model ([ACTION/POSE DESCRIPTION], confidently saying): "[HOOK LINE]."
The model [MOVEMENT, e.g., makes a relaxed turn], showcasing [KEY PRODUCT
FEATURE 1].

Shot 2: Quickly cuts to a close-up of the [PRODUCT], the model [DEMONSTRATION
ACTION, e.g., stretching the fabric] to demonstrate [FEATURE BEING SHOWN,
e.g., elasticity]. The camera quickly zooms in on [DETAIL, e.g.,
waistband/stitching/texture]. The model [SECONDARY DEMO ACTION]. The close-up
switches to a medium shot, the model (while demonstrating, saying):
"[FEATURE CALLOUT LINE]."

Shot 3: Quickly cuts to the [PRODUCT] laid out on [SURFACE, e.g., a
sofa/table]. Her [PET TYPE/BREED], "[PET NAME]," is [PET ACTION, e.g., lying
on it, rubbing against it]. She [TOUCH/DEMO ACTION] to demonstrate [QUALITY,
e.g., softness]. Close-up (voiceover, with [TONE, e.g., a smile and a hint of
exasperation]): "[RELATABLE/PLAYFUL LINE involving pet]."

Shot 4: Cuts back to the model in the full [PRODUCT/OUTFIT], performing
[ACTIVITY, e.g., light yoga stretches] to showcase [QUALITY, e.g.,
comfort/movement]. Model (naturally saying while [ACTIVITY]): "[VERSATILITY
LINE — listing use-cases, e.g., 'I could literally live in this. X, Y, Z...']."

Shot 5: The model [CLOSING ACTION, e.g., stops, picks up phone, waves goodbye]
as she [EXIT ACTION, e.g., walks towards the door], her smile natural and
infectious. Medium shot, (talking casually while [ACTION]): "[SIGN-OFF LINE +
CTA]."

Subtitle: [PROMO TEXT, e.g., "Sale On Now! 🏃‍♀️ Hurry Up!"]
```

### C. UGC single continuous selfie (Electronics)

```
Use the provided [PRODUCT NAME] ([COLOR/VARIANT]) product reference images
@image1 @image2 to generate a vlog-style UGC video. Maintain a natural
handheld selfie aesthetic, realistic lighting, and authentic creator energy.
Avoid polished commercial or studio-style visuals — no product close-ups, no
screen demos, no zoom-ins. This should feel like a single continuous, casual
selfie video of someone just talking to camera while holding their
[product/device].

The model from the reference image @image3 ([AGE RANGE], [ETHNICITY],
[STYLING/APPEARANCE DESCRIPTION]) holds the [PRODUCT NAME] in
[COLOR/VARIANT], taking a selfie-style video, speaking directly to camera in
a natural, upbeat, conversational tone — like he's/she's catching up with a
friend.

Single continuous shot: Model casually [ACTIVITY, e.g., walking / sitting]
(e.g., [SETTING, e.g., outdoors / relaxed indoor setting]), holding the
[product] up at selfie angle, occasionally glancing at it and back to camera.
Natural small movements — [GESTURE 1, e.g., adjusting grip], a slight smile,
casual body language.

Model (talking naturally to camera): "[OPENING REACTION LINE].
[FEATURE/EXPERIENCE LINE 1]. [FEATURE/EXPERIENCE LINE 2]. [SIGN-OFF LINE]."

Subtitle: [PRODUCT NAME] — [COLOR/VARIANT]
```

### D. Studio turntable showcase (product-only)

```
A sleek [product] reference image @image1 centered on a minimalist white
surface with soft studio lighting. Slow turntable rotation. Include macro
close-up cut-ins highlighting [material texture, finish, edges, and key
components]. Clean shadows, cinematic depth of field, photorealistic. Only
the product. No props. No people. No hands. No faces. High-end luxury
commercial aesthetic. Highlights [KEY SPEC 1], [KEY SPEC 2], [KEY SPEC 3].
Ensure music is fully original, generic, copyright-safe, and free from any
identifiable copyrighted or legally protected references.
```

### E. Timestamped feature showcase (bags / eyewear / furniture)

Structure the video in 2–3 second beats. Bag example (15s):

```
A sleek 15-second product showcase video for a [COLOR/MATERIAL] [BAG TYPE]
with [ACCENT MATERIAL/COLOR] accents, set against a clean, softly lit studio
background with subtle gray gradient shadows.

0-3s: Bag rotates slowly on a pedestal, front view showing [SIGNATURE DETAIL,
e.g. zipper style, clasp, logo patch] catching the light.
3-6s: Smooth push-in close-up on [CARRY FEATURE, e.g. top handle, strap], a
hand grabs it and lifts the bag slightly, showcasing [KEY BENEFIT, e.g. "easy
grab and go"].
6-9s: Cut to the [MAIN COMPARTMENT] opening in one fluid motion, camera tilts
down into the interior revealing [INTERIOR FEATURE, e.g. laptop sleeve,
organizer pockets] as [ITEM, e.g. laptop, notebook] slides/fits in smoothly.
9-12s: Quick side-angle shot of [SECONDARY FEATURE, e.g. side pocket,
external strap] in use with [RELEVANT ITEM, e.g. water bottle, phone],
demonstrating [FUNCTIONAL BENEFIT, e.g. flat-pack design, quick access].
12-15s: Final hero shot — the bag is lifted/worn via [CARRY METHOD, e.g.
shoulder straps, top handle], spinning gently to catch light on [TEXTURE
DETAILS, e.g. canvas weave, leather grain, hardware], ending on a clean
product beauty shot with soft studio lighting and subtle depth of field.

Style: minimal, premium, editorial product photography aesthetic. Neutral
color palette ([BAG COLORS] + off-white background). Smooth camera movements,
no jump cuts. Soft directional lighting with gentle shadows to emphasize
texture.
```

Eyewear variant (10s beats): 0-2s rotation on clear acrylic stand highlighting [SIGNATURE DETAIL]; 2-4s macro push-in on lens surface showing [LENS FEATURE] with light flare sweep; 4-6s hand picks up by [TEMPLE/BRIDGE], folds/unfolds to showcase [HINGE/BUILD FEATURE]; 6-8s placed on a face (or gliding toward camera POV) demonstrating [COMFORT FEATURE]; 8-10s final hero shot on reflective surface, slow rotation across [MATERIAL DETAILS]. Close with the same Style block plus the copyright-safe music clause.

Furniture variant (10s beats, no on-screen text): 0-2s wide establishing shot with slow push-in, natural light across [SIGNATURE DETAIL, e.g. tufted backrest, tabletop grain, curved legs]; 2-4s smooth orbit/pan revealing [STRUCTURAL FEATURE, e.g. joinery, upholstery stitching, frame silhouette] from a three-quarter angle; 4-6s macro close-up on [TEXTURE DETAIL, e.g. wood grain, fabric weave, leather finish] with soft raking light; 6-8s a hand or subtle human interaction (e.g. sitting down, opening a drawer, running a hand along the surface) to convey function and comfort; 8-10s final hero shot — camera pulls back to a styled vignette, soft ambient light, still elegant frame with shallow depth of field. Style: minimal, warm, editorial interior/product photography aesthetic. Neutral palette ([FURNITURE COLOR] + soft room tones — beige, white, wood). Smooth, slow camera movements only, no jump cuts, no on-screen text or overlays.

### F. Lifestyle ecommerce ad (appliances)

```
Create a [DURATION]-second premium ecommerce lifestyle video ad for a
[PRODUCT NAME]. Cinematic shot of a [MODEL DESCRIPTION, e.g., young woman] in
@image1 walking toward the [PRODUCT NAME].

[Model reference] in @image2 [PRIMARY INTERACTION, e.g., opens the fridge
smoothly]. [She/He] [SECONDARY ACTION, e.g., takes out a water bottle].

Hero product shot as [model reference] in @image3 faces slightly toward
camera, holding/showcasing [PRODUCT/ITEM, e.g., the water bottle].

Add elegant on-screen text transitions:
"[TAGLINE 1 — brand hook]"
"[TAGLINE 2 — feature highlight]"
"[TAGLINE 3 — CTA]"

Smooth cinematic transitions, polished ecommerce ad finish.
```

### G. Fashion catalogue (shoes / apparel)

```
A confident [gender] model wearing the sports shoes from @image1, @image2,
@image3, neutral activewear, shoes as hero product with exact colorway, sole,
lacing, and logo matching the reference. [he/she] holds slow editorial poses
— weight shift, camera angle moves to below knee area focusing on the shoes,
a controlled 180° turn showing the back, then a side profile stance. Seamless
off-white studio cyclorama, soft even lighting, consistent skin tone across
cuts. Locked-off medium-full shot with one slow push-in to knee-down framing
filling the frame with the shoes; smooth cuts between front, side, and back
angles, each held clean and steady. And a slow camera pull. High texture
fidelity on mesh, leather, and rubber sole. Premium studio-commercial catalog
look. Soft minimal beat, no vocals.
```

Start-frame variant (when a styled model image exists):

```
@Image3 @Image2 @Image1 are references of the product. @Image4 is the start
frame of the video. Generate a premium catalog-style fashion video for
[PRODUCT] from the reference images. Show confident model poses with elegant,
minimal natural movement and clear front/side/back product visibility.
Maintain consistent lighting, skin tones, and details, with high texture
fidelity and no artifacts. Use smooth cuts, steady framing, and a polished
studio-commercial look.
```

### H. Technical/comparative beauty (swatch shade shift)

```
Subject: A forearm positioned diagonally across frame as shown in @image1,
displaying a row of foundation swatches in ascending shade numbers with white
numeral labels beside each. Skin tone on the arm gradually shifts across the
video — starting fair/light, transitioning to medium, then to deep/dark —
while the swatch pattern and layout stay identical throughout.

0:00 -0:03- green must be replaced with a [skin tone]
cut
0:03 -0:06- green must be replaced with a [skin tone]
cut
0:06 -0:09- green must be replaced with a [skin tone]
cut
0:09 -0:12- green must be replaced with a [skin tone]

Camera: Sony VENICE 2, Lens: Zeiss Supreme Prime, Focal Length: 40–50mm,
Camera Aperture: T4
Ensure all music, visuals, characters, logos, brands, and video elements are
fully original, generic, copyright-safe, and free from any identifiable
copyrighted or legally protected references. Do not generate background music.
```

### I. Long-format multi-shot (30–45s electronics)

Break into 3 chained shots of 10–15s each, generated separately and stitched. Rules:

- **Shot 1** establishes: reference lock line, turntable/hero rotation, product name overlay, first feature with a minimal animated icon (e.g., battery icon filling), voiceover introducing the product.
- **Shots 2 and 3** each open with a start-frame lock: `[Image 1] is the start frame. The first frame of the generated video must match [Image 1] exactly, preserve the details.` — where [Image 1] is the final frame of the previous shot. Re-list all product references each time.
- Every shot carries: `Product-only shot, no hands, no people.` + continuation note (`Continuation of Shot 1: opens on the same studio setting.`)
- Feature communication pattern per beat: **minimal motion graphic icon** (battery, Bluetooth pulse splitting into two device icons, sound-wave lines fading on contact for ANC, clock→battery for quick charge) + **Text overlay: "..."** + **Voiceover** line reading the feature naturally.
- Close every shot with the quality block:

```
Throughout: 4K high definition, polished ecommerce ad finish, realistic
materials, smooth cinematic transitions. Product proportions, logo placement,
and [FINISH] identical to references — no redesign, no color shift, no
flickering.
Ensure music is fully original, generic, copyright-safe, and free from any
identifiable copyrighted or legally protected references.
```

- Bookend: the final shot pulls back to the exact hero angle of Shot 1's opening, with a final text summary: `"[PRODUCT NAME]. [TAGLINE]."`

Worked reference (Sony WH-CH720N): Shot 1 = 360° turntable + "Up to 50 Hours Battery Life" battery icon; Shot 2 = orbit to side profile, "Lightweight Over-Ear Design — 192 g", sound-wave DSEE graphic, Bluetooth multipoint icon split, ANC wave-fade graphic; Shot 3 = USB-C cable + rising percentage counter, "3 Min Charge = 1 Hr Playback", mic pulse icon, pull-back hero bookend with "Hear More. Carry Less."

---

## Step 4 — Universal rules (apply to every prompt)

1. **Tag every reference image** as `@image1`, `@image2`, … and state explicitly what each shows or which is a start frame.
2. **Lock the product to the references — at component level.** A generic lock line is not enough; small parts (lids, caps, handles, clasps, zipper pulls, buttons) are the first things video models redesign, especially in macro close-ups. Name each component from the Step 1 inventory explicitly, describe it in words, and tie it to its reference image. Example: *"The lid is a [mint-green screw-top cap with a single flat rectangular carry loop hinged on one side], exactly as shown in @image2 — its shape, loop geometry, proportions, and color must remain identical in every frame and every camera distance, including all close-ups. Zero design deviation, no redesign, no color shift, no morphing between shots, no flickering."* Repeat the component lock inside any timestamp beat that features that component in close-up.
   - **Verbal description is the safety net**: even if the reference image is attached, describing the component's geometry in words dramatically reduces drift. Never write "the lid" bare — always "the [described] lid as shown in @imageN."
3. **No hallucinated text.** Only text overlays/subtitles you explicitly script may appear. On-product text must match the reference images.
4. **Copyright-safe audio clause** whenever audio/music is possible: *"Ensure music is fully original, generic, copyright-safe, and free from any identifiable copyrighted or legally protected references."* Add *"Do not generate background music."* if silence is wanted.
5. **Specify model demographics** (age range, ethnicity, styling) and **accent** for any speaking model — e.g., *"Model must be of Indian ethnicity and have Indian accent."*
6. **Dialogue is written verbatim** in quotes, tone-annotated: `Model (talking naturally to camera): "..."` or `Voiceover (calm, warm female): "..."`.
7. **Camera language**: prefer concrete moves — slow push-in, smooth orbit/pan, controlled 180° turn, locked-off shot, macro close-up cut-in, camera pull-back. Optionally add camera/lens specs for cinematic realism (e.g., `Camera: ARRI Alexa Mini LF, Lens: Zeiss Supreme Prime, Focal Length: 24mm-105mm, Camera Aperture: T2.8`).
8. **Style block last**: aesthetic descriptor + palette (product colors + background tone) + "Smooth camera movements, no jump cuts" (except UGC, where jump cuts are the aesthetic) + lighting note tied to the product's texture.
9. **UGC anti-polish clause**: for styles A–C always include *"Avoid polished commercial or studio-style visuals"* and handheld/selfie aesthetic language.
   - **UGC voiceover is mandatory, never optional.** Every UGC prompt (styles A–C) must include spoken audio — either a scripted voiceover or on-camera dialogue — written out verbatim in quotes with a tone annotation, e.g. `Voiceover (natural, conversational tone): "..."` or `Model (talking naturally to camera): "..."`. Never deliver a silent or music-only UGC prompt. If the user hasn't supplied dialogue, write it yourself from the product's key features (Step 1) in a casual, first-person creator voice, and match the language/accent to the specified model demographics (e.g., Indian ethnicity → Indian accent, optionally Hinglish if the user's market suggests it). Keep lines short and speakable within the video duration (~2.5 words per second).
10. **Timestamps** use the `Ns-Ms:` beat format; keep beats 2–4 seconds and give each beat exactly one job (one feature, one camera move).
11. **Never script a shot the references can't support.** Only write macro close-ups of components that appear clearly in at least one reference image, and match the close-up's angle to that reference (e.g., *"macro close-up on the lid matching the top-down view in @image3"*). If a desired close-up component is on the "not covered" list from Step 1, do one of: (a) ask the user for an additional reference of that component, (b) replace the close-up with a mid-shot where the component stays small in frame, or (c) drop that beat. Never let the model invent detail at high magnification.
12. **Constrain rotation to reference coverage.** Full 360° turntable rotation forces the model to invent unseen sides. If references only cover front/three-quarter views, script a limited orbit instead (e.g., *"slow 90° orbit from front to three-quarter angle"*) or add: *"Sides not visible in the references must remain plain and consistent with the visible design language — do not add new details, seams, logos, or components."*
13. **No opening/disassembly actions without an open-state reference.** Don't script unscrewing lids, opening compartments, unzipping, or removing parts unless a reference image shows that open state — otherwise the model invents interiors and mechanisms (and often mutates the closed-state geometry in the process). Substitute a hand lifting, tilting, or rotating the closed product instead.

## Step 5 — Output format

Deliver to the user:
1. The **final filled prompt** in a code block, ready to paste into the video model.
2. A one-line note listing which `@image` slots they must attach and in what order.
3. If long-format (style I): one code block per shot, clearly labeled Shot 1/2/3, with the start-frame chaining instruction noted between shots.

Do not output the template with placeholders left in — every bracket must be resolved from the product images/description or a stated assumption.

**Pre-output QA checklist** — verify before delivering the prompt:
- [ ] Every distinct component from the Step 1 inventory is named, verbally described, and tied to an @image in the prompt.
- [ ] Every close-up beat targets a component actually visible in a reference, at a matching angle.
- [ ] Any component featured in a close-up has its lock line repeated inside that beat.
- [ ] Rotation range does not exceed reference coverage (or the "unseen sides stay plain" clause is present).
- [ ] No open/disassembled state is scripted without an open-state reference.
- [ ] The global lock line covers geometry, proportions, logo text/placement, colorway, and explicitly says "including all close-ups."
- [ ] If the style is UGC (A–C): the prompt contains verbatim voiceover or on-camera dialogue in quotes with a tone annotation — never silent or music-only.