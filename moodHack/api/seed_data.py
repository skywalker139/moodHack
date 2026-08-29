"""Seed data for moodHack: mood taxonomy, coping mechanisms, music, articles.

This is the single source of truth for the knowledge base. The frontend mood
picker and the RAG layer both read from `MoodResource` rows created here.
"""

# Primary emotions as a flat list of names.
PRIMARY_EMOTIONS = ["HAPPY", "SAD", "SURPRISE", "FEAR", "ANGER", "DISGUST"]

# secondary -> [tertiary, ...]
MOOD_TAXONOMY = {
    "HAPPY": ["JOYFUL", "INTERESTED", "PROUD", "INTIMATE", "OPTIMISTIC", "ACCEPTED"],
    "SAD": ["GUILTY", "ABANDONED", "DESPAIR", "DEPRESSED", "LONELY", "BORED"],
    "SURPRISE": ["STARTLED", "CONFUSED", "AMAZED", "EXCITED"],
    "FEAR": ["SCARED", "ANXIOUS", "INSECURE", "SUBMISSIVE", "HUMILIATED", "REJECTED"],
    "ANGER": ["HATEFUL", "MAD", "AGGRESSIVE", "FRUSTRATED", "THREATENED", "CRITICAL"],
    "DISGUST": ["DISAPPROVAL", "DISAPPOINTED", "AWFUL", "AVOIDANCE"],
}

# tertiary -> [sub-sub, ...]
TERTIARY_MOODS = {
    "JOYFUL": ["AMAZED", "INQUISITIVE"],
    "INTERESTED": ["LIBERATED", "ECSTATIC"],
    "PROUD": ["CONFIDENT", "IMPORTANT"],
    "INTIMATE": ["PLAYFUL", "SENSITIVE"],
    "OPTIMISTIC": ["INSPIRED", "OPEN"],
    "ACCEPTED": ["FULFILLED", "RESPECTED"],
    "GUILTY": ["ASHAMED", "REMORSEFUL"],
    "ABANDONED": ["IGNORED", "VICTIMIZED"],
    "DESPAIR": ["VULNERABLE", "POWERLESS"],
    "DEPRESSED": ["INFERIOR", "EMPTY"],
    "LONELY": ["ABANDONED", "ISOLATED"],
    "BORED": ["APATHETIC", "INDIFFERENT"],
    "STARTLED": ["SHOCKED", "DISMAYED"],
    "CONFUSED": ["DILLUSIONED", "PERPLEXED"],
    "AMAZED": ["ASTONISHED", "AWE"],
    "EXCITED": ["EAGER", "ENERGETIC"],
    "SCARED": ["FRIGHTENED", "TERRIFIED"],
    "ANXIOUS": ["WORRIED", "OVERWHELMED"],
    "INSECURE": ["INFERIOR", "INADEQUATE"],
    "SUBMISSIVE": ["INSIGNIFICANT", "WORTHLESS"],
    "HUMILIATED": ["RIDICULED", "DISRESPECTED"],
    "REJECTED": ["ALIENATED", "INADEQUATE"],
    "HATEFUL": ["VIOLATED", "RESENTFUL"],
    "MAD": ["FURIOUS", "ENRAGED"],
    "AGGRESSIVE": ["PROVOKED", "HOSTILE"],
    "FRUSTRATED": ["IRRITATED", "INFURIATED"],
    "THREATENED": ["INSECURE", "JEALOUS"],
    "CRITICAL": ["SARCASTIC", "SKEPTICAL"],
    "DISAPPROVAL": ["JUDGEMENTAL", "LOATHING"],
    "DISAPPOINTED": ["REPUGNANT", "REVOLTED"],
    "AWFUL": ["DETESTABLE", "REVULSION"],
    "AVOIDANCE": ["AVERSION", "HESITANT"],
}

