class InsultFilterBase:
    def __init__(self):
        self.insults = ["idiota", "tonto", "estúpido"]
        self.results = []

    def filter_text(self, text):
        for insult in self.insults:
            if insult in text.lower():
                text = text.replace(insult, "CENSORED")
        self.results.append(text)
        return text

    def get_results(self):
        return self.results