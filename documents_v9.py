"""Bounded local text extraction; ZIP members are read, never extracted or executed."""
import base64
import io
from pathlib import PurePath
import re
import zipfile
import xml.etree.ElementTree as ET

MAX_UPLOAD=6_000_000
MAX_XML=8_000_000
MAX_TEXT=80_000


def xml(archive,name):
    info=archive.getinfo(name)
    if info.file_size>MAX_XML:raise ValueError('Document décompressé trop volumineux')
    with archive.open(info) as stream:raw=stream.read(MAX_XML+1)
    if len(raw)>MAX_XML or re.search(br'<!\s*(DOCTYPE|ENTITY)',raw,re.I):raise ValueError('XML non autorisé')
    return ET.fromstring(raw)


def extract(filename,encoded):
    if not isinstance(filename,str) or not isinstance(encoded,str) or len(encoded)>MAX_UPLOAD*1.4:raise ValueError('Fichier limité à 6 Mo')
    try:raw=base64.b64decode(encoded,validate=True)
    except ValueError:raise ValueError('Fichier illisible') from None
    if len(raw)>MAX_UPLOAD:raise ValueError('Fichier limité à 6 Mo')
    suffix=PurePath(filename).suffix.lower()
    try:
        if suffix in ('.txt','.md','.csv','.json'):
            text=raw.decode('utf-8-sig')
        elif suffix=='.pdf':
            from pypdf import PdfReader
            reader=PdfReader(io.BytesIO(raw))
            if reader.is_encrypted or len(reader.pages)>100:raise ValueError('PDF chiffré ou supérieur à 100 pages')
            parts=[];size=0
            for page in reader.pages:
                part=page.extract_text() or '';parts.append(part);size+=len(part.encode())
                if size>MAX_TEXT:break
            text='\n\n'.join(parts)
        elif suffix in ('.docx','.xlsx'):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                if len(z.infolist())>2000:raise ValueError('Archive trop complexe')
                if suffix=='.docx':
                    root=xml(z,'word/document.xml')
                    text='\n'.join(''.join(t.text or '' for t in p.iter() if t.tag.endswith('}t')) for p in root.iter() if p.tag.endswith('}p'))
                else:
                    strings=[]
                    if 'xl/sharedStrings.xml' in z.namelist():
                        strings=[''.join(t.text or '' for t in si.iter() if t.tag.endswith('}t')) for si in xml(z,'xl/sharedStrings.xml') if si.tag.endswith('}si')]
                    lines=[];size=0
                    sheets=sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n))
                    for sheet in sheets[:30]:
                        lines.append(sheet.rsplit('/',1)[-1]);root=xml(z,sheet)
                        for row in (r for r in root.iter() if r.tag.endswith('}row')):
                            cells=[]
                            for cell in row:
                                value=next((v.text or '' for v in cell if v.tag.endswith('}v')),'')
                                if cell.get('t')=='s' and value.isdigit() and int(value)<len(strings):value=strings[int(value)]
                                elif cell.get('t')=='inlineStr':value=''.join(t.text or '' for t in cell.iter() if t.tag.endswith('}t'))
                                cells.append(cell.get('r','')+': '+value)
                            line='\t'.join(cells);lines.append(line);size+=len(line.encode())
                            if size>MAX_TEXT:break
                        if size>MAX_TEXT:break
                    text='\n'.join(lines)
        else:raise ValueError('Formats : PDF, DOCX, XLSX, TXT, MD, CSV, JSON')
    except ImportError:raise ValueError('Lecture PDF disponible dans la version Mac autonome (pypdf requis)') from None
    except (zipfile.BadZipFile,KeyError,ET.ParseError,UnicodeError):raise ValueError('Document illisible ou format non reconnu') from None
    text=text.replace('\x00','').strip()
    if not text:raise ValueError('Aucun texte extrait (PDF scanné : OCR non inclus)')
    if len(text.encode())>MAX_TEXT:text=text.encode()[:MAX_TEXT-60].decode('utf-8','ignore')+'\n[Texte tronqué à 80 Ko]'
    return text
