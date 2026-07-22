"""Translation helpers for RomanNepaliAI.

Provides a Translator wrapper that supports a stub backend, an optional
Hugging Face MarianMT backend (Helsinki-NLP/opus-mt-ne-en), and a lightweight
Google Translate adapter (via deep-translator) when available.

Backends:
- stub: returns input unchanged
- hf: uses transformers MarianMT
- google: uses deep-translator's GoogleTranslator (install: pip install deep-translator)
"""
from typing import Optional


class Translator:
    def __init__(self, backend: str = "stub", model_name: Optional[str] = None):
        self.backend = backend
        self.model_name = model_name or "Helsinki-NLP/opus-mt-ne-en"
        self.available = False
        self._load_error = None

        if self.backend == "hf":
            try:
                from transformers import MarianMTModel, MarianTokenizer
                # Delay model download until initialization
                self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
                self.model = MarianMTModel.from_pretrained(self.model_name)
                self.available = True
            except Exception as e:
                self.available = False
                self._load_error = e

        elif self.backend == "google":
            try:
                from deep_translator import GoogleTranslator
                self._google_translator_cls = GoogleTranslator
                self.available = True
            except Exception as e:
                self.available = False
                self._load_error = e

    def translate(self, text: str, src: str = "ne", tgt: str = "en") -> str:
        """Translate `text` from Nepali to English.

        If a non-stub backend is selected but unavailable, an informative
        exception will be raised. The stub backend returns the input unchanged.
        """
        if self.backend == "stub":
            return text

        if self.backend == "google":
            if not self.available:
                raise RuntimeError(
                    "Google Translate backend unavailable. Install deep-translator (pip install deep-translator) "
                    f"or use the stub backend. Original error: {self._load_error}"
                )
            try:
                return self._google_translator_cls(source=src, target=tgt).translate(text)
            except Exception as e:
                raise RuntimeError(f"Google Translate failed: {e}")

        if self.backend == "hf":
            if not self.available:
                raise RuntimeError(
                    "Hugging Face backend is unavailable. Install transformers and the model "
                    f"({self.model_name}) or use the stub backend. Original error: {self._load_error}"
                )

            # Run translation using MarianMT
            inputs = self.tokenizer([text], return_tensors="pt", truncation=True, padding=True)
            translated = self.model.generate(**inputs)
            out = self.tokenizer.batch_decode(translated, skip_special_tokens=True)[0]
            return out

        raise ValueError(f"Unknown backend: {self.backend}")


# Convenience one-shot helper
def translate_text(text: str, backend: str = "stub", model_name: Optional[str] = None) -> str:
    t = Translator(backend=backend, model_name=model_name)
    return t.translate(text)
