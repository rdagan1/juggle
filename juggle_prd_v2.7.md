# Product Requirements Document: Juggle

**Version:** 2.7
**Date:** March 2026
**Author:** Roy
**Status:** Draft for Development

---

## Executive Summary

Juggle is an AI-powered study companion for Open University of Israel (OUI) students. It helps working students stay on top of deadlines, plan study time, and never miss what matters — through a single, conversational interface that feels personal.

**The primary interface is Gio.** When a student opens Juggle, they open a chat with Gio — not a dashboard. Gio is where everything happens: new emails surface here, deadlines are discussed here, study sessions are booked here. Secondary screens (timeline, grades, email log, settings) exist and are accessible via a tab navigator, but Gio proactively surfaces what the student needs before they need to go looking. The tab navigator is a shortcut, not the starting point.

**Gio feels like a real person, not a notification bot.** Even though most interactions are driven by templates and button flows, every message Gio sends is personalized with the student's name, their specific course and assignment, the current day and urgency level, their recent behavior, and their full academic context. The message "ממ"ן 3" always appears — never "an upcoming assignment." "רועי, רגע לפני שמתחיל שישי" appears differently than "בוקר טוב." Templating provides the structure; context provides the soul.

**Design Principles:**
1. **Gio-first:** The chat is the product. Everything else is a detail view.
2. **Zero Active Data Entry:** Information enters through settings, OUI emails, or Gio conversation — never forms.
3. **Button-First Interaction:** Bounded questions are answered with taps. Typed input is always available but never required.
4. **Personally Contextualized:** Every Gio message is rendered with the student's name, course names, deadline proximity, time of day, day of week, and behavioral history. Templates are the skeleton; personalization is the flesh.

**New in v2.4 vs v2.3:**
- **Gio chat as primary UI:** Replaces dashboard as the home screen. All notifications are Gio chat messages.
- **Tab navigator:** Gio | לוח זמנים | ציונים | מיילים | הגדרות — Gio is the default tab
- **Personalization engine:** Defines exactly which context variables are injected into each message template and how they affect phrasing, tone, and urgency
- **Notification → chat message architecture:** All system notifications (new PDF parsed, upcoming deadline, conflict detected) surface as Gio messages in the chat thread, not as push alerts or dashboard cards

**Target Users:** OUI students, with priority on those working full-time.

---

## Product Identity

### Name: Juggle

