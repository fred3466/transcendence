from dotenv import load_dotenv
import random
import os
load_dotenv()

champions = [
    "Garen: The Might of Demacia, a noble warrior with a powerful spinning strike.",
    "Ahri: The Nine-Tailed Fox, a mage with charm and spirit fire abilities.",
    "Darius: The Hand of Noxus, a brutal warrior with a deadly axe.",
    "Lux: The Lady of Luminosity, a light mage with powerful laser attacks.",
    "Zed: The Master of Shadows, a ninja assassin with shadow clones.",
    "Ashe: The Frost Archer, an archer with ice arrows and a hawk scout.",
    "Katarina: The Sinister Blade, a deadly assassin with spinning daggers.",
    "Teemo: The Swift Scout, a yordle with poisonous darts and stealth.",
    "Jinx: The Loose Cannon, a chaotic marksman with explosive weapons.",
    "Yasuo: The Unforgiven, a swordsman with wind-based abilities and a powerful ultimate.",
    "Veigar: The Tiny Master of Evil, a powerful mage with dark magic and a devastating ultimate."
]

def pick_random_description():
    return random.choice(champions)
