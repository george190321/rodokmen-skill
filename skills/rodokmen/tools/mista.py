#!/usr/bin/env python3
"""Místa předků pro mapu na webu (data/mista.json).

Použití:
  mista.py pridej "Název" ["regulární výraz"] ["dotaz pro vyhledání"]
      přidá obec; výraz se hledá v údajích osob (výchozí = prvních 5 písmen názvu, aby sedělo i skloňování),
      dotaz pro OpenStreetMap (výchozí = "Název, Česko", když nic nenajde, zkusí Slovensko a další sousední země);
      historickou část obce, kterou mapa nezná, zadej jako celou obec; u víceznačných názvů (Podolí, Dub) přidej sousední obec:
      "Podolí, Odlochovice" – a ve výpisu vždy zkontroluj okres
  mista.py
      dohledá souřadnice u míst, která je ještě nemají (OpenStreetMap Nominatim, 1 dotaz za sekundu),
      a vypíše seznam. Když bod nesedí, opravte lat/lon v data/mista.json ručně.
U nově nalezeného místa vypíše okres a kraj, další stejnojmenné obce a varuje, když je bod daleko od ostatních míst
projektu. Hledá jen sídla (obce, vsi, osady); když žádné nenajde, vezme jiný výsledek a označí ho „NENÍ OBEC“.

Položka může mít "hypoteza": true a "rod": <Kekulé 8–15> – pak se na mapě ukáže jako hypotéza bez osob.
"""
import json, math, os, re, sys, time, urllib.parse, urllib.request
import os as _os, sys as _sys; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__))); import slusne  # noqa: E402 – brzda proti zablokování archivem (společný limit dotazů, tools/slusne.py)
for _s in (sys.stdout, sys.stderr):   # UTF-8 výstup i na Windows bez -X utf8 (cp1250 neumí třeba „→“)
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mista.json")


DALEKO_KM = 50   # bod dál od všech ostatních míst projektu je podezřelý (stejnojmenná obec jinde, #81)


def _hledej(q, zeme, sidla):
    par = {"q": q, "format": "json", "limit": 5, "addressdetails": 1} | ({"countrycodes": zeme} if zeme else {}) \
        | ({"featureType": "settlement"} if sidla else {})
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(par)
    req = urllib.request.Request(url, headers={"User-Agent": "rodokmen-skill/1.0 (family genealogy map, occasional geocoding)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)
    time.sleep(1.1)
    return res


def oblast(r):
    """Okres a kraj z adresy Nominatimu („okres Chrudim, Pardubický kraj“)."""
    a = r.get("address") or {}
    return ", ".join(x for x in (a.get("county"), a.get("state"), a.get("country")) if x)


def geocode(q, zeme=None):
    """(lat, lon, popis, další stejnojmenná sídla, je_obec) nebo None. Nejdřív jen sídla – bez toho Nominatim vrací
    i hospody a ulice („Andělka, Liberec“ = herna v Liberci, #81)."""
    res, obec = _hledej(q, zeme, True), True
    if not res:
        res, obec = _hledej(q, zeme, False), False
    if not res:
        return None
    r = res[0]
    dalsi = [oblast(x) or x.get("display_name", "")[:60] for x in res[1:]]
    return round(float(r["lat"]), 4), round(float(r["lon"]), 4), r["display_name"], oblast(r), dalsi, obec


def km(a, b):
    """Vzdálenost dvou bodů (lat, lon) v km."""
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def main():
    cache = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    if len(sys.argv) > 2 and sys.argv[1] == "pridej":
        name = sys.argv[2]
        stem = re.escape(name.split()[0][:5]) if len(name.split()) == 1 else re.escape(name)
        cache[name] = dict(cache.get(name, {}), re=sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else stem,
                           dotaz=sys.argv[4] if len(sys.argv) > 4 else f"{name}, Česko")
    for name, e in cache.items():
        if "lat" not in e:
            try:
                g = geocode(e.get("dotaz") or f"{name}, Česko")
            except OSError as chyba:   # bez sítě: uložit, co je, a srozumitelně skončit
                json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
                sys.exit(f"OpenStreetMap neodpovídá ({chyba}) – místa jsou uložená bez souřadnic, "
                         "spusť `mista.py` znovu později.")
            if not g and e.get("dotaz", f"{name}, Česko") == f"{name}, Česko":   # výchozí dotaz: zkus sousední země
                g = geocode(name, "sk,pl,at,de,hu")
                if g:
                    print("MIMO ČESKO:", name, "→", g[2][:80], "– zkontroluj, že je to ono")
            if g:
                e["lat"], e["lon"], e["osm"] = g[:3]
                print(f"NOVÉ: {name} → {g[3] or g[2][:80]}" + ("" if g[5] else "  – NENÍ OBEC (hospoda, ulice…?), zkontroluj"))
                if g[4]:
                    print(f"  stejnojmenné: {'; '.join(g[4])} – je to ta správná? Jinak dotaz se sousední obcí nebo okresem")
                ostatni = [(o["lat"], o["lon"]) for n, o in cache.items() if n != name and "lat" in o]
                if ostatni:
                    d = min(km((e["lat"], e["lon"]), o) for o in ostatni)
                    if d > DALEKO_KM:
                        print(f"  POZOR: {d:.0f} km od nejbližšího místa projektu – opravdu tahle obec, ne stejnojmenná jinde?")
            else:
                print("NENALEZENO:", name, "– upravte 'dotaz' nebo doplňte lat/lon ručně")
    json.dump(cache, open(OUT, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    for n, e in cache.items():
        print(f"{n:28} {e.get('lat', '?'):>8} {e.get('lon', '?'):>8}  hledá „{e.get('re')}“  {e.get('osm', '')[:60]}")


if __name__ == "__main__":
    main()
