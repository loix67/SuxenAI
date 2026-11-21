"""Provider credentials in macOS Keychain or Windows Credential Manager."""
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


class WindowsKeychain:
    """Windows Generic Credentials, per OS user, without process arguments."""
    def __init__(self):
        if sys.platform!='win32':raise ValueError('Coffre Windows indisponible.')
        from ctypes import wintypes as W
        class Credential(C.Structure):
            _fields_=[('Flags',W.DWORD),('Type',W.DWORD),('TargetName',W.LPWSTR),('Comment',W.LPWSTR),('LastWritten',W.FILETIME),('CredentialBlobSize',W.DWORD),('CredentialBlob',C.POINTER(C.c_ubyte)),('Persist',W.DWORD),('AttributeCount',W.DWORD),('Attributes',C.c_void_p),('TargetAlias',W.LPWSTR),('UserName',W.LPWSTR)]
        self.Credential=Credential;self.api=C.WinDLL('advapi32',use_last_error=True)
        pointer=C.POINTER(Credential)
        for name,args in {'CredReadW':[W.LPCWSTR,W.DWORD,W.DWORD,C.POINTER(pointer)],'CredWriteW':[pointer,W.DWORD],'CredDeleteW':[W.LPCWSTR,W.DWORD,W.DWORD]}.items():
            fn=getattr(self.api,name);fn.argtypes=args;fn.restype=W.BOOL
        self.api.CredFree.argtypes=[C.c_void_p];self.api.CredFree.restype=None

    def target(self,provider):return SERVICE.decode()+'.'+provider
    def get(self,provider):
        value=C.POINTER(self.Credential)()
        if not self.api.CredReadW(self.target(provider),1,0,C.byref(value)):
            if C.get_last_error()==1168:return ''
            raise ValueError('Accès au coffre Windows refusé.')
        try:return C.string_at(value.contents.CredentialBlob,value.contents.CredentialBlobSize).decode('utf-8')
        finally:self.api.CredFree(value)

    def set(self,provider,secret):
        raw=secret.encode();buf=(C.c_ubyte*len(raw)).from_buffer_copy(raw)
        if len(raw)>2560:raise ValueError('Clé trop longue pour le coffre Windows.')
        cred=self.Credential();cred.Type=1;cred.TargetName=self.target(provider);cred.CredentialBlobSize=len(raw);cred.CredentialBlob=C.cast(buf,C.POINTER(C.c_ubyte));cred.Persist=2;cred.UserName='SuxenAI'
        try:
            if not self.api.CredWriteW(C.byref(cred),0):raise ValueError('Enregistrement dans le coffre Windows refusé.')
        finally:C.memset(buf,0,len(raw))

    def delete(self,provider):
        if not self.api.CredDeleteW(self.target(provider),1,0) and C.get_last_error()!=1168:raise ValueError('Suppression du coffre Windows refusée.')


def credential_store():
    if sys.platform=='darwin':return MacKeychain()
    if sys.platform=='win32':return WindowsKeychain()
    raise ValueError('Coffre système indisponible : utilisez les variables d’environnement.')


def validate_provider(provider):
    if not isinstance(provider,str) or provider not in ENV:raise ValueError('Fournisseur inconnu.')
    return provider


def key(provider):
    validate_provider(provider)
    env=os.getenv(ENV[provider],'').strip()
    if env:return env
    if sys.platform not in ('darwin','win32'):return ''
    with LOCK:return credential_store().get(provider)


def status(provider):
    validate_provider(provider)
    if os.getenv(ENV[provider],'').strip():return {'configured':True,'source':'environment'}
    try:return {'configured':bool(key(provider)),'source':'keychain' if sys.platform in ('darwin','win32') else 'unavailable'}
    except ValueError:return {'configured':False,'source':'locked'}


def save(provider, secret):
    validate_provider(provider)
    if not isinstance(secret,str):raise ValueError('Clé invalide.')
    secret=secret.strip()
    if not 8<=len(secret)<=4096 or any(ord(c)<33 or ord(c)>126 for c in secret):
        raise ValueError('Clé invalide : coller uniquement le jeton.')
    with LOCK:credential_store().set(provider,secret)


def remove(provider):
    validate_provider(provider)
    with LOCK:credential_store().delete(provider)


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
