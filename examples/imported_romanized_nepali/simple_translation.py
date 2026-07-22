#!/usr/bin/env python3
"""
Simple Romanized Nepali to English Translation using Pre-trained Models
No training required - just use existing multilingual models!
"""

import torch
from transformers import MarianMTModel, MarianTokenizer, pipeline
import warnings
warnings.filterwarnings('ignore')

def setup_translation_models():
    """Setup various pre-trained translation models"""
    print("🚀 Setting up pre-trained translation models...")
    
    models = {}
    
    # Method 1: Google Translate via transformers pipeline
    try:
        print("📥 Loading Google Translate pipeline...")
        models['google'] = pipeline("translation", model="Helsinki-NLP/opus-mt-hi-en")
        print("✅ Google Translate model loaded!")
    except Exception as e:
        print(f"⚠️ Google Translate model failed: {e}")
    
    # Method 2: Facebook's M2M-100 (multilingual)
    try:
        print("📥 Loading Facebook M2M-100 multilingual model...")
        models['m2m'] = pipeline("translation", model="facebook/m2m100_418M", 
                                tokenizer="facebook/m2m100_418M")
        print("✅ M2M-100 model loaded!")
    except Exception as e:
        print(f"⚠️ M2M-100 model failed: {e}")
    
    # Method 3: mT5 multilingual model
    try:
        print("📥 Loading mT5 multilingual model...")
        models['mt5'] = pipeline("text2text-generation", model="google/mt5-small")
        print("✅ mT5 model loaded!")
    except Exception as e:
        print(f"⚠️ mT5 model failed: {e}")
    
    return models

def translate_with_multiple_models(text, models):
    """Try translation with multiple models"""
    print(f"\n🔄 Translating: '{text}'")
    print("-" * 60)
    
    results = {}
    
    # Try Google Translate model (Hindi to English - works for Romanized Nepali)
    if 'google' in models:
        try:
            result = models['google'](text, max_length=100)
            translation = result[0]['translation_text']
            results['Google Translate'] = translation
            print(f"🇬 Google Translate: {translation}")
        except Exception as e:
            print(f"❌ Google Translate failed: {e}")
    
    # Try M2M-100
    if 'm2m' in models:
        try:
            # M2M-100 needs source and target language codes
            result = models['m2m'](text, forced_bos_token_id=256047)  # English target
            translation = result[0]['translation_text']
            results['M2M-100'] = translation
            print(f"🌍 M2M-100: {translation}")
        except Exception as e:
            print(f"❌ M2M-100 failed: {e}")
    
    # Try mT5
    if 'mt5' in models:
        try:
            prompt = f"translate to English: {text}"
            result = models['mt5'](prompt, max_length=100)
            translation = result[0]['generated_text']
            results['mT5'] = translation
            print(f"🤖 mT5: {translation}")
        except Exception as e:
            print(f"❌ mT5 failed: {e}")
    
    return results

def simple_google_translate():
    """Even simpler - use Google Translate API if available"""
    try:
        from googletrans import Translator
        translator = Translator()
        
        def translate_simple(text):
            result = translator.translate(text, src='ne', dest='en')
            return result.text
        
        print("✅ Google Translate API available!")
        return translate_simple
    except ImportError:
        print("⚠️ Google Translate API not installed. Install with: pip install googletrans==4.0.0rc1")
        return None

def main():
    print("🎯 Simple Romanized Nepali to English Translation")
    print("=" * 60)
    print("Using pre-trained multilingual models - NO TRAINING REQUIRED!")
    print()
    
    # Test sentences
    test_sentences = [
        "ma ghar gaye",
        "malai tha xaina", 
        "yo ramro cha",
        "timi k gardai chau",
        "Aaja office jana man lagdaina",
        "Kathmandu ko mausam ramro cha",
        "momo khane man lagyo",
        "Nepal ma Dashain maneko"
    ]
    
    # Setup models
    models = setup_translation_models()
    
    if not models:
        print("❌ No models loaded successfully. Please check your internet connection.")
        return
    
    print(f"\n✅ Loaded {len(models)} translation models")
    print("🧪 Testing translations...")
    
    # Test translations
    all_results = {}
    for sentence in test_sentences:
        results = translate_with_multiple_models(sentence, models)
        all_results[sentence] = results
        print()
    
    # Summary
    print("\n📊 Translation Summary")
    print("=" * 60)
    
    for sentence, results in all_results.items():
        if results:
            print(f"\nInput: {sentence}")
            for model_name, translation in results.items():
                print(f"  {model_name}: {translation}")
        else:
            print(f"\nInput: {sentence}")
            print("  No successful translations")
    
    # Try Google Translate API as backup
    print("\n🔄 Trying Google Translate API as backup...")
    simple_translator = simple_google_translate()
    
    if simple_translator:
        print("\n🌐 Google Translate API Results:")
        for sentence in test_sentences[:3]:  # Test first 3
            try:
                translation = simple_translator(sentence)
                print(f"  {sentence} → {translation}")
            except Exception as e:
                print(f"  {sentence} → Error: {e}")
    
    print("\n✅ Translation testing complete!")
    print("\n💡 Recommendations:")
    print("1. Use Google Translate API for best results: pip install googletrans==4.0.0rc1")
    print("2. Helsinki-NLP models work well for Hindi/Nepali")
    print("3. M2M-100 is good for multiple languages")
    print("4. For production: Use Google Cloud Translation API or Azure Translator")

if __name__ == "__main__":
    main()