# Coping mechanisms and music for each secondary mood. Tertiary moods inherit
# these unless they have a more specific entry below.
MOOD_RESOURCES = {
    "HAPPY": {
        "description": "A positive, uplifted state characterized by joy and contentment.",
        "coping": ["Savor the moment and share it with someone you care about.", "Practice gratitude by writing down three good things.", "Engage in a creative or playful activity you enjoy."],
        "music": ["Happy - Pharrell Williams", "Walking on Sunshine - Katrina and the Waves", "Can't Stop the Feeling! - Justin Timberlake"],
        "keywords": ["joy", "contentment", "positive", "gratitude", "uplifted"],
    },
    "SAD": {
        "description": "A low, heavy emotional state often tied to loss or disappointment.",
        "coping": ["Allow yourself to feel without judgment.", "Reach out to a trusted friend or family member.", "Do one small, gentle self-care act (a walk, a warm drink)."],
        "music": ["Someone Like You - Adele", "Fix You - Coldplay", "The Night We Met - Lord Huron"],
        "keywords": ["low", "loss", "disappointment", "heavy", "crying"],
    },
    "SURPRISE": {
        "description": "A sudden emotional shift in response to something unexpected.",
        "coping": ["Pause and take a few slow breaths before reacting.", "Name what surprised you and why.", "Ground yourself by noticing five things around you."],
        "music": ["Uptown Funk - Mark Ronson ft. Bruno Mars", "Shake It Off - Taylor Swift", "On Top of the World - Imagine Dragons"],
        "keywords": ["unexpected", "shock", "startle", "amazement"],
    },
    "FEAR": {
        "description": "A response to perceived threat or uncertainty, ranging from worry to terror.",
        "coping": ["Use slow, deep breathing to calm your nervous system.", "Label the fear out loud; naming it reduces its power.", "Break the fear into smaller, manageable steps."],
        "music": ["Brave - Sara Bareilles", "Fight Song - Rachel Platten", "Three Little Birds - Bob Marley"],
        "keywords": ["anxiety", "worry", "scared", "threat", "panic"],
    },
    "ANGER": {
        "description": "A strong reaction to perceived wrong, injustice, or frustration.",
        "coping": ["Step away and cool down before responding.", "Use physical release safely (a brisk walk, squeezing a stress ball).", "Reframe the situation and identify what you can control."],
        "music": ["Roar - Katy Perry", "Eye of the Tiger - Survivor", "Stronger - Kelly Clarkson"],
        "keywords": ["rage", "frustration", "irritation", "mad", "resentment"],
    },
    "DISGUST": {
        "description": "A feeling of revulsion or disapproval toward something unpleasant.",
        "coping": ["Identify the specific trigger and set a boundary if needed.", "Take a mental step back and observe the reaction.", "Refocus on something neutral or pleasant."],
        "music": ["Get Lucky - Daft Punk", "Good as Hell - Lizzo", "Rather Be - Clean Bandit"],
        "keywords": ["revulsion", "aversion", "disapproval", "rejection"],
    },
    "ANXIOUS": {
        "description": "Persistent worry and unease, often about future events.",
        "coping": ["Practice 4-7-8 breathing: inhale 4s, hold 7s, exhale 8s.", "Write down worries and separate what you can vs. cannot control.", "Move your body for a few minutes to discharge nervous energy."],
        "music": ["Weightless - Marconi Union", "Breathe Me - Sia", "Sunset Lover - Petit Biscuit"],
        "keywords": ["anxiety", "worry", "stress", "overwhelm", "restless"],
    },
    "DEPRESSED": {
        "description": "A persistent low mood with reduced interest or energy.",
        "coping": ["Keep a gentle routine, even if it feels small.", "Spend a few minutes in daylight or fresh air.", "Talk to a professional or a trusted person — you don't have to carry this alone."],
        "music": ["Landslide - Fleetwood Mac", "Hurt - Johnny Cash", "Reasons to Stay - Jason Mraz"],
        "keywords": ["depression", "low mood", "fatigue", "hopelessness"],
    },
    "LONELY": {
        "description": "A sense of disconnection from others, even in company.",
        "coping": ["Send a message to someone you trust.", "Join a group or community around a shared interest.", "Practice self-compassion; loneliness doesn't mean you're unlovable."],
        "music": ["Alone - Heart", "Let Her Go - Passenger", "Talking to the Moon - Bruno Mars"],
        "keywords": ["loneliness", "isolation", "disconnection", "belonging"],
    },
    "FRUSTRATED": {
        "description": "Feeling blocked or thwarted in reaching a goal.",
        "coping": ["Pause and reassess the obstacle objectively.", "Break the task into smaller, achievable steps.", "Take a short break and return with fresh eyes."],
        "music": ["Break Stuff - Limp Bizkit", "I Won't Back Down - Tom Petty", "The Middle - Jimmy Eat World"],
        "keywords": ["frustration", "blocked", "stuck", "irritation"],
    },
    "OVERWHELMED": {
        "description": "Feeling flooded by too many demands at once.",
        "coping": ["Write everything down and prioritize just one thing.", "Say no to non-essential commitments.", "Take a complete screen break for 15 minutes."],
        "music": ["The Sound of Silence - Disturbed", "Let It Be - The Beatles", "Wherever You Will Go - The Calling"],
        "keywords": ["overwhelm", "too much", "stress", "burnout"],
    },
}

