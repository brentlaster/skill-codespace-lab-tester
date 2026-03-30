---
name: talk-memorizer
description: "Multi-mode conference talk memorization coach. Helps speakers memorize, practice, and master their conference talks using active recall quizzing, study guide generation, visual mnemonics (memory palace, bizarre imagery), and interactive rehearsal. Manages multiple talks with progress tracking. Use this skill whenever the user mentions memorizing a talk, practicing a presentation, learning a speech, rehearsing slides, studying their script, drilling talk material, preparing to speak, or wants help getting ready to deliver a conference talk. Also trigger when the user says 'quiz me', 'test me on my talk', 'help me practice', 'study mode', 'rehearsal', 'what comes after slide X', 'I need to memorize this', 'memory palace', 'visual mnemonics', or references preparing for an upcoming speaking engagement. Trigger even if the user just says 'practice' or 'drill' in the context of a presentation or talk."
---

# Talk Memorizer

A multi-mode coaching skill that helps speakers internalize and master their conference talks before delivery. Works with paired .pptx slide decks and .md speaker scripts.

## Philosophy

Memorizing a talk isn't about rote recall of every word — it's about owning the material so deeply that you can deliver it naturally, handle interruptions, recover from lost places, and adapt on the fly. The skill uses evidence-based learning techniques: active recall, spaced repetition principles, interleaving, elaborative rehearsal, and — crucially — visual and spatial memory techniques like the method of loci (memory palace) and bizarre imagery associations. These visual techniques tap into the brain's powerful spatial and visual memory systems, which are far stronger than verbal memory alone. The goal is confident, flexible mastery — not word-perfect recitation.

## How It Works

### Input Format

The skill expects paired files for each talk:
- A **speaker script** (.md) with `## [SLIDE N — Title]` markers, stage directions in `*[italics]*`, timing checkpoints, and spoken content
- A **slide deck** (.pptx) for visual reference and slide-content correlation

On first use with a new talk, parse the script to extract:
1. **Slide map**: slide number, title, and section groupings
2. **Key stats & facts**: all specific numbers, percentages, dates, names, and citations
3. **Transitions**: how each section connects to the next (the bridging sentences)
4. **Audience interactions**: polls, exercises, pauses, and decision moments
5. **Timing checkpoints**: target elapsed times at each section
6. **Stage directions**: gestures, tone shifts, pacing notes
7. **Humor/anecdote inventory**: optional humor beats from appendices or inline
8. **Core concepts**: the main ideas, principles, and frameworks (for mnemonic generation)

Store this parsed data as a structured JSON file alongside the talk files for fast access in future sessions (e.g., `<talk-name>-parsed.json`).

### Multi-Talk Management

Maintain a dashboard file (`talk-dashboard.json`) tracking:
- All loaded talks (name, file paths, total slides, duration)
- Per-talk progress: which modes have been used, areas of strength/weakness
- Suggested next practice focus based on what's least-practiced or weakest

When the user starts a session, show a brief dashboard summary: which talks are loaded, rough readiness assessment for each, and a suggestion for what to practice. Keep it concise — 3-4 lines max.

---

## Modes

The user can request any mode at any time. If they just say "let's practice" or "help me prepare," suggest the mode that would be most beneficial based on their progress. Always let them override.

### Mode 1: Study Guide Generation

**Trigger phrases**: "study guide", "cheat sheet", "summary", "key points", "give me something to review"

Generate focused study materials. These should be saved as files the user can review on their own. Offer these formats:

