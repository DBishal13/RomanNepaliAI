#!/usr/bin/env python3
"""
Ultra-Simple Romanized Nepali Translation using Google Translate
Just install and use - no training, no complexity!
"""

def setup_google_translate():
    """Setup Google Translate - the easiest solution"""
    print("🌐 Setting up Google Translate...")
    
    try:
        from googletrans import Translator
        translator = Translator()
        print("✅ Google Translate ready!")
        return translator
    except ImportError:
        print("📦 Installing Google Translate...")
        import subprocess
        subprocess.run(['pip', 'install', 'googletrans==4.0.0rc1'], capture_output=True)
        
        try:
            from googletrans import Translator
            translator = Translator()
            print("✅ Google Translate installed and ready!")
            return translator
        except Exception as e:
            print(f"❌ Failed to setup Google Translate: {e}")
            return None

def translate_nepali_to_english(text, translator):
    """Translate Romanized Nepali to English"""
    try:
        # Try as Nepali first
        result = translator.translate(text, src='ne', dest='en')
        return result.text
    except Exception as e:
        try:
            # Fallback: auto-detect language
            result = translator.translate(text, dest='en')
            return result.text
        except Exception as e2:
            return f"Translation failed: {e2}"

def main():
    print("🎯 Ultra-Simple Romanized Nepali to English Translation")
    print("=" * 60)
    print("Using Google Translate - No training required!")
    print()
    
    # Setup translator
    translator = setup_google_translate()
    
    if not translator:
        print("❌ Could not setup Google Translate. Please install manually:")
        print("pip install googletrans==4.0.0rc1")
        return
    
    # Test sentences
    test_sentences = [
        "ma ghar gaye",
        "malai tha xaina", 
        "yo ramro cha",
        "timi k gardai chau",
        "Aaja office jana man lagdaina",
        "Kathmandu ko mausam ramro cha",
        "momo khane man lagyo",
        "Nepal ma Dashain maneko",
        "dal bhat power 24 hour",
        "traffic jam ma baseko chu"
    ]
    
    print("🧪 Testing translations:")
    print("-" * 40)
    
    for i, sentence in enumerate(test_sentences, 1):
        translation = translate_nepali_to_english(sentence, translator)
        print(f"{i:2d}. {sentence}")
        print(f"    → {translation}")
        print()
    
    print("✅ Translation complete!")
    print("\n💡 This is much simpler than training your own model!")
    print("💡 For production use, consider Google Cloud Translation API")

if __name__ == "__main__":
    main()
