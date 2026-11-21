"""Provider credentials, stored in the macOS Keychain (not SQLite or logs)."""
import ctypes as C
import json
import os
import ssl
import sys
import threading
import urllib.error
import urllib.request

ENV = {'openai':'OPENAI_API_KEY','anthropic':'ANTHROPIC_API_KEY',
       'mistral':'MISTRAL_API_KEY','gemini':'GEMINI_API_KEY','github':'GITHUB_TOKEN'}
SERVICE = b'org.suxenai.local.connections.v1'
LOCK = threading.RLock()
NOT_FOUND = -25300


class MacKeychain:
    """Use Security.framework directly; secrets never become process arguments."""
    def __init__(self):
        if sys.platform != 'darwin':
            raise ValueError('Trousseau macOS indisponible : utiliser les variables d’environnement.')
        self.sec = C.CDLL('/System/Library/Frameworks/Security.framework/Security')
        self.cf = C.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        P, U, B = C.c_void_p, C.c_uint32, C.c_char_p
        signatures = {
            'SecKeychainFindGenericPassword':[P,U,B,U,B,C.POINTER(U),C.POINTER(P),C.POINTER(P)],
            'SecKeychainAddGenericPassword':[P,U,B,U,B,U,P,C.POINTER(P)],
            'SecKeychainItemModifyAttributesAndData':[P,P,U,P],
            'SecKeychainItemDelete':[P],
            'SecKeychainItemFreeContent':[P,P],
        }
        for name,args in signatures.items():
            func=getattr(self.sec,name);func.argtypes=args;func.restype=C.c_int32
        self.cf.CFRelease.argtypes=[P];self.cf.CFRelease.restype=None

    def _find(self, provider, password=False):
        name=provider.encode();length=C.c_uint32();data=C.c_void_p();item=C.c_void_p()
        status=self.sec.SecKeychainFindGenericPassword(None,len(SERVICE),SERVICE,len(name),name,
            C.byref(length) if password else None,C.byref(data) if password else None,C.byref(item))
        if status==NOT_FOUND:return None,None
        if status!=0:raise ValueError('Trousseau verrouillé ou accès refusé.')
        try:
            value=C.string_at(data,length.value).decode('utf-8') if password else None
        finally:
            if data:self.sec.SecKeychainItemFreeContent(None,data)
        return item,value

    def get(self, provider):
        item,value=self._find(provider,True)
        if item:self.cf.CFRelease(item)
        return value or ''

    def set(self, provider, value):
        name=provider.encode();raw=value.encode();buf=C.create_string_buffer(raw)
        item,_=self._find(provider)
        try:
            if item:status=self.sec.SecKeychainItemModifyAttributesAndData(item,None,len(raw),buf)
            else:status=self.sec.SecKeychainAddGenericPassword(None,len(SERVICE),SERVICE,len(name),name,len(raw),buf,None)
            if status!=0:raise ValueError('Impossible d’enregistrer dans le trousseau.')
        finally:
            if item:self.cf.CFRelease(item)
            C.memset(buf,0,len(raw))

    def delete(self, provider):
        item,_=self._find(provider)
        if item:
            try:
                if self.sec.SecKeychainItemDelete(item)!=0:raise ValueError('Suppression du trousseau refusée.')
            finally:self.cf.CFRelease(item)


def validate_provider(provider):
    if not isinstance(provider,str) or provider not in ENV:raise ValueError('Fournisseur inconnu.')
    return provider


def key(provider):
    validate_provider(provider)
    env=os.getenv(ENV[provider],'').strip()
    if env:return env
    if sys.platform!='darwin':return ''
    with LOCK:return MacKeychain().get(provider)


def status(provider):
    validate_provider(provider)
    if os.getenv(ENV[provider],'').strip():return {'configured':True,'source':'environment'}
    try:return {'configured':bool(key(provider)),'source':'keychain' if sys.platform=='darwin' else 'unavailable'}
    except ValueError:return {'configured':False,'source':'locked'}


def save(provider, secret):
    validate_provider(provider)
    if not isinstance(secret,str):raise ValueError('Clé invalide.')
    secret=secret.strip()
    if not 8<=len(secret)<=4096 or any(ord(c)<33 or ord(c)>126 for c in secret):
        raise ValueError('Clé invalide : coller uniquement le jeton.')
    with LOCK:MacKeychain().set(provider,secret)


def remove(provider):
    validate_provider(provider)
    with LOCK:MacKeychain().delete(provider)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def opener():
    # The standalone app bundles trusted CA roots; source installs can use system roots.
    try:
        import certifi
        context=ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        context=ssl.create_default_context()
    return urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=context))


def test(provider):
    """Read-only provider check. No prompts, user documents or paid generation."""
    if provider=='ollama':
        url='http://127.0.0.1:11434/api/tags';headers={}
    else:
        validate_provider(provider);secret=key(provider)
        if not secret:raise ValueError('Enregistrer une clé avant de tester.')
        url={'openai':'https://api.openai.com/v1/models','anthropic':'https://api.anthropic.com/v1/models',
             'mistral':'https://api.mistral.ai/v1/models','gemini':'https://generativelanguage.googleapis.com/v1beta/models',
             'github':'https://api.github.com/user'}[provider]
        headers={'Authorization':'Bearer '+secret}
        if provider=='anthropic':headers={'x-api-key':secret,'anthropic-version':'2023-06-01'}
        elif provider=='gemini':headers={'x-goog-api-key':secret}
        elif provider=='github':headers.update({'Accept':'application/vnd.github+json','User-Agent':'SuxenAI/0.8'})
    try:
        request=urllib.request.Request(url,headers=headers)
        with opener().open(request,timeout=10) as res:
            if provider=='ollama':
                models=json.loads(res.read(1_000_001))['models']
                return {'ok':True,'models':[m['name'] for m in models[:100]]}
            return {'ok':True}
    except urllib.error.HTTPError as e:
        raise ValueError(f'Connexion refusée (HTTP {e.code}). Vérifiez la clé ou les permissions.') from None
    except (urllib.error.URLError,TimeoutError,ValueError,KeyError):
        raise ValueError('Connexion indisponible. Vérifiez le réseau ou démarrez Ollama.') from None
