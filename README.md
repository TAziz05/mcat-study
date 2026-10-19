# MCAT Study

A daily MCAT quiz. Every day it gives eight questions: two from each section of the exam (Chem/Phys, CARS, Bio/Biochem and Psych/Soc). One section a day, on rotation, gets its two questions from a passage, the way most of the real exam works.

- **Today**: eight questions, two per section. They stay the same all day on a given device.
- **Review**: missed questions come back 1, 3, 7 and 16 days later.
- **Practice**: unlimited questions for any section. Narrow by AAMC content category (like 4B · Fluids and gas exchange) or CARS skill, then by topic, and choose standalone questions, passages or both.
- **Stats**: streak, accuracy by section, and your weakest content categories with a one-tap practice button.
- **Sync devices**: progress lives in each browser. Copy the sync code to move it to another device.

Live at https://taziz05.github.io/mcat-study/

## Adding questions

Questions live in `data/src/*.json`. The file prefix sets the section: `cp_` (Chem/Phys), `cars_`, `bb_` (Bio/Biochem) or `ps_` (Psych/Soc). Each question is tagged with an AAMC content category (`1A`–`10A`, or `C1`–`C3` for the CARS skills).

A standalone question:

```json
{"c": "4B", "t": "Fluid flow", "q": "Question", "a": "Correct answer", "w": ["Wrong 1", "Wrong 2", "Wrong 3"], "e": "Explanation"}
```

CARS standalones add a short excerpt with `"x": "..."`. A passage is:

```json
{"title": "Title", "c": "5A", "t": "Buffers", "passage": "Text (blank line between paragraphs)",
 "tbl": [["Header", "Header"], ["Row", "Row"]], "cap": "Optional table caption",
 "qs": [ {"q": "...", "a": "...", "w": ["...", "...", "..."], "e": "..."} ]}
```

After editing, rebuild `questions.js` with:

```
python3 build/build.py
```

The build checks that every question has three distinct wrong answers and a valid category for its section. `build/patch.py` applies bulk edits to existing questions.

## About the questions

All questions and passages are original practice material written for this app. They follow the AAMC's published content outline but are not official AAMC questions. For real exam-style practice, use the AAMC's official materials too.

## Credits

Coded with [Claude](https://claude.ai) (Opus 5.5) by Anthropic. Questions and passages were written by Claude, organized around the AAMC MCAT content categories.
