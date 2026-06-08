from deep_translator import GoogleTranslator

def translate_text(text_to_translate, target_language='en'):
    try:
        if not text_to_translate or not text_to_translate.strip():
            return "No text found to translate."
        return GoogleTranslator(source='auto', target=target_language).translate(text_to_translate)
    except Exception as e:
        return f"Translation error: {str(e)}"
