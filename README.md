<p align="center">
  <img src="docs/logo.png" alt="Cartoon DNA double helix mascot" width="200">
</p>

# 23andAgent

Years ago I took a 23andMe DNA test, at that time not really aware of the privacy nightmare that handing a company your DNA could turn into. But since I already have the raw data anyway, I might as well use it with a modern AI assistant.

The 23andMe website itself is very much focused on ancestry (“where are my ancestors from?”). That is not what I care about here. I want to know more about interesting genes related to health and behavior. Questions like:

- Might any well-known health-related variants show up in my file?
- How does my body tend to handle caffeine, or some common medicines?
- Is there anything interesting (and honest) about sleep, taste, or the psychology/behavior markers people argue about online?

**23andAgent** is a private, educational playground for those questions. You drop in your 23andMe raw data file, then ask an AI in plain English. You do not need to know gene names.

It is **not** a medical test and **not** medical advice. 23andMe already labels the file as research/educational only. A consumer spit test only looks at a sampling of common spelling differences in DNA, misses most rare ones, and can be wrong on the rare calls. Fun to explore. Not a diagnosis.

Your full DNA file never leaves your computer, and it is never pasted into the AI chat. See [How privacy is preserved](#how-privacy-is-preserved).

## What this is, in one picture

1. You keep the big 23andMe text file on disk (hundreds of thousands of lines).
2. A small local program can answer “what letters do I have at this spot?” without opening the whole file in the chat.
3. You ask things like “does caffeine show up in my file?” The AI runs that program, then optionally looks up what public science sites say about those few spots — not about your entire genome.

## Setup

You need Python 3.10 or newer. No extra packages are required for the basic lookup.

```text
git clone <this-repo>
cd 23andAgent
```

1. In 23andMe, download **raw data** (Settings → 23andMe Data → Download Raw Data). You want the text file, not a PDF report.
2. Copy that file into the `raw_genome` folder. The name usually looks like `genome_YourName_v5_Full_YYYYMMDDHHMMSS.txt`.
3. Build a fast local index (this stays on your machine):

```text
python scripts/setup.py
```

Then open this folder in [Cursor](https://cursor.com/) (or another coding assistant that reads project instructions) and just… ask.

On Windows PowerShell, run commands as separate lines.

Do not commit the DNA file. The project is set up so git ignores it.

## What you can ask

You do not need the command line for day-to-day use. Try questions like:

- “Is there anything in my file about caffeine or how coffee affects sleep?”
- “Which well-known medicine-response markers are in the list, and what is actually known vs. guesswork?”
- “Run the personality/behavior list. What’s real science, and what’s internet folklore?”
- “Anything interesting about iron, blood clotting, or eye color?”
- “I keep reading about a gene that supposedly makes people thrill-seekers. Is that even in a 23andMe file?”

Ready-made topic lists (the project calls them *panels*) include personality and behavior, medicine response, heart and circulation, iron, nutrition, metabolism, athletic traits, sleep, taste/smell, and a few others. Ask “what topic lists exist?” if you want the menu.

A few honest limits, in plain language:

- Almost nothing about personality or everyday health is decided by one DNA spelling. Environment and thousands of other spots matter more.
- Internet articles often hype genes that **are not even measured** by 23andMe. The assistant should say so, rather than fake an answer from a nearby marker.
- Do not start, stop, or change a medicine because of a chat. If something looks serious, that is a conversation with a clinician and a real lab test — not this hobby project.

If you like typing commands yourself:

```text
python scripts/lookup.py search caffeine
python scripts/lookup.py panel personality
python scripts/lookup.py panels
python scripts/lookup.py stats
```

`search` finds topics by everyday words. `panel` runs a whole topic list. `stats` just says the index is built.

## Agent skills (the AI’s cheat sheets)

The interesting part of 23andAgent is not a database file. It is that the assistant already knows *how* to look things up without leaking your genome.

Those instructions come as **skills** — extra playbooks the AI reads:

| Skill | In plain English |
|-------|------------------|
| `personal-genome` | How to query *your* file locally, and how cautious to be when talking about traits |
| `database-lookup` | How to check public science/health websites about a specific DNA marker |
| `paper-lookup` | How to find the actual research papers |
| `gget` | Optional extra gene tools |

You do not have to learn those site names. Ask a normal question; the assistant picks the sources.

**For people cloning the repo:** the playbooks are already included (copied into `.agents/skills/` and `.cursor/skills/`). A lockfile, `skills-lock.json`, records exactly which versions. Skills are the heart of this project, so they live in git rather than “please install these later.”

To reinstall the third-party ones on another machine:

```text
npx skills add k-dense-ai/scientific-agent-skills@database-lookup
npx skills add k-dense-ai/scientific-agent-skills@paper-lookup
npx skills add k-dense-ai/scientific-agent-skills@gget
```

The `personal-genome` playbook is unique to 23andAgent. Keep it in this repository. More skills: [skills.sh](https://skills.sh/).

## How privacy is preserved

A 23andMe raw file is huge. If you (or the AI) opened it in the chat, that whole DNA dump would be sent to the AI company. 23andAgent is built so that **does not happen**.

The assistant is told **not** to open the raw file. It runs a small local script instead. The script looks up only the spots you asked about — “caffeine,” “this medicine,” “the personality list” — and returns a short answer. That short answer is all that may appear in the chat. When the assistant then checks public websites, it sends those marker *names* (like a catalogue number for one DNA spot), never your file.

Also:

- The DNA file and the local index are ignored by git, so they are not uploaded to GitHub.
- Do not paste long lists of your results into issues or other websites.
- Do not ask the AI to “open the genome file.” Ask about a topic, a trait, or a medicine.

This is a **habit the project enforces**, not a lock on the file. If you drop the raw file into the chat yourself, privacy is gone.

## What’s in the folder (if you care)

| Folder / file | What it’s for |
|---------------|----------------|
| `raw_genome/` | Your 23andMe download (not shared) |
| `data/genome.sqlite` | Fast local index built by setup (not shared) |
| `data/panels/markers.json` | The topic lists the assistant can search |
| `scripts/lookup.py` | The lookup program |
| `AGENTS.md` | Rules the AI is supposed to follow |

## Disclaimer

23andAgent was created with AI assistance. It cannot provide medical advice. Nothing here is a diagnosis, a prescription, or a reason to start, stop, or change a medication. If a result touches health or drugs, treat it as a curiosity and talk to a qualified clinician before doing anything. Personality and behavior are not decided by a handful of DNA letters; they do not determine who you are.
