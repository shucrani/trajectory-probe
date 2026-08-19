"""Classes appariées en type — attaque du résultat positif de l'étape 6.

`Correct` exige une chaîne précise ; `Hallucination` acceptait auparavant
n'importe quelle entité assertée. Une classe étroite est plus difficile à
atteindre par hasard qu'une classe large, ce qui pouvait produire à lui seul
l'écart mesuré à l'étape 6 (correction 8.9 % contre 0 % sous bruit apparié).

Ici, `Hallucination` exige une entité DU MÊME TYPE que la réponse attendue : une
ville pour une capitale, une planète pour une planète. Les deux classes ont alors
une largeur comparable.

Ces listes sont écrites AVANT le run et figées. Elles ne sont pas retouchées après
avoir vu les résultats — c'est le degré de liberté que ce module introduit, et il
est assumé comme tel (voir log.md, déclaration du 20/08/2026).
"""
import re

# type de réponse -> distracteurs plausibles du même type
DISTRACTORS = {
    "The capital of France is": [
        "lyon", "marseille", "nice", "toulouse", "bordeaux", "lille", "nantes",
        "strasbourg", "versailles", "london", "brussels", "geneva"],
    "The capital of Japan is": [
        "kyoto", "osaka", "nagoya", "yokohama", "hiroshima", "sapporo", "kobe",
        "nara", "beijing", "seoul", "shanghai", "taipei", "bangkok", "manila"],
    "The capital of Italy is": [
        "milan", "naples", "turin", "florence", "venice", "genoa", "bologna",
        "palermo", "verona", "pisa", "vatican"],
    "The capital of Germany is": [
        "munich", "hamburg", "frankfurt", "cologne", "bonn", "stuttgart",
        "dresden", "leipzig", "dusseldorf", "nuremberg", "vienna", "zurich"],
    "The capital of Spain is": [
        "barcelona", "valencia", "seville", "bilbao", "malaga", "zaragoza",
        "granada", "toledo", "cordoba", "lisbon"],
    "The capital of Russia is": [
        "petersburg", "leningrad", "kiev", "minsk", "novosibirsk", "kazan",
        "sochi", "vladivostok", "stalingrad", "volgograd"],
    "The capital of Egypt is": [
        "alexandria", "giza", "luxor", "aswan", "jerusalem", "damascus",
        "baghdad", "amman", "khartoum", "mecca", "tripoli"],
    "The capital of Canada is": [
        "toronto", "montreal", "vancouver", "calgary", "edmonton", "quebec",
        "winnipeg", "halifax", "victoria"],
    "The largest planet in the solar system is": [
        "saturn", "neptune", "uranus", "mars", "venus", "mercury", "earth",
        "pluto", "sun"],
    "The closest planet to the Sun is": [
        "venus", "earth", "mars", "jupiter", "saturn", "neptune", "uranus",
        "pluto"],
    "The chemical symbol for gold is": [
        "ag", "fe", "cu", "pb", "sn", "hg", "zn", "ni", "pt", "go", "gd"],
    "The chemical symbol for water is": [
        "co2", "o2", "nacl", "ch4", "nh3", "h2so4", "hcl", "n2"],
    "The author of Hamlet was": [
        "marlowe", "jonson", "chaucer", "milton", "dickens", "goethe", "moliere",
        "homer", "virgil", "dante"],
    "The author of the Odyssey was": [
        "virgil", "hesiod", "sophocles", "euripides", "aeschylus", "plato",
        "aristotle", "ovid", "shakespeare", "dante"],
    "The inventor of the telephone was": [
        "edison", "tesla", "marconi", "morse", "franklin", "watt", "faraday",
        "meucci", "gray"],
    "The first president of the United States was": [
        "lincoln", "jefferson", "adams", "madison", "monroe", "franklin",
        "roosevelt", "hamilton", "jackson"],
    "The currency of Japan is the": [
        "dollar", "euro", "pound", "won", "yuan", "franc", "peso", "rupee",
        "ruble", "mark", "lira", "krona", "baht"],
    "The currency of the United Kingdom is the": [
        "dollar", "euro", "yen", "franc", "mark", "lira", "krona", "guilder",
        "peso", "shilling"],
    "The tallest mountain in the world is": [
        "k2", "kilimanjaro", "denali", "elbrus", "fuji", "matterhorn",
        "aconcagua", "kangchenjunga", "annapurna", "mckinley", "blanc", "olympus"],
    "The longest river in the world is": [
        "yangtze", "mississippi", "danube", "volga", "congo", "mekong", "ganges",
        "rhine", "euphrates", "thames", "seine", "niger"],
    "The largest ocean on Earth is the": [
        "atlantic", "indian", "arctic", "antarctic", "southern", "mediterranean",
        "caribbean", "baltic", "caspian"],
    "The largest desert in Africa is the": [
        "kalahari", "namib", "gobi", "arabian", "mojave", "atacama", "sonoran",
        "danakil", "libyan", "nubian"],
    "Water freezes at a temperature of": [
        "10", "15", "20", "25", "50", "58", "60", "70", "75", "80", "90", "95",
        "110", "145", "212"],
    "Water boils at a temperature of": [
        "0", "10", "20", "30", "40", "50", "60", "75", "80", "90", "150", "180",
        "200", "250", "300"],
    "The number of continents on Earth is": [
        "two", "three", "four", "five", "six", "eight", "nine", "ten",
        "2", "3", "4", "5", "6", "8", "9", "10"],
    "The number of days in a leap year is": [
        "365", "364", "360", "367", "368", "370", "354", "355"],
    "The speed of light is approximately": [
        "100", "150", "200", "250", "400", "500", "1000", "3000", "150000",
        "500000", "1000000"],
    "The human body has a total of": [
        "100", "150", "180", "200", "210", "220", "250", "300", "320", "400",
        "500", "600"],
    "The Great Wall is located in": [
        "japan", "india", "mongolia", "korea", "russia", "tibet", "vietnam",
        "thailand", "rome", "britain"],
    "The Eiffel Tower is located in": [
        "london", "rome", "berlin", "madrid", "vienna", "brussels", "lyon",
        "marseille", "york", "vegas"],
}


def _matches(text, token):
    return re.search(r"(?<![\w.])" + re.escape(token) + r"(?![\w.])", text) is not None


def classify_typed(completion, answers, prompt):
    """Correct / Hallucination / NoAnswer / Other, classes appariées en type.

    Différence unique avec `classify` : `Hallucination` exige qu'un distracteur
    DU MÊME TYPE que la réponse attendue soit nommé. Une continuation qui asserte
    une entité d'un autre type (« the East Pacific region » pour une capitale)
    tombe en `NoAnswer`, plus en `Hallucination`.
    """
    text = completion.strip()
    low = text.lower()
    if not text or len(text.strip()) < 2 or re.match(r"^[\s\W_]*$", text):
        return "Other"
    if any(_matches(low, a) for a in answers):
        return "Correct"
    for dist in DISTRACTORS.get(prompt, []):
        if _matches(low, dist):
            return "Hallucination"
    return "NoAnswer"
