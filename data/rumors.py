# data/rumors.py
# The 26 cryptic Rumors from Dungeon of Doom.
# Shown via Actions > Rumors menu. No manual exists — these ARE the manual.

RUMORS = [
    "A force prevents you from escaping to the surface.",
    "Maybe the Orb will set you free...",
    "Beauty can tame a beast.",
    "A Sethron is 63\" tall.",
    "Roni is life.",                             # Raymonds loved Rice-A-Roni
    "The Dark Wizard dwells on the 40th level.",
    "Lightning reflects off staircases.",
    "Standing in a staircase protects against spells.",
    "Vampires do not drain levels—they drain life itself.",
    "A giant scorpion's sting weakens the muscles.",
    "Charisma affects what monsters leave behind.",
    "The Floor has been known to attack unwary travelers.",
    "Identify Scrolls have more than one use.",
    "Jewelers and rings have a natural affinity.",
    "Not all orbs are what they seem.",
    "The wise read before they drink.",
    "Alchemists never poison themselves by accident.",
    "16 points of Intelligence illuminates the darkness.",
    "A knight knows good armour when he sees it.",
    "Fighters speak the language of blades.",
    "Sages understand words that others cannot read.",
    "Wizards and their wands are never parted.",
    "Dual wielding requires 16 Strength and 18 Dexterity.",
    "18 Strength is needed to push boulders.",
    "The Plastic Orb is not the real Orb.",
    "Eating too much is as deadly as eating too little.",
]

assert len(RUMORS) == 26, f"Expected 26 rumors, got {len(RUMORS)}"