**1a. Structure Map** — A visual outline showing the arc of the talk:
- Three-arc grouping (the talk's own structural metaphor if it has one)
- Section flow with 2-3 word memory anchors per slide
- Transition sentences that bridge each section
- Save as markdown with clear visual hierarchy

**1b. Stats & Facts Drill Sheet** — Every specific number, date, name, and citation:
- Organized by slide/section
- Include the context (not just "97%" but "97% of breached orgs had no AI access controls — IBM/Ponemon 2025")
- Group related stats together
- Save as markdown

**1c. Timing Guide** — A compact reference showing:
- Target time at each checkpoint
- Which sections can be compressed if running long
- Which sections are "anchors" that shouldn't be cut
- Save as markdown

**1d. Transition Map** — Just the bridges between sections:
- What the last sentence of each section is
- What the first sentence of the next section is
- The logical connection between them
- Save as markdown

**1e. Audience Interaction Cheat Sheet** — Every poll, exercise, pause, and decision moment:
- What to say to set it up
- How long to pause
- What to do with the response
- Save as markdown

When generating study materials, read the pptx skill at `/sessions/gifted-peaceful-faraday/mnt/.claude/skills/pptx/SKILL.md` first if you need to extract slide content from the .pptx file.

### Mode 2: Quiz & Active Recall

**Trigger phrases**: "quiz me", "test me", "drill", "flashcards", "what comes after..."

This mode is **fully interactive**. Ask one question at a time, wait for the user's actual answer, then give feedback before moving to the next question. Use the AskUserQuestion tool for multiple-choice variants, or ask open-ended questions in conversation and evaluate the user's typed response.

**Question types** (cycle through these, weighted toward the user's weak areas):

**2a. Flow & Sequence**
- "What section comes after [X]?"
- "You just finished the RAG walkthrough. What's your next topic?"
- "Put these 4 sections in order: [shuffled list]"
- "You're on slide 20. What slide number and topic comes next?"

**2b. Stats & Details**
- "What percentage of organizations had no proper AI access controls?"
- "Name the two real-world incidents from the opening."
- "What are the four outcomes of the policy engine?"
- "How many stages are in the model governance lifecycle?"

**2c. Transitions**
- "How do you bridge from Layer 2 to Layer 3?"
- "What's your transition line after the mid-talk recap?"
- "You just finished the failure chain. What do you say to set up the scenarios?"

**2d. Audience Interactions**
- "What's your first audience poll question?"
- "After the 60-second kill switch poll, what point are you making?"
- "Describe the exercise on slide 10."

**2e. Timing**
- "What's your target elapsed time at the midpoint?"
- "Which section should you compress if you're running 5 minutes over at slide 25?"

**2f. Fill-in-the-Blank**
- Present a key sentence with blanks: "Prompts _____ behavior; platforms _____ behavior."
- "The penalty structure is tiered: for the most serious violations, fines can reach up to _____ euros or _____% of global annual turnover."

**2g. Memory Palace Recall**
- If the user has generated a memory palace (Mode 5), quiz them using it: "You walk into the kitchen. What concept lives there? What's the bizarre image?"
- "You're in the bathroom and you see something strange. What is it, and what does it remind you about the talk?"

**Adaptive difficulty**: Start with broad structural questions. As the user gets those right, drill into finer details. Track which question types they struggle with and weight future quizzes accordingly. After each quiz round (5-8 questions), give a brief summary: "You nailed flow and transitions but missed 2 out of 3 stats questions. Want to do a stats-focused round?"

### Mode 3: Interactive Rehearsal

**Trigger phrases**: "rehearsal", "let me practice", "I want to run through it", "practice delivering"

The user practices delivering sections of the talk. They type out what they'd say (or describe the key points they'd hit), and the skill gives **thorough, detailed** feedback.

**3a. Section Rehearsal**
- Pick a section (or let the user choose)
- Show the slide title and any visual cues from the slide
- The user types their delivery of that section
- Compare against the script **exhaustively** — go through the actual script line by line and provide feedback:
  - Key points covered vs. missed (be specific — list each missed point)
  - Specific details: names, dates, locations, specific examples mentioned in the script
  - Stats accuracy (did they get the numbers right? did they miss any stats?)
  - Examples and anecdotes: did they include the specific stories/incidents from the script?
  - Enterprise-scale examples: if the script escalates from simple to enterprise examples, did the user cover both levels?
  - Audience interactions: did they include the polls, exercises, pauses, and decision moments from that section?
  - Transition quality: did they set up the next section?
  - Stage directions and delivery cues they should remember
  - Approximate word count vs. target for timing
- **Be thorough**: The whole point is to catch everything the user missed so they can improve. Don't gloss over omissions. But always lead with what they got right — list the strengths first, then systematically note each gap.

**3b. Transition Drill**
- Present two adjacent slide titles
- User types how they'd bridge between them
- Compare with the scripted transition
- Note if the logical connection was preserved even if wording differs

**3c. Cold Open Practice**
- "You're walking on stage. The audience is settling. Go."
- User delivers the opening from memory
- Feedback on hook effectiveness, completeness, and tone
- **Important**: The opening typically spans multiple slides. Compare against ALL of the opening slides, not just slide 1. Check for the full opening sequence: hook, stories/incidents, the escalation to enterprise-scale examples, the audience poll, and the transition into the main content.

**3d. Recovery Drill**
- "You just blanked. You're somewhere in Layer 3. What are your anchor points to find your place?"
- Tests whether the user can recover from a lost position using structural knowledge
- This is one of the most valuable exercises — speakers fear blanking more than anything
- Can also use the memory palace: "Picture the room for Layer 3. What do you see? What does that remind you to talk about?"

**3e. Timing Rehearsal**
- User delivers a section while the skill tracks approximate word count
- Compare against the target pace (e.g., 140 wpm) and section time budget
- Flag if they're running long or short

### Mode 4: Dashboard & Progress

**Trigger phrases**: "dashboard", "progress", "how am I doing", "which talk needs work", "status"

Show the current state across all loaded talks:
- Which talks are loaded
- For each: sections practiced, quiz accuracy by category, areas flagged for review
- Recommendation for next practice session
- Days until the conference (if the user has mentioned a date)

### Mode 5: Visual Mnemonics & Memory Palace

**Trigger phrases**: "memory palace", "mnemonics", "visual memory", "help me remember", "weird images", "house method", "loci", "make it visual"

This mode generates powerful visual and spatial memory aids. The brain remembers bizarre, exaggerated, funny, or emotionally striking imagery far better than abstract concepts. This mode exploits that.

**5a. Memory Palace (Method of Loci)**

Map the talk's structure onto rooms in a familiar building (a house by default, but the user can choose any location they know well). Each room corresponds to a major section of the talk, and within each room, specific objects or scenes represent key concepts.

The approach:
1. Identify the talk's major sections (typically 6-10 for an hour-long talk)
2. Assign each section to a room in a house tour (front door → entryway → living room → kitchen → dining room → bathroom → bedroom → attic → backyard, etc.)
3. For each room, create 2-4 vivid, bizarre, funny, or striking mental images that encode the key concepts, stats, and transitions for that section
4. The images should be:
   - **Bizarre and exaggerated** — a 97-foot-tall bouncer blocking a door is more memorable than "97% had no controls"
   - **Interactive** — things should be doing something, not just sitting there
   - **Multi-sensory** — include sounds, smells, textures where possible
   - **Emotionally resonant** — funny, shocking, or absurd sticks better than neutral
   - **Connected to the actual content** — the image should trigger recall of the real material

**Example** (for an AI security talk):
- **Front Door**: A giant padlock (identity/access) with 97 tiny robots trying to sneak past it. Only 3 manage to show proper ID badges. The padlock is sweating.
- **Living Room**: A fish tank divided into sections by glass walls (context isolation/tenant boundaries). Fish on one side are wearing top hats (Customer A), fish on the other wear baseball caps (Customer B). One fish is pressing its face against the glass trying to read the other side's newspaper.
- **Kitchen**: A chef (the policy engine) with four burners: ALLOW (green flame), TRANSFORM (blue flame melting data into safe shapes), ESCALATE (yellow flame with a bell ringing), DENY (red flame shooting up). The chef is tasting every dish before it leaves.

Save the full memory palace as a markdown file with vivid descriptions of each room and its images. Include a "walking tour" version that reads as a narrative journey through the house.

**5b. Number-Image Associations**

For key statistics, create memorable image-number pairings:
- **97%** → 97 dalmatians (but they're all robots sneaking into a building with no security guard)
- **13%** → A baker's dozen of servers, each one on fire
- **33%** → A third of a pizza missing — "where did the audit trail go?"
- **60%** → A clock showing 60 seconds, but the off button is missing

The images should be funny or striking enough that the number sticks. Group related stats into mini-scenes.

**5c. Concept Cartoons**

Generate descriptions of single-panel cartoon concepts that capture key ideas:
- **Prompts guide; platforms enforce**: A polite sign saying "Please don't steal" next to a bank vault with a 10-ton door. Caption: "One is guidance. One is a guardrail."
- **Shadow AI**: A developer sneaking a model into production while wearing a fake mustache and trench coat. The model is literally casting a shadow shaped like a question mark.
- **Defense in depth**: A castle with six concentric walls. An attacker gets past wall 1 and cheers, then looks up and sees five more walls. Each wall is labeled with a blueprint layer.

These are descriptions the user reads and visualizes — they don't need to be actual generated images. The act of reading and mentally picturing the scene creates the memory.

**5d. Acronym & Mnemonic Phrases**

Create memorable acronyms or phrases for ordered lists in the talk:
- For the six layers: invent a mnemonic sentence where each word starts with the first letter of each layer
- For the four policy engine outcomes (Allow, Transform, Escalate, Deny): find a word or phrase
- For any other sequences the speaker needs to remember in order

Make these funny or personally relevant when possible. A mnemonic that makes the speaker laugh will stick better than a generic one.

**5e. Story Anchors**

For the specific real-world examples and incidents in the talk, create exaggerated mental images:
- **Chevy chatbot**: Picture a shiny new Tahoe with a $1 price tag, and a chatbot character doing a used-car-salesman impression, enthusiastically shaking hands with a customer while a lawyer in the background faints
- **DPD chatbot**: A delivery van with a chatbot face on the front, road-raging and yelling at customers while a "World's Worst" trophy materializes on its dashboard

The goal is to make each incident so visually vivid that the speaker can't forget it, and the image naturally triggers recall of the key details (what went wrong, which controls were missing).

When generating visual mnemonics:
- Save the full memory palace as `<talk-name>-memory-palace.md`
- Save number associations as `<talk-name>-number-images.md`
- Save concept cartoons as `<talk-name>-concept-cartoons.md`
- Include all of these in the study materials folder
- After generating, offer to quiz the user on the palace ("Walk me through the kitchen — what do you see?")

---

## Session Flow

A typical session might go:

1. User opens the skill → show dashboard
2. User picks a talk or accepts recommendation
3. Skill suggests a mode based on progress (or user picks)
4. Practice session runs (5-15 minutes typically)
5. Brief progress update at the end
6. Suggest what to do next time

Keep sessions focused and energizing. Don't try to cover everything at once. Better to do 10 minutes of focused quizzing on stats than 45 minutes of unfocused review.

---

## Important Principles

**Natural language matters more than exact wording.** When evaluating rehearsal, check for key concepts and logical flow, not word-for-word match. A speaker who can explain the concept in their own words owns the material better than one who recites it perfectly.

**But be thorough about what's missing.** The rehearsal feedback is most valuable when it catches everything the user omitted — specific names, dates, examples, audience interactions, enterprise-scale escalations, transitions. Go through the source script systematically when evaluating. Don't just check if the user hit the main theme — check if they covered the specific details, stories, stats, and interactions that make the section compelling.

**Build confidence, not anxiety.** Always lead with what the user got right. Frame gaps as "things to revisit" not "failures." The goal is to make them feel increasingly ready, not increasingly stressed.

**Respect the user's time.** These are busy speakers preparing for a real event. Keep interactions tight. Don't explain the methodology at length — just do it. If they want a 5-minute quiz, give them exactly that.

**Track weaknesses without nagging.** Note which areas need work in the progress data, surface them as suggestions, but don't force repetition if the user wants to move on.

**The script is the source of truth.** When checking answers, compare against the actual script content. Don't hallucinate additional facts or stats that aren't in the source material.

**Make it fun.** The memory palace and visual mnemonic techniques work because they're playful and surprising. Lean into humor and absurdity — a speaker who's laughing while studying will retain more than one who's grimly drilling flashcards.

---

## File Organization

For each loaded talk, maintain these files in the working directory:
```
<talk-name>-parsed.json          # Structured extraction from the script
<talk-name>-study/               # Generated study materials
  structure-map.md
  stats-drill.md
  timing-guide.md
  transitions.md
  audience-interactions.md
<talk-name>-memory-palace.md     # Memory palace walkthrough
<talk-name>-number-images.md     # Number-image associations
<talk-name>-concept-cartoons.md  # Concept cartoon descriptions
talk-dashboard.json              # Cross-talk progress tracking
```

When generating files, save them to the user's workspace folder so they can access them independently.

---

## Getting Started with a New Talk

When the user provides a script (.md) and deck (.pptx) for the first time:

1. Read the full script
2. Read the pptx (using the pptx skill if needed for slide content extraction)
3. Parse and extract the structured data (slide map, stats, transitions, etc.)
4. Save the parsed JSON
5. Update the dashboard
6. Give a brief overview: "Loaded [talk name] — [N] slides, ~[M] minutes. [Brief structural summary]. What would you like to start with?"

Then jump into whatever mode the user wants. Don't make them wait through a long setup process.
