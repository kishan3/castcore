"""json schemas."""
from utils import choices

schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "eye_color": {
            "enum": [
                "black",
                "blue",
                "dark_brown",
                "light_brown",
                "green",
                "grey",
                "violet",
                "hazel",
                "",
            ]
        },
        "height": {"type": ["number", "null"]},
        "street_address": {"type": ["string", "null"]},
        "shoulders": {"type": ["integer", "null"]},
        "chest": {"type": ["integer", "null"]},
        "hair_color": {
            "enum": [
                "black",
                "dark_brown",
                "light_brown",
                "blonde",
                "red",
                "grey",
                "white",
                "",
            ]
        },
        "hair_type": {
            "enum": ["straight", "wavy", "curly", "scanty", "bald", "half_bald", ""]
        },
        "hips": {"type": ["integer", "null"]},
        "waist": {"type": ["integer", "null"]},
        "shoe_size": {"type": ["number", "null"]},
        "skin_type": {
            "enum": ["very_fair", "fair", "wheatish", "dusky", "dark", "very_dark", ""]
        },
        "body_type": {
            "enum": [
                "skinny",
                "slim",
                "athletic",
                "muscular",
                "heavy",
                "bulky",
                "very_fat",
                "curvy",
                "very_heavy",
                "",
            ]
        },
        "hair_style": {
            "enum": [
                "army_cut",
                "normal",
                "slightly_long",
                "shoulder_length",
                "partially_bald",
                "completely_bald",
                "boy_cut",
                "bust_length",
                "waist_length",
                "knee_length",
                "",
            ]
        },
        # SAVE PREFERENCE VALIDATION SCHEMAS
        "gender": {
            "enum": [choices.MALE, choices.FEMALE, choices.OTHER, choices.NOT_SPECIFIED]
        },
    },
}
