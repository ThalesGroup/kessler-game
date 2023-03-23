from ..controller import KesslerController


class TTSController(KesslerController):

    @property
    def explanation(self) -> str:
        """
        Property for returning explanation strings from the AI controller to the game for tts shout-casting

        """
        raise NotImplementedError("Your derived KesslerController must include an explanation method for passing explanation strings to the game.")
