"""Corpus étendu — prompts, réponses acceptées, distracteurs typés.

Écrit le 20/08/2026 AVANT tout run, conformément à la déclaration de protocole
du même jour. Aucune entrée ne sera retirée ni retouchée après avoir vu quels
prompts bifurquent : ce serait une sélection post-hoc.

Chaque entrée : (prompt, réponses acceptées, distracteurs DU MÊME TYPE).

La diversité syntaxique est délibérée. Le corpus initial n'avait qu'une forme
(« The X of Y is »), ce que `docs/DEGRES-DE-LIBERTE.md` § 1 signalait comme un
degré de liberté non contrôlé.
"""

EXTRA = [
    # --- capitales, autres pays -------------------------------------------
    ("The capital of Portugal is", ["lisbon"],
     ["porto", "madrid", "seville", "braga", "coimbra", "faro", "barcelona"]),
    ("The capital of the Netherlands is", ["amsterdam", "hague"],
     ["rotterdam", "utrecht", "eindhoven", "brussels", "antwerp", "leiden"]),
    ("The capital of Belgium is", ["brussels"],
     ["antwerp", "ghent", "bruges", "liege", "amsterdam", "luxembourg", "namur"]),
    ("The capital of Austria is", ["vienna"],
     ["salzburg", "graz", "innsbruck", "linz", "munich", "prague", "budapest"]),
    ("The capital of Greece is", ["athens"],
     ["sparta", "thessaloniki", "corinth", "crete", "rhodes", "delphi", "istanbul"]),
    ("The capital of Poland is", ["warsaw"],
     ["krakow", "gdansk", "wroclaw", "poznan", "lodz", "prague", "berlin"]),
    ("The capital of Sweden is", ["stockholm"],
     ["gothenburg", "malmo", "uppsala", "oslo", "copenhagen", "helsinki"]),
    ("The capital of Norway is", ["oslo"],
     ["bergen", "trondheim", "stavanger", "stockholm", "copenhagen", "helsinki"]),
    ("The capital of Turkey is", ["ankara"],
     ["istanbul", "izmir", "bursa", "antalya", "adana", "athens", "constantinople"]),
    ("The capital of India is", ["delhi"],
     ["mumbai", "bombay", "calcutta", "kolkata", "chennai", "bangalore", "hyderabad"]),
    ("The capital of China is", ["beijing", "peking"],
     ["shanghai", "guangzhou", "shenzhen", "nanjing", "chengdu", "tokyo", "seoul"]),
    ("The capital of Brazil is", ["brasilia"],
     ["rio", "janeiro", "paulo", "salvador", "recife", "fortaleza", "lisbon"]),
    ("The capital of Australia is", ["canberra"],
     ["sydney", "melbourne", "brisbane", "perth", "adelaide", "darwin", "auckland"]),
    ("The capital of Kenya is", ["nairobi"],
     ["mombasa", "kisumu", "nakuru", "kampala", "addis", "dar", "lagos"]),

    # --- localisation de monuments (forme « X is located in ») -------------
    ("The Colosseum is located in", ["rome", "italy"],
     ["athens", "paris", "london", "madrid", "cairo", "istanbul", "greece", "spain"]),
    ("The Louvre is located in", ["paris", "france"],
     ["london", "rome", "madrid", "berlin", "vienna", "italy", "spain", "england"]),
    ("The Kremlin is located in", ["moscow", "russia"],
     ["petersburg", "kiev", "warsaw", "berlin", "prague", "ukraine", "poland"]),
    ("Big Ben is located in", ["london", "england", "britain"],
     ["paris", "dublin", "edinburgh", "manchester", "york", "france", "ireland"]),
    ("The Statue of Liberty is located in", ["york", "manhattan"],
     ["boston", "washington", "chicago", "philadelphia", "paris", "france"]),
    ("The Taj Mahal is located in", ["india", "agra"],
     ["pakistan", "iran", "turkey", "delhi", "mumbai", "nepal", "bangladesh"]),
    ("Machu Picchu is located in", ["peru"],
     ["bolivia", "chile", "ecuador", "mexico", "brazil", "colombia", "argentina"]),
    ("The Acropolis is located in", ["athens", "greece"],
     ["rome", "italy", "istanbul", "cairo", "sparta", "turkey", "egypt"]),
    ("The Great Pyramid is located in", ["egypt", "giza"],
     ["sudan", "mexico", "peru", "iraq", "greece", "cairo", "libya"]),
    ("Mount Fuji is located in", ["japan"],
     ["china", "korea", "nepal", "taiwan", "tibet", "philippines", "indonesia"]),

    # --- langues -----------------------------------------------------------
    ("The official language of Brazil is", ["portuguese"],
     ["spanish", "english", "french", "italian", "german", "dutch"]),
    ("The official language of Egypt is", ["arabic"],
     ["english", "french", "hebrew", "persian", "turkish", "coptic", "berber"]),
    ("The official language of Austria is", ["german"],
     ["austrian", "english", "hungarian", "czech", "italian", "french"]),
    ("The official language of Mexico is", ["spanish"],
     ["portuguese", "english", "french", "mexican", "italian", "mayan"]),
    ("The official language of Argentina is", ["spanish"],
     ["portuguese", "english", "italian", "french", "german", "argentine"]),

    # --- monnaies ----------------------------------------------------------
    ("The currency of India is the", ["rupee"],
     ["dollar", "euro", "pound", "yen", "yuan", "ruble", "peso", "dinar"]),
    ("The currency of Russia is the", ["ruble", "rouble"],
     ["dollar", "euro", "pound", "yen", "yuan", "rupee", "peso", "krona"]),
    ("The currency of China is the", ["yuan", "renminbi"],
     ["dollar", "euro", "pound", "yen", "ruble", "rupee", "won", "peso"]),
    ("The currency of Mexico is the", ["peso"],
     ["dollar", "euro", "pound", "yen", "real", "rupee", "franc", "escudo"]),

    # --- éléments chimiques ------------------------------------------------
    ("The chemical symbol for iron is", ["fe"],
     ["ir", "in", "au", "ag", "cu", "pb", "zn", "sn", "ni"]),
    ("The chemical symbol for silver is", ["ag"],
     ["si", "au", "fe", "cu", "pb", "sn", "zn", "hg", "sv"]),
    ("The chemical symbol for sodium is", ["na"],
     ["so", "si", "s", "k", "ca", "mg", "cl", "li", "sd"]),
    ("The chemical symbol for oxygen is", ["o", "o2"],
     ["ox", "h", "n", "c", "co", "he", "ne", "og"]),

    # --- astronomie --------------------------------------------------------
    ("The planet known as the Red Planet is", ["mars"],
     ["venus", "jupiter", "mercury", "saturn", "neptune", "uranus", "pluto"]),
    ("The planet with the most prominent rings is", ["saturn"],
     ["jupiter", "uranus", "neptune", "mars", "venus", "mercury", "pluto"]),
    ("The closest star to the Earth is the", ["sun"],
     ["proxima", "centauri", "sirius", "polaris", "vega", "betelgeuse", "moon"]),
    ("The hottest planet in the solar system is", ["venus"],
     ["mercury", "mars", "jupiter", "saturn", "neptune", "uranus", "sun"]),

    # --- auteurs et oeuvres ------------------------------------------------
    ("The author of Romeo and Juliet was", ["shakespeare"],
     ["marlowe", "jonson", "chaucer", "milton", "dickens", "goethe", "dante"]),
    ("The author of Don Quixote was", ["cervantes"],
     ["lope", "borges", "dante", "shakespeare", "moliere", "homer", "virgil"]),
    ("The Mona Lisa was painted by", ["leonardo", "vinci"],
     ["michelangelo", "raphael", "donatello", "botticelli", "titian", "caravaggio",
      "picasso", "rembrandt"]),
    ("The theory of relativity was developed by", ["einstein"],
     ["newton", "bohr", "planck", "heisenberg", "maxwell", "galileo", "tesla"]),
    ("The Origin of Species was written by", ["darwin"],
     ["lamarck", "wallace", "mendel", "huxley", "linnaeus", "newton", "malthus"]),

    # --- géographie superlative -------------------------------------------
    ("The longest river in Africa is the", ["nile"],
     ["congo", "niger", "zambezi", "amazon", "limpopo", "orange", "volta"]),
    ("The largest country in the world is", ["russia"],
     ["china", "canada", "america", "brazil", "australia", "india", "greenland"]),
    ("The smallest country in the world is", ["vatican"],
     ["monaco", "malta", "andorra", "liechtenstein", "luxembourg", "nauru", "tuvalu"]),
    ("The largest island in the world is", ["greenland"],
     ["australia", "borneo", "madagascar", "iceland", "sumatra", "java", "honshu"]),
    ("The deepest ocean trench is the", ["mariana", "marianas"],
     ["puerto", "java", "tonga", "kermadec", "philippine", "atlantic", "aleutian"]),

    # --- animaux -----------------------------------------------------------
    ("The largest land animal is the", ["elephant"],
     ["rhinoceros", "hippopotamus", "giraffe", "whale", "bear", "bison", "gorilla"]),
    ("The fastest land animal is the", ["cheetah"],
     ["lion", "leopard", "gazelle", "horse", "antelope", "greyhound", "tiger"]),
    ("The largest animal in the ocean is the", ["whale"],
     ["shark", "squid", "octopus", "dolphin", "orca", "manta", "tuna"]),

    # --- divers ------------------------------------------------------------
    ("The Olympic Games originated in", ["greece", "olympia"],
     ["rome", "egypt", "france", "britain", "china", "italy", "sparta"]),
    ("The sport played at Wimbledon is", ["tennis"],
     ["cricket", "golf", "rugby", "football", "soccer", "polo", "badminton"]),
    ("The first man to walk on the Moon was", ["armstrong"],
     ["aldrin", "collins", "gagarin", "glenn", "shepard", "kennedy", "columbus"]),
]

# Sécurité : aucune entrée sans distracteurs, aucun doublon de prompt.
_texts = [t for t, _, _ in EXTRA]
assert len(_texts) == len(set(_texts)), "prompt dupliqué dans EXTRA"
assert all(a and d for _, a, d in EXTRA), "entrée sans réponse ou sans distracteur"