# Specific tertiary moods that need distinct resources beyond their parent.
TERTIARY_RESOURCES = {
    "PROUD": {
        "coping": ["Reflect on the effort behind the achievement.", "Share the win with someone who celebrates you.", "Use the confidence to set your next small goal."],
        "music": ["Hall of Fame - The Script", "Don't Stop Believin' - Journey"],
    },
    "CONFIDENT": {
        "coping": ["Stand in a grounded posture and breathe deeply.", "Recall a past success you're proud of.", "Take one bold step toward what you want."],
        "music": ["Confident - Demi Lovato", "Born This Way - Lady Gaga"],
    },
    "EXCITED": {
        "coping": ["Channel the energy into planning and action.", "Share the excitement with someone.", "Stay present and enjoy the anticipation."],
        "music": ["I Gotta Feeling - The Black Eyed Peas", "Dynamite - BTS"],
    },
    "BORED": {
        "coping": ["Try something new, even a tiny novelty.", "Reconnect with a hobby you've set aside.", "Set a small, time-boxed challenge for yourself."],
        "music": ["New Light - John Mayer", "Electric Feel - MGMT"],
    },
    "GUILTY": {
        "coping": ["Acknowledge the mistake without self-attack.", "Make amends if it would help.", "Separate the action from your worth as a person."],
        "music": ["Apologize - OneRepublic", "Sorry - Justin Bieber"],
    },
}

# Resource links for a professional-help / article callout.
RESOURCE_LINKS = [
    {"title": "Psychology Today", "url": "https://www.psychologytoday.com/"},
    {"title": "IIT Roorkee Wellness Cell", "url": "https://wellness.iitr.ac.in/"},
    {"title": "Mind - Mental Health Charity", "url": "https://www.mind.org.uk/"},
    {"title": "7 Cups - Free Support", "url": "https://www.7cups.com/"},
]

# Starter article library (curated, stable links).
ARTICLES = [
    {
        "title": "How to Manage and Understand Your Emotions",
        "url": "https://www.psychologytoday.com/us/blog/the-neuroscience-of-personal-growth/202408/the-first-step-to-tackling-your-emotions",
        "description": "A starting point for naming and working through difficult emotions.",
        "topics": ["emotions", "coping", "self-awareness"],
        "source": "Psychology Today",
    },
    {
        "title": "Anxiety Coping Strategies",
        "url": "https://www.mind.org.uk/information-support/types-of-mental-health-problems/anxiety-and-panic-attacks/",
        "description": "Practical techniques for managing anxiety and panic.",
        "topics": ["anxiety", "coping", "mental health"],
        "source": "Mind",
    },
    {
        "title": "Understanding Depression",
        "url": "https://www.nimh.nih.gov/health/topics/depression",
        "description": "An overview of depression, its signs, and treatment options.",
        "topics": ["depression", "mental health", "support"],
        "source": "NIMH",
    },
    {
        "title": "The Science of Gratitude",
        "url": "https://www.psychologytoday.com/us/basics/gratitude",
        "description": "Why gratitude practices improve emotional wellbeing.",
        "topics": ["happiness", "gratitude", "wellbeing"],
        "source": "Psychology Today",
    },
    {
        "title": "Mindfulness for Stress Reduction",
        "url": "https://www.mindful.org/how-to-manage-stress-with-mindfulness-and-meditation/",
        "description": "How mindfulness and meditation help reduce stress.",
        "topics": ["mindfulness", "stress", "meditation"],
        "source": "Mindful",
    },
]


def all_moods() -> list[tuple[str, str]]:
    """Return a flat list of (mood_name, primary_emotion) pairs."""
    moods: list[tuple[str, str]] = []
    for primary in PRIMARY_EMOTIONS:
        moods.append((primary, primary))
        for secondary in MOOD_TAXONOMY.get(primary, []):
            moods.append((secondary, primary))
            for tertiary in TERTIARY_MOODS.get(secondary, []):
                moods.append((tertiary, primary))
    return moods
