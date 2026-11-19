"""Adds Morph transitions, auto-playing entrance animations and font fixes to the pptxgenjs output."""
import re, sys, zipfile, shutil

SRC, DST = sys.argv[1], sys.argv[2]

def set_vis(i, spid):
    return (f'<p:set><p:cBhvr><p:cTn id="{i}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:to><p:strVal val="visible"/></p:to></p:set>')

def fx(i, spid, filt, dur):
    return (f'<p:animEffect transition="in" filter="{filt}"><p:cBhvr><p:cTn id="{i}" dur="{dur}"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl></p:cBhvr></p:animEffect>')

def prop(i, spid, attr, frm, to, dur):
    return (f'<p:anim calcmode="lin" valueType="num"><p:cBhvr additive="base"><p:cTn id="{i}" dur="{dur}" decel="100000" fill="hold"/>'
            f'<p:tgtEl><p:spTgt spid="{spid}"/></p:tgtEl><p:attrNameLst><p:attrName>{attr}</p:attrName></p:attrNameLst></p:cBhvr>'
            f'<p:tavLst><p:tav tm="0"><p:val><p:strVal val="{frm}"/></p:val></p:tav>'
            f'<p:tav tm="100000"><p:val><p:strVal val="{to}"/></p:val></p:tav></p:tavLst></p:anim>')

# effect -> (presetID, subtype, builder)
def build_effect(ids, spid, effect, delay, dur):
    nid = lambda: next(ids)
    outer = nid()
    kids = [set_vis(nid(), spid)]
    if effect == "fade":
        pid, sub = 10, 0; kids.append(fx(nid(), spid, "fade", dur))
    elif effect == "rise":
        pid, sub = 42, 0
        kids += [fx(nid(), spid, "fade", dur), prop(nid(), spid, "ppt_x", "#ppt_x", "#ppt_x", dur), prop(nid(), spid, "ppt_y", "#ppt_y+0.08", "#ppt_y", dur)]
    elif effect in ("slideL", "slideR"):
        pid, sub = 2, (2 if effect == "slideL" else 8)
        off = "+0.06" if effect == "slideL" else "-0.06"
        kids += [fx(nid(), spid, "fade", dur), prop(nid(), spid, "ppt_x", f"#ppt_x{off}", "#ppt_x", dur), prop(nid(), spid, "ppt_y", "#ppt_y", "#ppt_y", dur)]
    elif effect == "zoom":
        pid, sub = 53, 16
        kids += [prop(nid(), spid, "ppt_w", "0", "#ppt_w", dur), prop(nid(), spid, "ppt_h", "0", "#ppt_h", dur), fx(nid(), spid, "fade", dur)]
    elif effect == "grow":
        pid, sub = 22, 4; kids.append(fx(nid(), spid, "wipe(up)", dur))
    elif effect == "wipe":
        pid, sub = 22, 8; kids.append(fx(nid(), spid, "wipe(right)", dur))
    elif effect == "wipeR":
        pid, sub = 22, 2; kids.append(fx(nid(), spid, "wipe(left)", dur))
    else:
        raise ValueError(effect)
    return (f'<p:par><p:cTn id="{outer}" presetID="{pid}" presetClass="entr" presetSubtype="{sub}" fill="hold" nodeType="withEffect">'
            f'<p:stCondLst><p:cond delay="{delay}"/></p:stCondLst><p:childTnLst>{"".join(kids)}</p:childTnLst></p:cTn></p:par>')

def timing(items):
    def counter():
        n = 5
        while True:
            yield n; n += 1
    ids = counter()
    effects = "".join(build_effect(ids, spid, e, d, dur) for spid, e, d, dur in items)
    return ('<p:timing><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot"><p:childTnLst>'
            '<p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq"><p:childTnLst>'
            '<p:par><p:cTn id="3" fill="hold"><p:stCondLst><p:cond delay="indefinite"/><p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
            '<p:par><p:cTn id="4" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
            f'{effects}'
            '</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>'
            '</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst>'
            '<p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl><p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>'
            '</p:childTnLst></p:cTn></p:par></p:tnLst></p:timing>')

TRANSITION = ('<mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006">'
              '<mc:Choice xmlns:p159="http://schemas.microsoft.com/office/powerpoint/2015/09/main" Requires="p159">'
              '<p:transition xmlns:p14="http://schemas.microsoft.com/office/powerpoint/2010/main" spd="slow" p14:dur="1600"><p159:morph option="byObject"/></p:transition>'
              '</mc:Choice><mc:Fallback><p:transition spd="slow"><p:fade/></p:transition></mc:Fallback></mc:AlternateContent>')

zin = zipfile.ZipFile(SRC)
zout = zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED)
total = 0
for item in zin.infolist():
    if item.filename.endswith('/'):
        continue
    data = zin.read(item.filename)
    if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
        x = data.decode("utf-8")
        items, k = [], 0
        def rename(m):
            global k
            spid, name = m.group(1), m.group(2)
            _, eff, delay, dur, _n = name.split("|")
            items.append((spid, eff, int(delay), int(dur)))
            return f'<p:cNvPr id="{spid}" name="{eff.capitalize()} {len(items)}"'
        x = re.sub(r'<p:cNvPr id="(\d+)" name="(anim\|[^"]*)"', rename, x)
        # objects that pptxgenjs gave the descr attr too
        items.sort(key=lambda t: t[2])
        tail = TRANSITION + (timing(items) if items else "")
        x = x.replace("</p:clrMapOvr>", "</p:clrMapOvr>" + tail, 1)
        assert tail in x, item.filename
        total += len(items)
        data = x.encode("utf-8")
    if item.filename.startswith("ppt/slides/slide") or item.filename.startswith("ppt/slideLayouts/") or item.filename.startswith("ppt/slideMasters/"):
        x = data.decode("utf-8")
        for f in ("JetBrains Mono", "Orbitron", "Orbitron Black", "Orbitron Medium"):
            x = x.replace(f'<a:cs typeface="{f}"', '<a:cs typeface="Vazirmatn"')
        data = x.encode("utf-8")
    zout.writestr(item, data)
zout.close()
print("animations:", total)
