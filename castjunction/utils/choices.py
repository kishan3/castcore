"""Choices for different models."""


# Gender
MALE = 'M'
FEMALE = 'F'
OTHER = 'O'
NOT_SPECIFIED = "NS"
GENDER_CHOICES = (
    (MALE, 'Male'),
    (FEMALE, 'Female'),
    (OTHER, 'Other'),
    (NOT_SPECIFIED, 'Not_specified')
)

# Job state
DRAFT = 'DR'
PENDING_APPROVAL = 'PA'
APPROVED = 'A'
REMOVED = 'R'
CLOSED = 'C'
JOB_STATE_CHOICES = (
    (DRAFT, 'Draft'),
    (PENDING_APPROVAL, 'Unapproved'),
    (APPROVED, 'Approved'),
    (REMOVED, 'Removed'),
    (CLOSED, 'Closed'),)


# JOB TYPES

FEATURE_FILM = "feature_film"
INTERNET_MOVIE = "internet_movie"
THEATRE = "theatre"
TELEVISION = "television"
MODELLING = "modelling"
ADVERTISING = "advertising"
OTHER = "other"

JOB_TYPE_CHOICES = (
    (FEATURE_FILM, "feature_film"),
    (INTERNET_MOVIE, "internet_movie"),
    (THEATRE, "theatre"),
    (TELEVISION, "television"),
    (MODELLING, "modelling"),
    (ADVERTISING, "advertising"),
    (OTHER, "other"),
)

# Media Type
PRIMARY = 'P'
GENERIC = 'G'
COVER = 'C'

MEDIA_TYPE_CHOICES = (
    (PRIMARY, 'Primary'),
    (GENERIC, 'Generic'),
    (COVER, 'Cover'),
)

# Profile States
PUBLIC = 'PB'
PRIVATE = 'PR'
DISABLED = 'DA'

PROFILE_STATE_CHOICES = (
    (PUBLIC, 'public'),
    (PRIVATE, 'private'),
    (DISABLED, 'disabled'),
)


DOES_NOT_MATTER = ""

# Skin types

VERY_FAIR = "very_fair"
Fair = "fair"
Wheatish = "wheatish"
DUSKY = "dusky"
Dark = "dark"
VERY_DARK = "very_dark"

SKIN_TYPE_CHOICES = (
    (VERY_FAIR, "very_fair"),
    (Fair, "fair"),
    (Wheatish, "wheatish"),
    (DUSKY, "dusky"),
    (Dark, "dark"),
    (VERY_DARK, "very_dark"),
    (DOES_NOT_MATTER, "does_not_matter"),
)

# hair type
STRAIGHT = "straight"
WAVY = "wavy"
CURLY = "curly"
SCANTY = "scanty"
BALD = "bald"
HALF_BALD = "half_bald"

HAIR_TYPE_CHOICES = (
    (STRAIGHT, "straight"),
    (WAVY, "wavy"),
    (CURLY, "curly"),
    (SCANTY, "scanty"),
    (BALD, "bald"),
    (HALF_BALD, "half_bald"),
    (DOES_NOT_MATTER, "does_not_matter"),
)

# colors


BLACK = "black"
BLONDE = "blonde"
BLUE = "blue"
DARK_BROWN = "dark_brown"
GREEN = "green"
GREY = "grey"
HAZEL = "hazel"
LIGHT_BROWN = "light_brown"
OTHER = "other"
RED = "red"
VIOLET = "violet"
WHITE = "white"

EYE_COLOR_CHOICES = (
    (BLACK, "black"),
    (BLUE, "blue"),
    (DARK_BROWN, "dark_brown"),
    (LIGHT_BROWN, "light_brown"),
    (GREEN, "green"),
    (GREY, "grey"),
    (VIOLET, "violet"),
    (HAZEL, "hazel"),
    (DOES_NOT_MATTER, "does_not_matter"),
)


HAIR_COLOR_CHOICES = (
    (BLACK, "black"),
    (DARK_BROWN, "dark_brown"),
    (LIGHT_BROWN, "light_brown"),
    (BLONDE, "blonde"),
    (RED, "red"),
    (GREY, "grey"),
    (WHITE, "white"),
    (DOES_NOT_MATTER, "does_not_matter"),
)
# body types

SKINNY = 'skinny'
BULKY = 'bulky'
SLIM = 'slim'
ATHLETIC = 'athletic'
MUSCULAR = 'muscular'
CURVY = 'curvy'
HEAVY = 'heavy'
VERY_HEAVY = 'very_heavy'
VERY_FAT = 'very_fat'

BODY_TYPES = (
    # common
    (SKINNY, 'skinny'),
    (SLIM, 'slim'),
    (ATHLETIC, 'athletic'),
    (MUSCULAR, 'muscular'),
    (HEAVY, 'heavy'),

    # male
    (BULKY, 'bulky'),
    (VERY_FAT, 'very_fat'),

    # female
    (CURVY, 'curvy'),
    (VERY_HEAVY, 'very_heavy'),
    (DOES_NOT_MATTER, "does_not_matter"),
)

ARMY_CUT = "army_cut"
NORMAL = "normal"
SLIGHTLY_LONG = "slightly_long"
SHOULDER_LENGTH = "shoulder_length"
PARTIALLY_BALD = "partially_bald"
COMPLETELY_BALD = "completely_bald"
BOY_CUT = "boy_cut"
BUST_LENGTH = "bust_length"
WAIST_LENGTH = "waist_length"
KNEE_LENGTH = "knee_length"

HAIR_STYLE_CHOICES = (
    # common
    (PARTIALLY_BALD, "partially_bald"),
    (COMPLETELY_BALD, "completely_bald"),
    (SHOULDER_LENGTH, "shoulder_length"),
    # male
    (ARMY_CUT, "army_cut"),
    (NORMAL, "normal"),
    (SLIGHTLY_LONG, "slightly_long"),
    # female
    (BOY_CUT, "boy_cut"),
    (BUST_LENGTH, "bust_length"),
    (WAIST_LENGTH, "waist_length"),
    (KNEE_LENGTH, "knee_length"),
)

# Languages
ENGLISH = 'english'
HINDI = 'hindi'
GUJARATI = 'gujarati'
BENGALI = 'bengali'

LANGUAGE_CHOICES = (
    (ENGLISH, 'english'),
    (HINDI, 'hindi'),
    (GUJARATI, 'gujarati'),
    (BENGALI, 'bengali'),
    (DOES_NOT_MATTER, "does_not_matter"),
)


PRINT = "print"
MOVIE = "movie"
DIGITAL = "digital"

AUDITION_TYPE_CHOICES = (
    (TELEVISION, "television"),
    (PRINT, "print"),
    (MOVIE, "movie"),
    (THEATRE, "theatre"),
    (DIGITAL, "digital"),
)

TALENT = 'talent'
AGENT = 'agent'
DIRECTOR = 'director'
APP_TYPE_CHOICES = (
    (TALENT, 'talent'),
    (DIRECTOR, 'director'),
    (AGENT, 'agent'),
)
