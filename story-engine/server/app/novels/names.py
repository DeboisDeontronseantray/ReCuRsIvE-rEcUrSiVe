from faker import Faker

# transliterate is only needed for Russian. Guarded so a missing/broken install
# degrades to leaving Cyrillic alone rather than breaking every other region.
try:
    from transliterate import translit

    _HAS_TRANSLIT = True
except ImportError:  # pragma: no cover - depends on the install
    _HAS_TRANSLIT = False

# The regions offered in the create form, mapped to faker locales. The keys are
# what the user picks and what gets sent to the AI as a cultural touchstone.
REGION_LOCALES = {
    "Italy": "it_IT",
    "France": "fr_FR",
    "Germany": "de_DE",
    "Russia": "ru_RU",
    "Britain": "en_GB",
    "America": "en_US",
}

DEFAULT_REGION = "Italy"

# ru_RU is the only locale that returns a non-Latin script, which is unusable
# in an English novel — 'Алексеев Николай' has to become 'Alekseev Nikolay'.
_CYRILLIC_LOCALES = {"ru_RU"}


def _to_latin(value: str, locale: str) -> str:
    if locale not in _CYRILLIC_LOCALES or not _HAS_TRANSLIT:
        return value
    # reversed=True goes Cyrillic -> Latin.
    return translit(value, "ru", reversed=True)


# Builds a pool of real person names for the region, for the characters step to
# pick from. The model is bad at inventing names — it reaches for the same
# invented-fantasy register every time — so it gets handed real ones instead.
#
# Names are composed from first_name_* + last_name rather than faker's name(),
# because name() prefixes titles ('Dott. Antonietta Valentino', 'Dr. Hans-Rudolf
# Siering') that must not reach the prompt.
def build_name_pool(region: str | None, count: int = 25, surname_count: int = 12) -> dict:
    locale = REGION_LOCALES.get(region or DEFAULT_REGION, REGION_LOCALES[DEFAULT_REGION])
    fake = Faker(locale)

    pool = {}
    for key, first_name in (("male", fake.first_name_male), ("female", fake.first_name_female)):
        names = []
        seen = set()
        # Bounded loop: dedupe can reject a draw, so cap the attempts rather
        # than spinning if a locale's pool is smaller than `count`.
        for _ in range(count * 10):
            if len(names) >= count:
                break
            name = _to_latin(f"{first_name()} {fake.last_name()}", locale)
            if name not in seen:
                seen.add(name)
                names.append(name)
        pool[key] = names

    # Standalone surnames, separate from the first_name+last_name pairs above.
    # Family members (spouses, parents, children) need to share one surname,
    # which the paired names can't provide on their own since each is an
    # independent random draw. The model reuses one of these across a family
    # instead of inventing a surname.
    surnames = []
    seen_surnames = set()
    for _ in range(surname_count * 10):
        if len(surnames) >= surname_count:
            break
        surname = _to_latin(fake.last_name(), locale)
        if surname not in seen_surnames:
            seen_surnames.add(surname)
            surnames.append(surname)
    pool["surnames"] = surnames

    return pool
