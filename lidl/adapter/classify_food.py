FOOD_HINTS = {
    "pollo", "carne", "pesce", "salmone", "hamburger", "salsiccia",
    "cotoletta", "formaggio", "mozzarella", "gorgonzola", "grana",
    "feta", "gouda", "latte", "burro", "pizza", "pasta",
    "cous cous", "muesli", "cereali", "pane", "biscotti", "cracker",
    "olive", "funghi", "carciofi", "patate", "carote", "mele",
    "uva", "melone", "pesche", "peperone", "verdure", "frutta",
    "pomodoro", "insalata", "tonno", "prosciutto", "polpette",
    "gelato", "birra", "vino", "chianti", "barbera", "cedrata",
    "sushi", "lumache", "paté", "tortilla", "snack", "polpa",
    "limanda", "patatine", "camembert", "pommes"
}

NON_FOOD_HINTS = {
    "pantaloni", "tavolino", "asciugapiatti", "contenitori",
    "posate", "bicchieri", "piatti", "ciotole", "pellicola",
    "vernice", "pennelli", "deodorante"
}


def classify_product(title: str) -> str:
    text = " ".join((title or "").lower().split())

    if any(token in text for token in NON_FOOD_HINTS):
        return "NON_FOOD"

    if any(token in text for token in FOOD_HINTS):
        return "FOOD"

    return "UNKNOWN"


if __name__ == "__main__":
    assert classify_product("Petto di pollo disossato") == "FOOD"
    assert classify_product("Camembert") == "FOOD"
    assert classify_product("Pantaloni da trekking da uomo") == "NON_FOOD"
    assert classify_product("Oggetto misterioso") == "UNKNOWN"

    print("classify_food: PASS")