Captures the core challenge — simultaneously managing work, studies, and life. Active, relatable, works in both Hebrew (ג'אגל) and English.

**Brand Voice:**
- Empowering: "You've got this — I'm keeping track"
- Acknowledges the struggle: "I know you're juggling a lot right now"
- Celebrates progress: "Look at you, juggling like a pro!"

---

### Assistant Persona: Gio (ג'יו)

**Why "Gio"?**
Short, warm, easy to say in Hebrew and English. Gender-neutral. Feels like a person.

**Personality:**
- **Warm but efficient:** Never wastes words. Every message has a point.
- **Proactive:** Initiates contact. Doesn't wait to be summoned.
- **Reads the room:** More playful early in the semester, more focused when deadlines close in. Uses the student's name more when things get urgent — it signals this matters.
- **Honest:** Never invents, never summarizes what it hasn't read.
- **Has memory:** Remembers what the student said last week. References it.
- **Tap-friendly:** Offers choices as buttons; doesn't expect typing for simple answers.

**Voice ranges by urgency:**

| Context | Tone | Example |
|---|---|---|
| 2+ weeks to deadline | Warm, casual | "סתם בדקתי — ממ"ן 3 בעוד שבועיים. בכיף לתכנן מוקדם?" |
| 1 week to deadline | Friendly, nudging | "שבוע לממ"ן 3. לפי נתונים קודמים זה לוקח ~6 שעות — יש לך מספיק זמן?" |
| 3 days to deadline | Focused, action-oriented | "רועי, עוד 3 ימים לממ"ן 3. כדאי לסגור זמן לימוד היום." |
| Day before | Direct, caring | "מחר מגיש ממ"ן 3. הכל בסדר?" |
| Day of | Warm, supportive | "היום יום ההגשה 💪 בהצלחה, רועי!" |

---

## App Architecture — Gio-First

### The Tab Navigator

The app has five tabs. **Gio is the default and home tab.** The others are secondary views the student can reach at any time.

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│              [Main content area]                     │
│                                                      │
└──────────────────────────────────────────────────────┘
│  💬 ג'יו  │  📅 לוח זמנים  │  🎓 ציונים  │  📬 מיילים  │  ⚙️ הגדרות  │
└──────────────────────────────────────────────────────┘
```

| Tab | Content | Gio's role |
|---|---|---|
| **💬 ג'יו** | The chat. Gio messages, button responses, conversation. | Primary interface — everything surfaces here first |
| **📅 לוח זמנים** | Timeline of all upcoming deadlines, exams, lectures. Study blocks. | Gio links here when context helps ("הנה לוח הזמנים שלך →") |
| **🎓 ציונים** | Grades per course, per assignment, trend view. | Gio links here after grade notifications |
| **📬 מיילים** | Log of all parsed emails + attachments. Unreadable PDFs surfaced here. | Gio links here on new email events |
| **⚙️ הגדרות** | Preferences, virtual email address, Google Calendar, quiet hours, etc. | Gio links here during onboarding and when relevant |

### What Lives in Gio (Chat Tab)

Everything that requires a student's attention surfaces as a Gio message first:

- New PDF parsed → Gio message with summary + buttons
- Unreadable PDF → Gio message with attachment link + buttons
- Deadline approaching → Gio message with nudge + buttons
- Grade received → Gio message with grade + buttons
- Calendar conflict detected → Gio message with slot options + buttons
- Study block reminder → Gio message with confirmation + buttons
- Parse needs review → Gio message with confirmation + buttons

The student never needs to check a dashboard for new information. If Gio has something to say, it says it in the chat. The chat is also persistent — older messages scroll up, so the student can always review what Gio told them and what they replied.

### What Lives in Secondary Tabs

Secondary tabs are **detail views** — read-optimized, with a small set of direct actions. They are not the primary way to interact with the system, but they're essential for orientation and review.

**לוח זמנים (Timeline):**
- Chronological list of all upcoming obligations (30-day window + beyond)
- Each item: course name, type (ממ"ן / בחינה / הרצאה), date, status badge, effort estimate
- Tapping an item opens a detail card with Gio context ("הנה מה שאנחנו יודעים על זה")
- No forms. Actions (mark complete, schedule study time) open a Gio message thread for that item.

**ציונים (Grades):**
- Per-course breakdown: all assignments, exams, running average
- Trend indicator per course
- Tapping a grade shows the source (email parsed / manual entry)
- No manual entry UI — if student wants to add a grade, tap "דווח ל-Gio" which opens a pre-filled Gio message

**מיילים (Email Log):**
- List of all OUI emails received, sorted by date
- Each entry: subject, date, parse status (parsed / unreadable / partial), attachment count
- Tapping an email: shows parsed events extracted from it, or the unreadable notice + attachment link
- Unread badge for unprocessed/unreadable items

**הגדרות (Settings):**
- Virtual email address (displayed, copyable)
- Google Calendar connection (OAuth button)
- Quiet hours (time range picker)
- Shabbat blackout (toggle)
- Grade alert threshold (slider)
- Minimum study session length (slider)
- Preferred study windows (multi-select: ימי חול בוקר / ימי חול ערב / שישי / שבת)
- Effort contribution opt-out (toggle)
- Data deletion

---

## Personalization Engine

This section defines exactly how Gio messages are personalized. Every templated message has a set of **context slots** that are populated at render time. The result is a message that references the student's reality, not a generic academic scenario.

### Context Variables Available to All Messages

| Variable | Source | Example value |
|---|---|---|
| `{name}` | users.name | "רועי" |
| `{time_of_day}` | Current time | "בוקר" / "אחה"צ" / "ערב" |
| `{day_of_week}` | Current date | "יום ראשון" / "שישי" |
| `{course_name}` | courses.name | "חדו"א א׳" |
| `{assignment_title}` | deadlines.title | "ממ"ן 3" |
| `{days_until}` | Computed | 3 |
| `{due_day_name}` | Computed from due_date | "ביום שישי" / "מחרתיים" / "מחר" / "היום" |
| `{estimated_hours}` | effort_aggregates | 6.5 |
| `{estimate_sample}` | effort_aggregates | 18 |
| `{last_start_days_before}` | gio_memory | 5 (days before deadline user typically starts) |
| `{other_due_soon_count}` | Computed | 2 (other items due within 5 days) |
| `{grade_value}` | grades.grade | 87 |
| `{course_avg}` | Computed | 84 |
| `{study_block_time}` | study_blocks | "מחר 19:00" |
| `{conflict_event}` | Google Calendar | "פגישת צוות" |

### Personalization Rules

**1. Use the student's name at critical moments, not constantly.**

Gio uses `{name}` in:
- The first message of the day
- Day-of deadline reminders (urgency signal)
- Post-completion celebrations
- When contradicting the student ("רועי, שים לב — הפרטים לא תואמים.")

Gio does *not* use the name in:
- Routine check-ins mid-chain (would feel repetitive and hollow)
- Pure information messages (feels patronizing: "רועי, הבחינה ב-15 באפריל")

**2. Vary the opening based on time of day and day of week.**

| Time | Day | Opening variant |
|---|---|---|
| 07:00–10:00 | Weekday | "בוקר טוב!" / "יום טוב, {name}!" |
| 19:00–22:00 | Weekday | "ערב טוב!" / "אחרי עבודה —" |
| Morning | Friday | "בוקר טוב! לפני שמתחיל שישי —" |
| Afternoon | Friday | "כמעט סוף שבוע —" |
| Morning | Sunday | "שבוע חדש!" / "בוקר טוב, {name} —" |

**3. Reference behavioral history when it strengthens the nudge.**

If `gio_memory` contains evidence that the student tends to start late (e.g. `last_start_days_before: 2`), Gio can reference it once per assignment cycle — not repeatedly:

> "רועי, בפעם הקודמת התחלת ממ"ן 2 ימים לפני — השבוע יש לך 8 ימים. נצל את זה?"

This is done with warmth, not judgment. Used at most once per assignment, not every check-in.

**4. Reference workload context when relevant.**

If the student has multiple things due soon, Gio weaves it in naturally:

> "ממ"ן 3 בעוד 5 ימים — וגם בחינה בסוף השבוע. כדאי לתכנן היום."

The `{other_due_soon_count}` variable enables this. If 0, omit. If 1+, include.

**5. Tone shifts with urgency — automatically.**

Templates have multiple urgency variants. The backend selects based on `days_until`:

| `days_until` | Urgency level | Tone |
|---|---|---|
| ≥ 14 | low | Casual, optional framing |
| 7–13 | medium | Friendly, light push |
| 3–6 | high | Focused, action-oriented |
| 1–2 | urgent | Direct, caring |
| 0 | day-of | Warm, supportive |

**6. Celebrate specifics, not generics.**

When marking complete:
- ✅ "בואנה, סגרת ממ"ן 3! 🎉 כמה שעות לקח לך?"
- ❌ "המשימה הושלמה בהצלחה."

When a grade arrives:
- ✅ "קיבלת 87 על ממ"ן 2 בסטטיסטיקה — הממוצע שלך בקורס עלה ל-84."
- ❌ "ציון התקבל."

---

### Template Examples with Context Slots

The following show how the same underlying template renders differently based on context.

---

**Template: Proactive deadline nudge**

Base: `"{opening} {assignment_title} ב{course_name} {due_day_phrase}. {effort_line} {workload_line} {cta}"`

Rendered, 10 days out, Sunday morning, no other items due:
> "שבוע חדש! ממ"ן 3 בחדו"א בעוד 10 ימים. לפי 18 סטודנטים לוקח בממוצע 6.5 שעות — בכיף לתכנן מוקדם?"

Rendered, 3 days out, Wednesday evening, exam also due soon:
> "ערב טוב. רועי, עוד 3 ימים לממ"ן 3 — וגם בחינה בסוף השבוע. כדאי לסגור זמן לימוד הערב."

Rendered, 1 day out, student previously started late:
> "מחר מגיש ממ"ן 3. בפעם הקודמת התחלת מאוחר — היום זה הזמן לסיים."

---

**Template: Study block reminder (1 hour before)**

Rendered, Tuesday evening:
> "לימוד חדו"א בעוד שעה (19:00) 📚 מוכן?"

Rendered, Saturday morning:
> "שבת בוקר — לימוד חדו"א ב-10:00. בכיף שיש זמן שקט 😊"

---

**Template: Grade notification**

Grade above course average:
> "קיבלת 91 על ממ"ן 3 בחדו"א — גבוה מהממוצע שלך בקורס (84). יפה! 🎉"

Grade below threshold:
> "קיבלת 62 על ממ"ן 1 בסטטיסטיקה. מועד ב׳ עדיין פתוח אם תרצה לשפר."

---

**Template: Post-parse notification**

One event found, high confidence:
> "ממ"ן 3 בחדו"א מגיש ב-14 במרץ (עוד 12 ימים). הוספתי ללוח הזמנים."

Multiple events found:
> "יש לך 3 תאריכים חדשים בחדו"א: ממ"ן 3, ממ"ן 4, ובחינה. הכל ברשימה שלך עכשיו."

---

### What Makes It Feel Personal (Summary)

The goal is that a student who reads a Gio message thinks "זה מרגיש שהוא מכיר אותי" — not "זה בוט שיודע את שמי."

The levers that achieve this, in order of importance:

1. **Specific names:** Course name and assignment title, always. Never generic.
2. **Temporal awareness:** Time of day, day of week, days until. Always.
3. **Workload context:** Other obligations mentioned when they add urgency.
4. **Behavioral callbacks:** Past behavior referenced occasionally, warmly, not repeatedly.
5. **Student's first name:** Sparingly, at high-stakes moments.
6. **Tone calibration:** Urgency level changes the register, not just the words.

---

## Gio Interaction Design — Button-First Model

### Core Principle

When the answer to a Gio question has a bounded set of values, those values are tappable buttons. Typing is always accepted but never required.

### Button Anatomy

```
┌─────────────────────────────────────────────────────┐
│  [Gio message — personalized]                       │
│                                                     │
│  [כפתור א׳]  [כפתור ב׳]  [כפתור ג׳]               │
│                                                     │
│  ▾ משהו אחר...                                      │
│  └─ [text input, placeholder: "כתוב כאן..."]       │
└─────────────────────────────────────────────────────┘
```

- Buttons: rounded pills, RTL order, max 4 per row, overflow to second row
- "משהו אחר...": collapsed accordion, always present on prompted messages
- Tap = immediate submit, button set dismissed
- Typed input: always accepted, dismisses button set on submit

### Standard Button Sets

**Yes / No**
```
[כן]  [לא]
▾ משהו אחר...
```

**Yes / Not Now / Remind Me Tomorrow**
```
[כן]  [לא עכשיו]  [תזכיר לי מחר]
▾ משהו אחר...
```

**Snooze Duration**
```
[מחר בבוקר]  [בעוד 2 ימים]  [בעוד שבוע]  [עזוב את זה]
▾ משהו אחר...
```

**Completion Check**
```
[סיימתי ✓]  [עדיין לא]
▾ משהו אחר...
```

**Effort Hours — Assignments**
```
[פחות מ-2]  [2–4]  [4–6]  [6–8]  [יותר מ-8]
▾ משהו אחר...  (free text exact hours)
```

**Effort Hours — Exams**
```
[פחות מ-5]  [5–10]  [10–15]  [15–20]  [יותר מ-20]
▾ משהו אחר...  (free text exact hours)
```

**Study Session — Accept / Move**
```
[מושלם, קבע]  [הזז לשעה אחרת]  [הזז ליום אחר]  [לא צריך]
▾ משהו אחר...
```

**Study Slot Selection** (dynamically rendered from calendar)
```
[רביעי 19:00–21:00]  [חמישי 18:00–20:00]  [שבת 10:00–12:00]
▾ משהו אחר...
```

**Exam מועד Selection** (dynamically rendered from PDF)
```
[מועד א׳ — 15 באפריל, 09:00]
[מועד ב׳ — 12 ביוני, 09:00]
[מועד ג׳ — 20 ביולי, 09:00]
▾ משהו אחר...
```

**Parse Confirmation**
```
[נראה נכון ✓]  [יש שגיאה]
▾ משהו אחר...
```

**Course Selection** (dynamically rendered from user's enrolled courses)
```
[חדו"א א׳]  [אלגברה לינארית]  [סטטיסטיקה]
▾ משהו אחר...  (free text)
```

**Grade Acknowledgment**
```
[תודה 👍]  [רוצה לתכנן שיפור]
▾ משהו אחר...
```

**Unreadable PDF**
```
[פתח קובץ]  [הבנתי, תודה]
▾ משהו אחר...
```

**Lecture Reminder**
```
[כן, הוסף ליומן]  [לא, אצפה בהקלטה]  [כבר יש לי ביומן]
▾ משהו אחר...
```

### What Is Never Buttonified

- Corrections to parsed data ("מה לא נכון?")
- Informal updates not prompted by Gio
- Open Q&A and direct conversation
- When the student initiates unprompted

### Technical Notes

- Each Gio response object includes `buttons: []` array and `escape_hatch: true/false`
- Button schema: `{ text, value, style: "primary|secondary|destructive" }`
- Known button values → template handler (no LLM needed)
- "משהו אחר" typed text → NLU + LLM
- `escape_hatch: false` only for pure-information messages with no expected response
- `input_method` logged per message (`button` | `typed`) for analytics

---

## Core Features

---

### Feature 1: Virtual Email Address — PDF Ingestion Pipeline
**Priority:** P0

All OUI emails arrive with empty body and Hebrew PDF attachments. Each student gets a virtual address (`{name}.{random}@students.juggle.app`) set once in the OUI portal.

**Pipeline:**
1. Email received → immediately forwarded to personal inbox with original attachments
2. Each PDF queued for text extraction
3. SHA-256 hash of PDF bytes computed → checked against `pdf_parse_cache`
   - **Cache hit:** parsed JSON result reused instantly, zero LLM cost
   - **Cache miss:** proceed to step 4
4. Readability assessed (readable / unreadable)
5. Pre-filter: keyword scan for date/assignment/grade patterns (see below)
   - **No events likely:** log as `no_events`, skip LLM, no Gio message
   - **Events likely:** proceed to step 6
6. Readable → LLM parse → result stored in cache → events inserted → Gio chat message sent
7. Unreadable → Gio chat message with attachment + buttons. No summary, no inference.

**Readable PDF → Gio message (personalized):**
```
Gio: ממ"ן 3 בחדו"א מגיש ב-14 במרץ — עוד 12 ימים.
     לפי 18 סטודנטים לוקח בממוצע 6.5 שעות.

[כן, אמצא זמן ללמוד]  [לא עכשיו]  [תזכיר לי מחר]
▾ משהו אחר...
```

**Unreadable PDF → Gio message:**
```
Gio: קיבלת אימייל מהאו"פ עם קובץ מצורף.
     לא הצלחתי לקרוא אותו — הנה הקובץ.
     [📎 הודעה_קורס_20109.pdf]
     אם יש שם משהו חשוב — תגיד לי ואעדכן.

[פתח קובץ]  [הבנתי, תודה]
▾ משהו אחר...
```

**Confidence flagging:**
- High confidence → auto-insert, one-line Gio mention in context
- Medium/low confidence → Parse Confirmation buttons in Gio message

**Pre-filter: keyword scan before LLM (Optimization 2)**

Before invoking Claude Haiku on any readable PDF, a lightweight Python function scans the extracted text for signals that structured events are present. This costs nothing and eliminates LLM calls on administrative emails that contain no actionable data.

```python
EVENT_KEYWORDS = [
    'ממ"ן', 'ממ"מ', 'הגשה', 'תרגיל',           # assignment signals
    'בחינה', 'מועד', 'מבחן', 'בוחן',             # exam signals
    r'\d{1,2}[./]\d{1,2}[./]\d{2,4}',         # DD/MM/YYYY or DD.MM.YYYY
    r'\d{1,2} ב[א-ת]+',                          # "14 במרץ"
    'ציון', 'ציונים',                             # grade signals
]

def has_extractable_events(text: str) -> bool:
    for pattern in EVENT_KEYWORDS:
        if re.search(pattern, text):
            return True
    return False
```

- `False` → log PDF as `no_events`, skip LLM entirely, no Gio message sent
- `True` → proceed to LLM parse
- Estimated skip rate: ~25% of incoming OUI PDFs (administrative notices, general announcements)

**PDF content hash cache (Optimization 1)**

OUI frequently sends the same PDF to every student enrolled in a course. The cache prevents re-parsing identical documents across users.

```python
pdf_parse_cache (
  id: UUID PK,
  pdf_hash: String unique,      # SHA-256 of raw PDF bytes
  parse_result: JSON,           # structured event JSON returned by Claude
  parsed_at: DateTime,
  hit_count: Integer default 0, # for monitoring cache effectiveness
  created_at: DateTime
)
```

- Cache keyed on SHA-256 of raw PDF bytes (computed before text extraction)
- TTL: 90 days
- Cache hit: `hit_count++`, result used directly, LLM not invoked
- **Shared across all users** — one student's parse benefits every subsequent student who receives the same file
- Privacy: cache stores only structured JSON (dates, titles, course codes), never raw PDF text or student-identifying data

**Success Criteria:**
- 100% of emails forwarded within 60 seconds
- 100% of unreadable PDFs surfaced in Gio chat with attachment
- 80%+ of readable PDFs parsed correctly
- Cache hit rate ≥40% within 4 weeks of launch
- Pre-filter correctly skips ≥20% of PDFs with no LLM call

---

### Feature 2: Manual PDF Upload
**Priority:** P0

Drag-and-drop or file picker anywhere in the portal. No metadata required.

**Post-parse Gio message:**
```
Gio: יש לך עכשיו בחדו"א: 5 ממ"נים, 3 מועדי בחינה, 14 הרצאות.
     הכל ברשימה שלך.

[נראה נכון ✓]  [יש שגיאה]
▾ משהו אחר...
```

**Course not identified:**
```
Gio: לא הצלחתי לזהות לאיזה קורס זה שייך — יכול לעזור לי?

[חדו"א א׳]  [אלגברה לינארית]  [סטטיסטיקה]
▾ משהו אחר...
```

---

### Feature 3: Timeline Tab (לוח זמנים)
**Priority:** P0

The secondary view for all upcoming obligations. Read-optimized.

- All deadlines, exams, lectures in the next 30 days+
- Each item: course, type, date, status badge, effort estimate
- Urgent strip: items due within 72 hours
- Tapping an item: opens detail card with Gio summary of what's known
- Actions from detail card open a Gio conversation thread (e.g. "תכנן לימוד", "סמן כהושלם")
- No forms anywhere

Gio surfaces this view proactively in chat when helpful:
> "יש לך 3 דברים בשבוע הקרוב — רוצה לראות את לוח הזמנים?" `[הצג לוח זמנים →]` `[לא, תסכם בשבילי]`

---

### Feature 4: Exam Date Selection Flow
**Priority:** P0

PDF with multiple מועדים → Gio chat message with per-מועד buttons.

```
Gio: יש תאריכי בחינה לחדו"א — באיזה מועד אתה מתכוון לגשת?

[מועד א׳ — 15 באפריל, 09:00]
[מועד ב׳ — 12 ביוני, 09:00]
[מועד ג׳ — 20 ביולי, 09:00]
▾ משהו אחר...

User: [taps מועד א׳ — 15 באפריל, 09:00]

Gio: ✅ מועד א׳ — 15 באפריל נקבע ביומן.
     מועד ב׳ ו-ג׳ נשמרו כגיבוי — יופיעו ביומן כ"אופציונלי".
```

- Confirmed מועד → GCal standard event
- Other מועדים → GCal Tentative + "[אופציונלי]" prefix
- Never deleted from database
- Student can change via Gio: "שיניתי דעתי" → Gio re-renders מועד buttons

---

### Feature 5: Gio Proactive Study Engagement
**Priority:** P0

Gio initiates. All proactive messages are Gio chat messages — not push notifications, not dashboard cards.

**Assignment cadence (all rendered as personalized Gio chat messages):**

*10 days before — low urgency:*
```
Gio: שבוע חדש! ממ"ן 3 בחדו"א בעוד 10 ימים.
     לפי 18 סטודנטים לוקח בממוצע 6.5 שעות — בכיף לתכנן מוקדם?

[כן, בוא נתכנן]  [לא עכשיו]  [תזכיר לי בעוד 3 ימים]
▾ משהו אחר...
```

*7 days before — medium, if no study block yet:*
```
Gio: שבוע לממ"ן 3 בחדו"א. ביומן שלך יש מחר ב-19:00 — אקבע שעתיים?

[כן, קבע]  [הזז ליום אחר]  [לא צריך]
▾ משהו אחר...
```

*3 days before — high:*
```
Gio: רועי, עוד 3 ימים לממ"ן 3 — וגם בחינה בסוף השבוע.
     סיימת?

[סיימתי ✓]  [עדיין לא]
▾ משהו אחר...
```

*1 day before:*
```
Gio: מחר מגיש ממ"ן 3. הכל בסדר?

[כן, מוכן]  [צריך עוד זמן]
▾ משהו אחר...
```
If `[צריך עוד זמן]` → immediately shows study slot buttons.

*Day of:*
```
Gio: היום יום ההגשה של ממ"ן 3 💪 בהצלחה, רועי!
```
*(No buttons — purely supportive. No response expected.)*

---

**Exam cadence:**

*14 days before:*
```
Gio: בחינת חדו"א בעוד שבועיים.
     סטודנטים בדרך כלל מתחילים לחזור בסביבות עכשיו — נתכנן?

[כן, בוא נתכנן]  [תזכיר לי בעוד 4 ימים]  [לא צריך]
▾ משהו אחר...
```

*5 days before:*
```
Gio: עוד 5 ימים לבחינה. התחלת לחזור?

[כן, מתכונן]  [עדיין לא]
▾ משהו אחר...
```

---

**Lecture cadence — mode: `attend`** *(set during onboarding or per-course)*

*N minutes before lecture start (N = `lecture_reminder_before_minutes`, default 30):*
```
Gio: הרצאת חדו"א מתחילה בעוד 30 דקות (18:00) 👋

[הבנתי 👍]  [לא אגיע היום]
▾ משהו אחר...
```
If `[לא אגיע היום]` → Gio immediately asks:
```
Gio: רוצה שאתזמן לך זמן לצפות בהקלטה?

[כן, תזמן]  [לא, אסתדר לבד]
▾ משהו אחר...
```
If `[כן, תזמן]` → Gio shows study slot buttons for recording time.

---

**Lecture cadence — mode: `recording`** *(set during onboarding or per-course)*

*No reminder before the lecture. After lecture end time + `recording_reminder_delay`:*
```
Gio: הרצאת חדו"א הסתיימה — רוצה לתזמן זמן לצפות בהקלטה?

[כן, אמצא זמן]  [כבר צפיתי]  [לא צריך]
▾ משהו אחר...
```
If `[כן, אמצא זמן]` → Gio shows calendar slot buttons.

If `recording_schedule_prompt = false`: no message sent at all. Lecture tracked in Timeline only.

---

**Lecture cadence — mode: `per_course`** *(student chose "תלוי בקורס" in onboarding)*

First time a lecture is parsed for a new course, Gio asks:
```
Gio: יש לך הרצאות בחדו"א. בדרך כלל מגיע פיזית או צופה בהקלטות?

[מגיע להרצאות 🎓]  [צופה בהקלטות 📹]
▾ משהו אחר...
```
Answer stored in `gio_memory.course_lecture_modes[course_id]` and applies to all future lectures for that course.

---

**Anti-Creep Guardrails (enforced in Celery scheduler):**
- Max 1 proactive message per topic per day
- 3 consecutive snoozes → reduce frequency to every 2 days (but never stop if <5 days to deadline)
- Quiet hours: 23:00–07:00 — no messages sent
- Shabbat blackout: opt-in
- "עזוב אותי עם זה" → silence that topic 48 hours

**Snooze always follows with duration buttons:**
```
Gio: בסדר 😊 לכמה זמן?

[מחר בבוקר]  [בעוד 2 ימים]  [בעוד שבוע]  [עזוב לגמרי]
▾ משהו אחר...
```

---

### Feature 6: Crowdsourced Effort Estimates
**Priority:** P0

After marking complete, Gio asks in chat. One tap.

**Assignment completion:**
```
Gio: בואנה, סגרת ממ"ן 3! 🎉
     כמה שעות לקח לך בסך הכל? (עוזר לסטודנטים הבאים)

[פחות מ-2]  [2–4]  [4–6]  [6–8]  [יותר מ-8]
▾ משהו אחר...
```

**Exam completion:**
```
Gio: סיימת את הבחינה! בהצלחה 🍀
     כמה שעות חזרת לבחינה הזו בסך הכל?

[פחות מ-5]  [5–10]  [10–15]  [15–20]  [יותר מ-20]
▾ משהו אחר...
```

Data stored anonymously (no user_id). Minimum 5 data points before surfacing to others. Bucket taps stored as midpoint + `input_method: 'button_bucket'`.

---

### Feature 7: Gio Memory & Manual Record Updates
**Priority:** P1

Student tells Gio about changes not in email. Gio confirms before writing.

```
User: [typed] ההרצאה של אלגברה ביום שלישי נדחתה שבוע

Gio: אז הרצאת אלגברה עוברת מ-18 במרץ ל-25 במרץ?

[כן, עדכן]  [לא, תקן]
▾ משהו אחר...

User: [taps כן, עדכן]

Gio: ✅ עודכן ביומן Google.
```

If taps `[לא, תקן]` → free text "מה הפרטים הנכונים?" — one of the few typed-first flows.

Gio remembers preferences across sessions (`gio_memory` JSON):
- "אני לא הולך להרצאות" → switches to recording-availability reminders
- Course difficulty noted → calibrates encouragement tone

Full audit log in Settings / "שינויים ידניים" view.

---

### Feature 8: Work/Study Schedule Coordination
**Priority:** P1

Google Calendar OAuth (optional). Gio detects conflicts and offers slots in chat.

```
Gio: שמתי לב: ממ"ן 3 בעוד 4 ימים ואין זמן לימוד מתוכנן.
     הנה 3 חלונות פנויים:

[רביעי 19:00–21:30]  [חמישי 18:00–20:00]  [שבת 10:00–12:00]
▾ משהו אחר...

User: [taps רביעי 19:00–21:30]

Gio: ✅ נקבע "לימוד: חדו"א" רביעי 19:00–21:30.
     אזכיר שעה לפני 👍
```

OR-Tools CP-SAT solver generates top 3 slots using effort estimates to size sessions.

---

### Feature 9: Grade Tracking
**Priority:** P1

Grades parsed from PDFs. Surfaced in Gio chat immediately.

**Above average:**
```
Gio: קיבלת 91 על ממ"ן 3 בחדו"א — גבוה מהממוצע שלך בקורס (84). יפה! 🎉

[תודה 👍]  [רוצה לתכנן שיפור]
▾ משהו אחר...
```

**Below threshold (default <70):**
```
Gio: קיבלת 62 על ממ"ן 1 בסטטיסטיקה. מועד ב׳ עדיין פתוח.

[רוצה לתכנן חזרה]  [הבנתי, המשך]
▾ משהו אחר...
```

Full grade history in the ציונים tab. Tapping "מידע נוסף →" in a Gio message navigates to that tab.

---

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      USER LAYER                         │
│  - Gio Chat Tab (primary UI, all notifications here)    │
│  - Tab Navigator: ג'יו | לוח זמנים | ציונים | מיילים | הגדרות │
│  - Manual PDF Upload (drag-and-drop, any tab)           │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  APPLICATION LAYER                      │
│  - FastAPI Backend (Python 3.11+)                       │
│  - PDF Ingestion Pipeline                               │
│      ├── Text Extraction (PyMuPDF, Hebrew)              │
│      ├── Readability Assessment                         │
│      ├── LLM Parsing (Claude Haiku, readable only)      │
│      └── Unreadable PDF Handler (Gio message + attach)  │
│  - Gio Engine                                           │
│      ├── Personalization Renderer (context injection)   │
│      ├── Template Handler (button value → response)     │
│      ├── LLM Handler (typed / "משהו אחר" inputs)        │
│      └── Memory Manager (gio_memory R/W)                │
│  - Proactivity Scheduler (Celery Beat, 2hr cycle)       │
│      └── Urgency Classifier (selects tone variant)      │
│  - Conflict Detector (Google Calendar analysis)         │
│  - Study Scheduler (OR-Tools constraint solver)         │
│  - Effort Aggregator (nightly batch, Redis cache)       │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                  INTEGRATION LAYER                      │
│  - Inbound Email (Mailgun/Postmark)                     │
│  - Outbound Email (forwarding + notifications)          │
│  - Object Storage (S3-compatible, PDF storage)          │
│  - Google Calendar API (OAuth 2.0, read/write)          │
│  - Claude API (Haiku — PDF parsing, Gio LLM responses)  │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│                    DATA LAYER                           │
│  - PostgreSQL 15: users, courses, deadlines,            │
│    study_blocks, exam_sittings, parsed_emails,          │
│    uploaded_documents, grades, effort_records,          │
│    effort_aggregates, conversation_history,             │
│    reminder_state, manual_update_log                    │
│  - Redis 7 (session state, job queue, effort cache,     │
│              personalization context cache)             │
│  - S3-compatible object storage (PDF files)             │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Frontend | React (RTL), Tailwind CSS |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 |
| PDF Extraction | PyMuPDF (fitz), Hebrew encoding |
| Object Storage | Cloudflare R2 or AWS S3 |
| Email | Mailgun or Postmark |
| Scheduling | OR-Tools CP-SAT |
| LLM | Claude Haiku (`claude-3-5-haiku-20241022`) |
| Hosting | Railway or Fly.io |
| Auth | Google OAuth 2.0 / email+password |

---

## Gio Message API Schema

Every Gio message from the backend carries personalization context and optional buttons.

```json
{
  "id": "msg_abc123",
  "text": "רועי, עוד 3 ימים לממ\"ן 3 — וגם בחינה בסוף השבוע. כמה מתקדם?",
  "buttons": [
    { "text": "סיימתי ✓", "value": "completed", "style": "primary"   },
    { "text": "עדיין לא", "value": "pending",   "style": "secondary" }
  ],
  "escape_hatch": true,
  "navigate_hint": null,
  "context": {
    "template_id": "deadline_nudge_high",
    "urgency": "high",
    "deadline_id": "uuid-xxx",
    "days_until": 3
  }
}
```

**`navigate_hint`**: Optional. When Gio's message references a secondary tab, this carries the tab name and optional deep link:
```json
"navigate_hint": {
  "label": "הצג לוח זמנים →",
  "tab": "timeline",
  "filter": "upcoming_7_days"
}
```
This renders as a tappable text link below the button set, opening the relevant tab.

---

## Personalization Rendering — Implementation

The Personalization Renderer runs before every Gio outgoing message. It:

1. Receives `template_id` + `context_variables` from the calling service
2. Selects the correct urgency variant of the template
3. Injects all context variables
4. Applies opening variant based on `time_of_day` + `day_of_week`
5. Appends workload mention if `other_due_soon_count > 0`
6. Appends behavioral callback if `last_start_days_before` in `gio_memory` and this is first nudge for this assignment
7. Returns rendered text + buttons array

```python
def render_gio_message(template_id: str, ctx: dict) -> GioMessage:
    template = load_template(template_id)
    urgency = classify_urgency(ctx["days_until"])
    variant = template.variants[urgency]

    text = variant.format(
        name=ctx.get("name", ""),
        opening=get_opening(ctx["time_of_day"], ctx["day_of_week"]),
        course_name=ctx["course_name"],
        assignment_title=ctx["assignment_title"],
        due_day_phrase=get_due_day_phrase(ctx["days_until"]),
        estimated_hours=ctx.get("estimated_hours", ""),
        estimate_sample=ctx.get("estimate_sample", ""),
        workload_line=get_workload_line(ctx.get("other_due_soon_count", 0)),
        behavioral_callback=get_behavioral_callback(ctx),
    )
    buttons = template.buttons[urgency]
    return GioMessage(text=text, buttons=buttons, escape_hatch=True)
```

Templates live in a YAML file, version-controlled. Example:

```yaml
deadline_nudge:
  variants:
    low:
      text: "{opening} {assignment_title} ב{course_name} {due_day_phrase}. {effort_line} {cta_relaxed}"
    medium:
      text: "{opening} {assignment_title} ב{course_name} {due_day_phrase}. {effort_line} {workload_line} {cta_medium}"
    high:
      text: "{opening} {name}, עוד {days_until} ימים ל{assignment_title} ב{course_name}. {workload_line} {behavioral_callback} {cta_urgent}"
    urgent:
      text: "מחר מגיש {assignment_title}. {behavioral_callback_urgent} הכל בסדר?"
    day_of:
      text: "היום יום ההגשה של {assignment_title} 💪 בהצלחה{name_suffix}!"
  buttons:
    low:    [["כן, בוא נתכנן", "confirm_plan"], ["לא עכשיו", "dismiss"], ["תזכיר לי בעוד 3 ימים", "snooze_3d"]]
    medium: [["כן, קבע", "confirm_schedule"], ["הזז ליום אחר", "reschedule"], ["לא צריך", "dismiss"]]
    high:   [["סיימתי ✓", "completed"], ["עדיין לא", "pending"]]
    urgent: [["כן, מוכן", "ready"], ["צריך עוד זמן", "needs_time"]]
    day_of: []   # no buttons — purely supportive
```

---

## Data Model (Key Entities)

```python
users (
  id: UUID PK,
  email: String,
  virtual_email: String unique,
  name: String,
  timezone: String default 'Asia/Jerusalem',
  google_calendar_token: JSON encrypted nullable,    # personal/study GCal
  work_calendar_token: JSON encrypted nullable,      # separate OAuth token for work GCal if different account
  preferences: JSON,
    # Email:      forward_emails: bool (default true)
    # Lectures:   lecture_reminder_before_minutes: int (default 30)
    #             recording_reminder_delay: 'immediate'|'few_hours'|'next_day' (default 'few_hours')
    # Work:       work_days: List[str]  e.g. ['ראשון','שני','שלישי','רביעי','חמישי']
    #             work_hours: {start: 'HH:MM', end: 'HH:MM'} nullable
    # Reminders:  assignment_first_reminder_days: int (default 7)
    #             exam_first_reminder_days: int (default 14)
    # Other:      quiet_hours, shabbat_blackout, grade_threshold,
    #             min_study_session, preferred_study_windows,
    #             effort_contribution_opt_out
  gio_memory: JSON,
    # lecture_mode: 'attend'|'recording'|'per_course'
    # recording_schedule_prompt: bool
    # course_lecture_modes: {course_id: 'attend'|'recording'}  # when lecture_mode='per_course'
    # works: bool
    # last_start_days_before: int nullable  # behavioral learning
    # course_difficulty: {course_id: 'hard'|'ok'}
    # last_active_tab: str
  onboarding_completed: Boolean default False,
  onboarding_step: String nullable,    # tracks resume point if student left mid-onboarding
  created_at: DateTime
)

courses (
  id: UUID PK,
  user_id: UUID FK,
  code: String,
  name: String,
  semester: String,
  source: Enum('pdf_parsed', 'gio_conversation'),
  created_at: DateTime
)

deadlines (
  id: UUID PK,
  course_id: UUID FK,
  type: Enum('assignment','exam','lecture','announcement'),
  title: String,
  due_date: DateTime,
  status: Enum('pending','completed','missed'),
  needs_review: Boolean default False,
  source: Enum('pdf_parsed','gio_conversation'),
  source_pdf_id: UUID FK nullable,
  created_at: DateTime
)

exam_sittings (
  id: UUID PK,
  deadline_id: UUID FK,
  moed_label: String,
  sitting_date: DateTime,
  location: String nullable,
  status: Enum('confirmed','optional','cancelled'),
  gcal_event_id: String nullable,
  created_at: DateTime
)

parsed_emails (
  id: UUID PK,
  user_id: UUID FK,
  received_at: DateTime,
  subject: String,
  forwarded_at: DateTime nullable,
  attachment_count: Integer,
  parse_status: Enum('parsed','unreadable','partial','pending'),
  created_at: DateTime
)

pdf_attachments (
  id: UUID PK,
  email_id: UUID FK nullable,
  user_id: UUID FK,
  filename: String,
  storage_url: String,
  parse_status: Enum('readable','unreadable','pending'),
  parsed_at: DateTime nullable,
  document_type: String nullable,
  raw_text_length: Integer nullable,
  created_at: DateTime
)

uploaded_documents (
  id: UUID PK,
  user_id: UUID FK,
  filename: String,
  storage_url: String,
  parse_status: Enum('readable','unreadable','pending'),
  inferred_course_id: UUID FK nullable,
  course_match_confidence: Float nullable,
  parsed_at: DateTime nullable,
  created_at: DateTime
)

grades (
  id: UUID PK,
  user_id: UUID FK,
  course_id: UUID FK,
  assignment_id: UUID FK nullable,
  grade: Float,
  max_grade: Float default 100,
  grade_type: Enum('assignment','exam','final'),
  source: Enum('pdf_parsed','gio_conversation'),
  source_pdf_id: UUID FK nullable,
  received_at: DateTime
)

study_blocks (
  id: UUID PK,
  user_id: UUID FK,
  course_id: UUID FK nullable,
  gcal_event_id: String nullable,
  scheduled_start: DateTime,
  scheduled_end: DateTime,
  status: Enum('scheduled','completed','skipped','rescheduled'),
  created_at: DateTime
)

effort_records (
  id: UUID PK,
  course_code: String,
  assignment_label: String,
  semester: String,
  hours_spent: Float,
  input_method: Enum('button_bucket','typed'),
  record_type: Enum('assignment','exam'),
  recorded_at: DateTime
  # no user_id — anonymous
)

effort_aggregates (
  id: UUID PK,
  course_code: String,
  assignment_label: String,
  record_type: Enum('assignment','exam'),
  sample_count: Integer,
  mean_hours: Float,
  p25_hours: Float,
  p75_hours: Float,
  last_computed: DateTime
)

reminder_state (
  id: UUID PK,
  user_id: UUID FK,
  target_id: UUID,
  target_type: String,
  last_sent: DateTime,
  send_count: Integer,
  snooze_count: Integer,
  silenced_until: DateTime nullable
)

manual_update_log (
  id: UUID PK,
  user_id: UUID FK,
  target_type: String,
  target_id: UUID,
  field_changed: String,
  old_value: Text,
  new_value: Text,
  changed_at: DateTime
)

conversation_history (
  id: UUID PK,
  user_id: UUID FK,
  role: Enum('user','assistant'),
  content: Text,
  input_method: Enum('button','typed','unknown'),
  template_id: String nullable,       # which template generated this message
  timestamp: DateTime
)
```

---

## Onboarding Flow

### Design Principles
- Fully delivered as a Gio chat conversation — no separate onboarding screens
- Every question asked once, answered by button tap where possible
- Every step is skippable (student can always say "אחר כך" and complete it later)
- Target duration: under 6 minutes
- All collected preferences stored in `users.preferences` and `users.gio_memory`
- Courses are **not** entered here — inferred from the first PDF

### Authentication (pre-chat)

This is the only step that happens outside the Gio chat — a standard auth screen before the conversation begins.

```
┌─────────────────────────────────────────────────┐
│                  Juggle                         │
│           ג'אגל — עוזר הלימודים שלך             │
│                                                 │
│  [  המשך עם Google  ]                           │
│                                                 │
│           ─────── או ───────                    │
│                                                 │
│  אימייל: [________________]                     │
│  סיסמה:  [________________]                     │
│                                                 │
│  [  כניסה  ]    [  הרשמה  ]                     │
│                                                 │
│  (הרשמה שולחת קוד אימות לאימייל שלך)            │
└─────────────────────────────────────────────────┘
```

**Google OAuth:** Name and email auto-populated from Google account. Student proceeds directly to the Gio chat.

**Email/password registration:** Student enters email → receives a 6-digit verification code → enters code → sets password → proceeds to Gio chat. Name asked by Gio in the first message.

---

### Step 1 — Welcome & Name (email/password only)

*Skipped entirely for Google OAuth users — name already known.*

```
Gio: היי! 👋 אני ג'יו — העוזר האישי שלך מ-Juggle.
     אני כאן כדי לעזור לך לג'גל בין עבודה, לימודים וחיים.

     מה השם שלך?
```
*[Free text — one of the few typed-first steps in onboarding.]*

```
User: רועי

Gio: כיף להכיר, רועי! בוא נתחיל 🚀
```

---

### Step 2 — Virtual Email Address

```
Gio: הדבר הראשון — כתובת האימייל שלך באו"פ.

     📧 roy.cohen.x7k2@students.juggle.app
     [📋 העתק כתובת]

     איך להשתמש בה:
     1. היכנס לפורטל האו"פ
     2. עבור ל"פרטים אישיים"
     3. עדכן את "כתובת הדוא"ל ליצירת קשר" לכתובת הזו

     [📖 הצג הוראות מפורטות עם צילומי מסך →]

     ────────────────────────────────
     ☑ העבר עותק של כל אימייל לתיבת הדואר האישית שלי
     ────────────────────────────────

     ברגע שתעדכן — כל אימייל מהאו"פ יגיע ישר אליי,
     ואני אעבד אותו ואספר לך.

     עדכנת?

[כן, עדכנתי ✓]  [אעשה את זה אחר כך]
▾ משהו אחר...
```

**The forwarding checkbox:**
- Default: ticked (on)
- Unchecking it stores `preferences.forward_emails = false`
- Student can change this at any time in הגדרות
- If ticked: all OUI emails forwarded to the auth email address within 60 seconds, unchanged, with original attachments
- If unticked: emails processed and parsed by Juggle only — not forwarded to personal inbox

**If "אעשה את זה אחר כך":**
```
Gio: בסדר — הכתובת שמורה בפרופיל שלך בכל עת.
     [הגדרות → כתובת אימייל וירטואלית]
     נמשיך?

[כן, נמשיך]
```

---

### Step 3 — Lecture Attendance Style

```
Gio: שאלה קצרה על הרצאות.
     אתה בדרך כלל מגיע פיזית להרצאות, או צופה בהקלטות?

[מגיע להרצאות 🎓]  [צופה בהקלטות 📹]  [תלוי בקורס]
▾ משהו אחר...
```

**If `[מגיע להרצאות 🎓]`:**
```
Gio: מעולה! אזכיר לך לפני שהרצאה מתחילה.
     כמה זמן לפני שנתחיל להזכיר לך?

[15 דקות לפני]  [30 דקות לפני]  [שעה לפני]
▾ משהו אחר...
```
→ Stores: `gio_memory.lecture_mode = 'attend'`, `preferences.lecture_reminder_before_minutes = 15|30|60`

Reminder behavior: Gio sends a reminder N minutes before the lecture starts.

---

**If `[צופה בהקלטות 📹]`:**
```
Gio: הבנתי — לא אטריד אותך לפני ההרצאה.
     אחרי שההרצאה מסתיימת, רוצה שאשאל אם לתזמן צפייה בהקלטה?

[כן, תזמן לי צפייה]  [לא, אני מסתדר לבד]
▾ משהו אחר...
```

If `[כן, תזמן לי צפייה]`:
```
Gio: מצוין. כמה זמן אחרי שההרצאה מסתיימת לשלוח לך את ההצעה?

[מיד אחרי]  [כמה שעות אחרי]  [למחרת]
▾ משהו אחר...
```
→ Stores: `gio_memory.lecture_mode = 'recording'`, `gio_memory.recording_schedule_prompt = true`, `preferences.recording_reminder_delay = 'immediate'|'few_hours'|'next_day'`

Reminder behavior: Gio sends no reminder before the lecture. After the lecture end time, Gio messages: "הרצאת חדו"א הסתיימה — רוצה לתזמן זמן לצפות בהקלטה?" with study slot buttons.

If `[לא, אני מסתדר לבד]`:
→ Stores: `gio_memory.lecture_mode = 'recording'`, `gio_memory.recording_schedule_prompt = false`

Reminder behavior: Gio sends nothing for lectures at all — they are tracked in the timeline but not nudged.

---

**If `[תלוי בקורס]`:**
```
Gio: מובן! כשיתווסף קורס חדש, אשאל אותך לגבי ההרצאות שלו.
```
→ Stores: `gio_memory.lecture_mode = 'per_course'`

Per-course lecture mode is resolved the first time Gio parses a lecture schedule for a new course — Gio asks the same attend/record question then, in context.

---

### Step 4 — Work Schedule

```
Gio: אתה עובד בזמן הלימודים?

[כן, עובד]  [לא, רק לומד]
▾ משהו אחר...
```

**If `[לא, רק לומד]`:**
→ Stores: `gio_memory.works = false`. Gio skips the rest of Step 4.

---

**If `[כן, עובד]`:**
```
Gio: מתי אתה בדרך כלל עובד?
     (בחר את כל הימים שרלוונטיים)

[ראשון]  [שני]  [שלישי]  [רביעי]  [חמישי]  [שישי]
▾ משהו אחר...
```
*Multi-select: student can tap multiple days. Tapped days become filled/selected.*

```
[after day selection]

Gio: ובאילו שעות בדרך כלל?

[08:00–16:00]  [09:00–17:00]  [09:00–18:00]  [10:00–18:00]
▾ משהו אחר...  (e.g. "10:00–15:00 ביום שני, 09:00–17:00 בשאר הימים")
```
→ Stores: `preferences.work_days = [...]`, `preferences.work_hours = {start, end}`

```
Gio: רוצה לחבר את יומן העבודה שלך?
     זה מאפשר לי לראות מתי אתה פנוי באמת — ולהציע זמני לימוד שמתאימים.

[חבר Google Calendar]  [אחר כך]  [לא, אזין ידנית]
▾ משהו אחר...
```

**If `[חבר Google Calendar]`** → OAuth flow opens, returns to chat.
```
Gio: ✅ מחובר! אני אלקח בחשבון את הפגישות שלך כשאציע זמני לימוד.
```
→ Stores: `google_calendar_token`, `gio_memory.works = true`

**If `[אחר כך]` or `[לא, אזין ידנית]`:**
```
Gio: בסדר — אשתמש בשעות שציינת כנקודת התחלה.
     אפשר לחבר יומן בכל עת מההגדרות.
```
→ Stores: `gio_memory.works = true`, uses manual `work_days` + `work_hours`

---

### Step 5 — Notification Preferences

```
Gio: שאלה אחרונה — כמה מוקדם לפני הגשת עבודה תרצה שאתחיל להזכיר לך?
     (זו התזכורת הראשונה — אחרי זה אשלח עדכונים לפי ההתקדמות שלך)

[שבועיים לפני]  [שבוע לפני]  [5 ימים לפני]  [3 ימים לפני]
▾ משהו אחר...
```
→ Stores: `preferences.assignment_first_reminder_days = 14|7|5|3`

```
Gio: ולגבי בחינות — כמה מוקדם לפני בחינה?

[3 שבועות לפני]  [שבועיים לפני]  [שבוע לפני]
▾ משהו אחר...
```
→ Stores: `preferences.exam_first_reminder_days = 21|14|7`

---

### Step 6 — Done & First Action

```
Gio: מושלם, רועי — מוכן! 🚀

     ברגע שיגיע אימייל מהאו"פ, אני אעבד אותו ואספר לך.
     אם יש לך סילבוס של קורס — תוכל להעלות אותו עכשיו ואני אחלץ את כל התאריכים.

[העלה סילבוס עכשיו]  [אחר כך]
▾ משהו אחר...
```

If `[העלה סילבוס עכשיו]` → file picker opens, upload flow begins (Feature 2).
If `[אחר כך]` → Gio chat ready for regular use.

---

### Onboarding Data Collected (Summary)

| Preference | Where stored | Default if skipped |
|---|---|---|
| Name | `users.name` | Required (Google auto-fill or typed) |
| Forward emails | `preferences.forward_emails` | `true` |
| Lecture mode | `gio_memory.lecture_mode` | `'attend'` |
| Lecture reminder lead time | `preferences.lecture_reminder_before_minutes` | `30` |
| Recording prompt after lecture | `gio_memory.recording_schedule_prompt` | `false` |
| Recording reminder delay | `preferences.recording_reminder_delay` | `'few_hours'` |
| Works | `gio_memory.works` | `false` |
| Work days | `preferences.work_days` | `[]` |
| Work hours | `preferences.work_hours` | `null` |
| Google Calendar | `google_calendar_token` | `null` |
| Assignment first reminder | `preferences.assignment_first_reminder_days` | `7` |
| Exam first reminder | `preferences.exam_first_reminder_days` | `14` |

All of these are editable at any time via הגדרות or by telling Gio conversationally.

---

### Post-Onboarding: Lecture Mode Applied

The lecture mode preference set during onboarding directly drives the proactivity scheduler:

**`lecture_mode = 'attend'`:**
- N minutes before lecture start (N = `lecture_reminder_before_minutes`): Gio sends reminder with "הבנתי 👍" / "לא אגיע היום" buttons
- If "לא אגיע היום" → Gio asks: "רוצה שאתזמן לך צפייה בהקלטה?" with slot buttons

**`lecture_mode = 'recording'` + `recording_schedule_prompt = true`:**
- No reminder before lecture
- After lecture end time + delay (`recording_reminder_delay`): Gio sends "הרצאת {course} הסתיימה — רוצה לתזמן זמן לצפייה בהקלטה?" with study slot buttons

**`lecture_mode = 'recording'` + `recording_schedule_prompt = false`:**
- No reminders for lectures at all
- Lecture still tracked in Timeline tab

**`lecture_mode = 'per_course'`:**
- First time a lecture-containing PDF is parsed for a new course → Gio asks attend/record question for that specific course
- Stored per-course in `gio_memory.course_lecture_modes: {course_id: 'attend'|'recording'}`

---

## Complete User Flows

### Flow 1: Email Arrives with Readable PDF
```
[Gio chat — new message]

Gio: ממ"ן 3 בחדו"א מגיש ב-14 במרץ — עוד 12 ימים.
     לפי 18 סטודנטים לוקח בממוצע 6.5 שעות.

[כן, אמצא זמן ללמוד]  [לא עכשיו]  [תזכיר לי מחר]
▾ משהו אחר...

User: [taps כן, אמצא זמן ללמוד]

Gio: הנה 3 חלונות פנויים:

[רביעי 19:00–21:30]  [חמישי 18:00–20:00]  [שבת 10:00–12:00]
▾ משהו אחר...

User: [taps רביעי 19:00–21:30]

Gio: ✅ נקבע "לימוד: חדו"א" רביעי 19:00–21:30.
     אזכיר שעה לפני 👍
```

---

### Flow 2: Email Arrives with Unreadable PDF
```
[Gio chat — new message]

Gio: קיבלת אימייל מהאו"פ עם קובץ מצורף.
     לא הצלחתי לקרוא אותו — הנה הקובץ:
     [📎 הודעה_קורס_20109.pdf]
     אם יש שם משהו חשוב — תגיד לי ואעדכן.

[פתח קובץ]  [הבנתי, תודה]
▾ משהו אחר...

User: [reads PDF, comes back to chat]
User: [typed] כתוב שם שממ"ן 4 נדחה ל-28 במרץ

Gio: אז ממ"ן 4 בחדו"א עכשיו עד 28 במרץ?

[כן, עדכן]  [לא, תקן]
▾ משהו אחר...

User: [taps כן, עדכן]

Gio: ✅ עודכן.
```

---

### Flow 3: Manual PDF Upload
```
[Student drops PDF on the Gio chat or anywhere in the app — no mention of PDF in Gio reply]

Gio: יש לך עכשיו בחדו"א: 5 ממ"נים, 3 מועדי בחינה, 14 הרצאות.

[נראה נכון ✓]  [יש שגיאה]
▾ משהו אחר...

User: [taps נראה נכון ✓]

Gio: ✅ הכל ברשימה. רוצה לראות? [הצג לוח זמנים →]
```

---

### Flow 4: Exam Date Selection
```
[Gio chat — new message]

Gio: יש תאריכי בחינה לחדו"א — באיזה מועד אתה מתכוון לגשת?

[מועד א׳ — 15 באפריל, 09:00]
[מועד ב׳ — 12 ביוני, 09:00]
[מועד ג׳ — 20 ביולי, 09:00]
▾ משהו אחר...

User: [taps מועד א׳ — 15 באפריל, 09:00]

Gio: ✅ מועד א׳ — 15 באפריל נקבע ביומן.
     מועד ב׳ ו-ג׳ נשמרו כגיבוי.
```

---

### Flow 5: Informal Update
```
User: [typed] ביטלו את ממ"ן 4 בחדו"א

Gio: אז ממ"ן 4 בחדו"א בוטל לחלוטין?

[כן, מחק אותו]  [לא, רק נדחה]
▾ משהו אחר...

User: [taps כן, מחק אותו]

Gio: ✅ הסרתי ממ"ן 4 מהרשימה.
```

---

### Flow 6: Grade Notification
```
[Gio chat — new message]

Gio: קיבלת 87 על ממ"ן 2 בסטטיסטיקה 🎉
     הממוצע שלך בקורס עלה ל-84.
     [הצג ציונים →]

[תודה 👍]  [רוצה לתכנן שיפור]
▾ משהו אחר...
```

---

### Flow 7: Completion Check-In
```
[Gio chat — proactive message, 3 days before]

Gio: רועי, עוד 3 ימים לממ"ן 3 — וגם בחינה בסוף השבוע.
     סיימת?

[סיימתי ✓]  [עדיין לא]
▾ משהו אחר...

User: [taps סיימתי ✓]

Gio: בואנה, סגרת ממ"ן 3! 🎉
     כמה שעות לקח לך?

[פחות מ-2]  [2–4]  [4–6]  [6–8]  [יותר מ-8]
▾ משהו אחר...

User: [taps 4–6]

Gio: תודה 🙏 עוזר לסטודנטים הבאים לתכנן.
```

---

### Flow 8: Study Slot Selection
```
[Gio chat — proactive message, no study block booked]

Gio: שבוע לממ"ן 3 בחדו"א ואין זמן לימוד ביומן.
     הנה 3 חלונות פנויים:

[רביעי 19:00–21:30]  [חמישי 18:00–20:00]  [שבת 10:00–12:00]
▾ משהו אחר...

User: [taps רביעי 19:00–21:30]

Gio: ✅ נקבע "לימוד: חדו"א" רביעי 19:00–21:30.
```

---

### Flow 9: Snooze Flow
```
Gio: עוד 5 ימים לממ"ן 3. הכל בסדר?

[כן, מוכן]  [צריך עוד זמן]  [לא עכשיו]
▾ משהו אחר...

User: [taps לא עכשיו]

Gio: בסדר 😊 לכמה זמן?

[מחר בבוקר]  [בעוד 2 ימים]  [בעוד שבוע]  [עזוב לגמרי]
▾ משהו אחר...

User: [taps מחר בבוקר]

Gio: 👍 אחזור מחר בבוקר.
```

---

## LLM Integration Strategy

### Hybrid Template + LLM + Personalization Renderer

**The four tiers:**

1. **Template handler** (button taps with known `value`): No LLM. Immediate response. Covers ~75% of interactions.
2. **Personalization renderer**: Runs before every outgoing message. Pure string interpolation — no LLM. Adds name, course, urgency variant, workload context.
3. **Batched reminder generator** (proactive nudges requiring LLM): Single daily Celery job at 06:00 — one LLM call generates all that day's LLM-required nudges in one shot.
4. **Real-time LLM handler** (typed input, "משהו אחר", open Q&A, urgent alerts): Claude Haiku, ~25% of interactions.

The personalization renderer adds zero LLM cost — it's template interpolation with structured context data.

---

### Optimization 4: Batched Reminder Generation

Most proactive reminders are fully templated (no LLM needed). The minority that do require LLM — reminders involving behavioral callbacks, multi-deadline context, or edge cases outside the template set — previously would each make a separate real-time API call. Instead, a single Celery Beat job at **06:00 daily** collects all users needing an LLM-generated nudge and resolves them in one batched request.

```python
async def generate_daily_llm_reminders():
    users = get_users_needing_llm_nudge_today()  # typically 20-30% of active users
    if not users:
        return

    lines = []
    for u in users:
        lines.append(json.dumps({
            'user_id': u.id,
            'name': u.name,
            'assignment': u.next_deadline_title,
            'course': u.course_name,
            'days_until': u.days_until,
            'last_start_days_before': u.gio_memory.get('last_start_days_before'),
            'other_due_count': u.other_due_soon_count,
        }, ensure_ascii=False))

    prompt = (
        "Generate short, warm Hebrew nudges for each student below.\n"
        "One line per student. Format: user_id|reminder_text\n"
        "Max 120 characters each. Encouraging tone, reference their specific assignment.\n\n"
        + "\n".join(lines)
    )

    response = claude.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=len(users) * 60,
        messages=[{"role": "user", "content": prompt}]
    )

    for user_id, text in parse_batch_response(response):
        schedule_gio_message(user_id, text, buttons=get_reminder_buttons(user_id))
```

**What gets batched vs. stays real-time:**

| Message type | Delivery | Reason |
|---|---|---|
| Proactive deadline nudges (templated) | Celery Beat, no LLM | Pure template render |
| Proactive nudges needing LLM | 06:00 daily batch | One call covers all users |
| Study block reminders (1h before) | Celery Beat, no LLM | Time-triggered template |
| Post-parse notifications | Real-time | Triggered by email arrival |
| Urgent reminders (<6h to deadline) | Real-time | Time-sensitivity overrides batching |
| Conversational replies | Real-time | User is waiting |

**Cost saving:** Without batching, each LLM-required nudge carries ~150 tokens of per-call overhead (API handshake, system prompt fragment). With batching that overhead is paid once regardless of N. At 100 users with ~30% needing LLM nudges daily, this reduces per-reminder overhead by ~70%.

---

**Revised Cost Estimate (100 users/month) — with Optimizations 1, 2, 4:**

| Category | Baseline | Optimized | Saving |
|---|---|---|---|
| PDF parsing | ~$3.36 | ~$1.80 | ~46% |
| Conversational LLM | ~$0.80 | ~$0.80 | — |
| Reminder generation | ~$0.50 | ~$0.20 | ~60% |
| Other LLM operations | ~$0.50 | ~$0.50 | — |
| Buffer | ~$1.50 | ~$1.00 | — |
| **Total** | **~$6.66** | **~$4.30** | **~35%** |

**PDF saving breakdown:**
- Cache hits (same PDF across cohort): ~40% hit rate → ~$1.34 saved
- Pre-filter skipping no-event PDFs: ~25% skip rate → ~$0.22 saved
- Combined PDF saving: ~$1.56/month

---

## Non-Functional Requirements

**Performance:**
- Email forwarding: <60 seconds
- PDF parse: <30 seconds
- Gio response (template/button): <500ms
- Gio response (LLM): <3 seconds
- Tab switch: <200ms
- Timeline load: <1 second

**Reliability:**
- 95% uptime
- Zero email loss — forward even if parse fails
- Zero silent parse failures — every unreadable PDF surfaces in Gio chat
- Daily PostgreSQL backups

**Security & Privacy:**
- GCal tokens encrypted at rest (AES-256)
- PDF text discarded after parsing
- Effort records: no user_id
- Grade data strictly private
- GDPR: full deletion via Settings

**Localization:**
- Hebrew RTL throughout — chat bubbles, buttons, tab labels, secondary screens
- PyMuPDF Hebrew text direction
- Timezone: Asia/Jerusalem default
- Date: DD/MM/YYYY
- Shabbat blackout: opt-in

**Accessibility:**
- Min 44×44px tap targets
- `aria-label` in Hebrew on all buttons
- Keyboard navigable chat interface
- Screen reader support for chat thread

---

## Out of Scope (MVP)

- OCR for scanned PDFs (v2.5)
- Push notifications to mobile (web chat is the notification surface for now)
- Native mobile app (mobile-responsive web)
- Study partner matching
- Weighted GPA
- Exam preparation resources
- Multi-calendar merging

---

## Development Roadmap

### Week 1: Foundation + PDF Pipeline + Gio Chat Shell
- User registration, login, virtual email
- Email inbound routing + forwarding
- PDF extraction (PyMuPDF, Hebrew, readability)
- Unreadable PDF handler → Gio chat message with buttons
- **Gio chat UI shell:** Tab navigator, chat thread component, button renderer, "משהו אחר" accordion
- PostgreSQL schema

**Goal:** Email arrives → unreadable or readable Gio chat message appears. Chat UI renders buttons. Tab navigator navigates.

---

### Week 2: LLM Parsing + Personalization Renderer + Timeline Tab
- Claude Haiku PDF parsing: all event types
- **Personalization renderer:** Context variable injection, urgency variant selection, opening variants, workload lines
- Dashboard populated from Gio messages (no forms)
- Exam date selection buttons in chat
- Parse confirmation buttons
- Manual PDF upload → Gio chat response
- Timeline tab (read-only, linked from Gio)

**Goal:** Upload real OUI syllabus → Gio chat message with personalized summary → tap confirm → Timeline tab shows events.

---

### Week 3: Proactivity + All Button Flows + Secondary Tabs
- Full proactivity scheduler with personalized templates + urgency variants
- All button flows: completion check, snooze, study slots, grade acknowledgment, manual update confirm
- Behavioral callback injection into templates
- Grades tab populated from parsed data
- Email log tab
- Gio → tab navigation links ("הצג לוח זמנים →")

**Goal:** Gio proactively nudges with a personalized message. Student responds in 1–2 taps. Grade received → Gio message → ציונים tab shows it.

---

### Week 4: Effort Estimates + Scheduling + Polish
- Effort collection button flows
- Nightly aggregation + Redis cache
- Google Calendar OAuth + conflict detection + study slot buttons
- OR-Tools scheduler feeding slot options into Gio messages
- Behavioral memory: `last_start_days_before` tracking, callback injection
- "משהו אחר" analytics (button tap rate vs typed rate per template)
- Hebrew UI polish, accessibility, edge cases

**Goal:** Full loop — PDF arrives → Gio nudges with personalized messages + buttons → student taps through → study booked → completion + effort recorded.

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Scanned/unreadable PDFs >50% | High | High | Unreadable protocol handles gracefully; OCR evaluation Week 1 |
| Personalization feels hollow despite context injection | Medium | Medium | A/B test templates with/without behavioral callbacks during beta; track "מרגיש אישי" in feedback survey |
| Gio chat becomes cluttered with too many proactive messages | Medium | Medium | Anti-creep guardrails; snooze is one tap; consider "תראה רק התראות חשובות" mode |
| Tab navigator neglected — students don't discover secondary screens | Low | Low | Gio links to tabs proactively; tabs are discovery, not core flow |
| OUI PDF format varies | Medium | High | LLM is format-agnostic; test on 20+ real PDFs before launch |
| Grade parsing error | Medium | High | Default grade parses to medium-confidence; always show confirmation buttons in chat |
| "משהו אחר" overused (>15%) on specific flows | Medium | Medium | Track rate per template_id; expand button sets accordingly |
| Solo founder burnout | Medium | High | Ship chat shell + unreadable PDF handler in Week 1 — those two are the foundation of everything |

---

## Open Questions

### Before Development Starts
1. **Email provider:** Mailgun vs Postmark — Hebrew MIME, attachment webhooks
2. **Object storage:** Cloudflare R2 vs AWS S3
3. **PDF library:** Benchmark PyMuPDF vs pdfplumber on real OUI PDFs
4. **Scanned PDF rate:** Test before launch. If >30%, pull OCR into MVP.

### During Development
5. **Personalization A/B test:** During beta, randomly assign 20% of users to non-personalized templates (no name, no behavioral callbacks, no workload context). Measure engagement rate difference.
6. **"משהו אחר" monitoring:** Build analytics from day 1 — rate per `template_id`. Critical signal.
7. **Chat history depth:** How far back should the Gio chat thread scroll? Leaning: all history, paginated, since it's the audit trail for the student.
8. **Tab badge counts:** Should tabs show unread badges (e.g., ציונים tab with "2" if two new grades)? Leaning: yes — drives tab discovery.

### Post-MVP
9. **OCR (v2.5):** PaddleOCR for scanned PDFs — highest-impact single feature.
10. **Push notifications:** Currently, Gio chat is the notification surface. Post-MVP: evaluate web push or mobile app for when the student isn't in the portal.
11. **Weighted GPA:** Requires weight extraction from syllabus PDFs.
12. **Monetization:** Free through beta; paid tier after 500 users.

---

## Appendix: Button Vocabulary Reference

| Flow | Buttons | Escape Hatch |
|---|---|---|
| Yes/No | `[כן]` `[לא]` | ✓ |
| Proactive nudge | `[כן, בוא נתכנן]` `[לא עכשיו]` `[תזכיר לי מחר]` | ✓ |
| Study slot selection | Dynamic calendar slots × 3 | ✓ |
| Snooze duration | `[מחר בבוקר]` `[בעוד 2 ימים]` `[בעוד שבוע]` `[עזוב לגמרי]` | ✓ |
| Completion check | `[סיימתי ✓]` `[עדיין לא]` | ✓ |
| Effort — assignment | `[פחות מ-2]` `[2–4]` `[4–6]` `[6–8]` `[יותר מ-8]` | ✓ |
| Effort — exam | `[פחות מ-5]` `[5–10]` `[10–15]` `[15–20]` `[יותר מ-20]` | ✓ |
| Exam מועד | Dynamic per PDF × N מועדים | ✓ |
| Parse confirmation | `[נראה נכון ✓]` `[יש שגיאה]` | ✓ |
| Course selection | Dynamic enrolled courses | ✓ |
| Grade acknowledgment | `[תודה 👍]` `[רוצה לתכנן שיפור]` | ✓ |
| Grade below threshold | `[רוצה לתכנן חזרה]` `[הבנתי, המשך]` | ✓ |
| Manual update confirm | `[כן, עדכן]` `[לא, תקן]` | ✓ |
| Cancel vs postpone | `[כן, מחק]` `[לא, רק נדחה]` | ✓ |
| Unreadable PDF | `[פתח קובץ]` `[הבנתי, תודה]` | ✓ |
| Lecture reminder 24h | `[כן, הוסף ליומן]` `[לא, אצפה בהקלטה]` `[כבר יש לי ביומן]` | ✓ |
| Lecture reminder 2h | `[הבנתי 👍]` `[לא אגיע היום]` | ✓ |
| Onboarding — GCal | `[חבר Google Calendar]` `[אחר כך]` | ✗ |
| Onboarding — study time | `[ימי חול בערב]` `[ימי חול בבוקר]` `[סופ"ש]` `[מעורב]` | ✓ |
| Onboarding — upload | `[העלה סילבוס עכשיו]` `[אחר כך]` | ✗ |
| Navigate to tab | `[הצג לוח זמנים →]` `[הצג ציונים →]` `[הצג מיילים →]` | N/A (link, not button) |

---

## Document Metadata

**Version History:**
- v1.0 (Feb 11, 2026): Initial Telegram bot PRD
- v2.0 (March 2026): Web portal, virtual email, Gio assistant
- v2.1 (March 2026): Effort estimates, proactivity, exam selection, Gio memory, grade tracking
- v2.2 (March 2026): PDF-first pipeline, unreadable PDF protocol, manual upload, zero data entry
- v2.3 (March 2026): Button-first interaction model, button vocabulary, Gio message API
- v2.4 (March 2026): Gio-first architecture, tab navigator, personalization engine, all notifications as Gio chat messages
- v2.5 (March 2026): Full onboarding flow spec
- v2.6 (March 2026): Cost optimizations
- v2.7 (March 2026): Simplified task status to pending/completed — removed in-progress states and progress_percentage — PDF content hash cache, LLM pre-filter, batched reminder generation — auth, virtual email + forwarding toggle, lecture mode (attend/record/per-course), work schedule + calendar sync, notification lead-time preferences

**Next Steps:**
1. Benchmark PDF libraries on real OUI PDFs — determine scanned-PDF rate
2. Build Gio chat shell + button renderer + tab navigator in Week 1 (parallel to backend pipeline)
3. Write initial template YAML for all flows — get native Hebrew review before Week 3
4. Set up personalization A/B test infrastructure from day 1
5. Set up "משהו אחר" tap rate analytics per template_id from day 1

**Contact:** Roy — [Telegram / email]
