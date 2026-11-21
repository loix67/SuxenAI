"""Manual web workflows. No browser automation, credentials, or external requests."""

PROVIDERS = {
    'chatgpt': ('ChatGPT', 'https://chatgpt.com/'),
    'claude': ('Claude', 'https://claude.ai/'),
    'gemini': ('Gemini', 'https://gemini.google.com/'),
    'mistral': ('Le Chat', 'https://chat.mistral.ai/'),
}


def provider_list():
    return [{'id': key, 'name': name, 'url': url} for key, (name, url) in PROVIDERS.items()]


def save_manual_response(db, chat_id, provider, content):
    db.require_chat(chat_id)
    if not isinstance(provider, str) or provider not in PROVIDERS:
        raise ValueError('Service Web inconnu')
    if not isinstance(content, str) or not content.strip() or len(content) > 20000:
        raise ValueError('Collez une réponse de 1 à 20 000 caractères')
    db.add(chat_id, 'Web · ' + PROVIDERS[provider][0] + ' (import manuel)', content.strip())


def prepare_prompt(db, chat_id, text, include_history=False):
    """Return a local preview. Never send it to a provider or copy automatically."""
    chat = db.require_chat(chat_id)
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise ValueError('Saisissez une demande de 1 à 12 000 caractères')
    if include_history is not True:
        return text.strip()
    history = db.history(chat_id)[-6:]
    context = '\n\n'.join(m['speaker'] + ' : ' + m['content'][:1400] for m in history)
    return ('Contexte fourni par l’utilisateur (extraits de la discussion) :\n' + context +
            '\n\nDemande actuelle :\n' + text.strip()) if context else text.strip()
