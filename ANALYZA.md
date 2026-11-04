# Rozbor skillu „rodokmen“ (verze 0.7.0)

Psáno pro laika. Kde se objeví technické slovo, je hned vysvětlené. Rozbor vychází z obsahu tohoto repozitáře
(stav ke commitu `e386dfa`, verze 0.7.0 ze 3. 11. 2026) a ze zkušeností z Jiřího projektu.

## 1. Co skill dělá – jednou větou a pak podrobněji

**Skill je návod pro Clauda, jak s člověkem bez zkušeností udělat rodokmen z českých matrik a postavit z něj
rodinný web.** Claude dělá technickou práci (hledá knihy v archivech, stahuje snímky, čte staré písmo, zapisuje
data, staví web), člověk dodává znalost rodiny, rozhoduje sporná místa a schvaluje, co jde ven.

Práce je rozdělená do fází (SKILL.md):

| Fáze | Co se děje |
|---|---|
| 0. Příprava | kontrola programů (Python, Node.js, ImageMagick, git), založení složky projektu, volitelně „hlídač sítě“ |
| 1. Rozhovor s rodinou | co ví rodina, dokumenty, import rodinného stromu (GEDCOM, záloha MyHeritage) |
| 2. Matriky | generace po generaci: najít knihu, stáhnout snímek, přečíst zápis, uložit výřez, přepis, překlad a osobu |
| 3. Zajímavosti a příběh | „svatba na poslední chvíli“, rod sto let v jednom domě…; článek „Příběh Novákových“ |
| 4. Web | statický web (Astro) s vějířem předků, mapou, kartami osob a výřezy zápisů |
| 5. Zveřejnění | Netlify nebo vlastní server, chráněné rodinnou otázkou |

## 2. Jak je postavený

```
skills/rodokmen/
  SKILL.md        hlavní návod pro Clauda (313 řádků) – načte se vždy, když skill běží
  VERZE           číslo verze; podle něj Claude pozná, že má nabídnout aktualizaci projektu
  reference/      podrobné návody, které Claude čte, až je potřebuje:
                  matriky.md (jak číst), portaly.md (archivy), data.md (formát dat), web.md, soukromi.md,
                  pribehy.md, playbook.md (metodika, anglicky, 714 řádků)
  tools/          32 malých programů v Pythonu a shellu (stahování z archivů, výřezy, kontrola dat, export webu)
  template/       šablona projektu: prázdná data, ukázková rodina Novákových, web v Astru
tests/brzda/      testy „brzdy“ a hlídače (nekopírují se uživatelům)
.claude-plugin/   aby šel skill nainstalovat jako plugin
```

**Důležitý princip:** skill sám nic „neumí“ – je to text. Claude ho čte a podle něj spouští nástroje.
Nástroje se při založení projektu **zkopírují do projektu** (`~/Rodokmen/tools/`), takže projekt je samostatný.
To má výhodu (projekt funguje, i když se skill změní) a nevýhodu (při aktualizaci se kopie přepisují – viz #79).

**Data projektu** jsou obyčejné soubory ve složce `data/`:
- `osoby.py` – předci očíslovaní Kekulého čísly (1 = výchozí osoba, otec = 2n, matka = 2n+1), stav údaje
  (`doc` = přečteno v matrice, `prob` = pravděpodobné, `fam` = od rodiny, `mh` = cizí strom, `unk`),
- `zaznamy.json`, `svazky.json`, `prepisy.json`, `zvyrazneni.json` – zápisy z matrik, knihy, přepisy, rámečky,
- `research_log.md` – deník všech hledání, i neúspěšných,
- `web.json` – nastavení webu (název, přihlašovací otázka, schválené citlivé texty).

Z dat se příkazem `npm run data` vyrobí web (`tools/export_web.py`) a `npm run build` ho postaví.

**Brzda `tools/slusne.py`** je srdce ohleduplnosti k archivům: všechny nástroje i vlastní skripty Clauda jdou přes
ni a ta drží společný limit pro celý počítač (1 dotaz za 2 s, obrázky 10 za s). Když archiv odpoví „moc rychle“
(429/503/403), brzda web zastaví na 30 minut až 8 hodin a nic se neopakuje. Volitelný **hlídač** (`hlidac_site.py`)
před každým příkazem Clauda zkontroluje, že síť nejde mimo brzdu. Nově (0.7.0) se stažené snímky ukládají do
společné **mezipaměti** (`~/.cache/rodokmen_snimky`), takže se stejný snímek nestahuje dvakrát.

## 3. Silná místa

1. **Poctivost k nejistotě.** Každý údaj má stav (`doc`/`prob`/`fam`/`mh`), každý zápis výřez snímku s rámečkem,
   přepis a překlad. Nejistá čtení se značí „(?)“. Rodokmen jde zpětně zkontrolovat – to je u AI zásadní.
2. **Ohleduplnost k archivům** je promyšlená a vynucená kódem (brzda, stopka, mezipaměť, zákaz `curl` v nastavení
   projektu, hlídač). Pravidla vznikla ze skutečných zablokování.
3. **Pravidla „naučená na skutečném projektu“** – hledat od nejmladšího zápisu, nikdy křest naslepo, ověřit
   ztotožnění místa podle panství, čtení pomocníků ověřit na snímku. To je cenné know-how.
4. **Bezpečná úprava dat** – `zapis.py` mění jen jednu položku a zachová formát; `kontrola.py` hlídá chyby
   i citlivé údaje (sebevraždy, nemoci…) před zveřejněním.
5. **Hezký výsledek pro rodinu** – vějíř, mapa, příběh rodu, zajímavosti; rodina to opravdu čte.
6. **Myslí na laika a na Windows** – česky, bez žargonu, podrobné pasti pro Windows (cp1250, alias `python3`,
   `convert`, winget).
7. **Ohleduplný tón** u smrti a hrobů, ochrana žijících lidí.

## 4. Slabá místa

1. **Hodně textu.** SKILL.md + reference mají přes 1 700 řádků. Claude musí hodně číst a pravidla se snadno
   „ztratí“ v dlouhé konverzaci. Některá pravidla se opakují na více místech (údržba = měnit na více místech).
2. **Data se upravují ručně v Pythonu.** `osoby.py` je program, ne tabulka. Pro jednu osobu chybí nástroj
   (jako `zapis.py` pro JSON) – Claude si píše vlastní skripty a riskuje rozbití formátu. Totéž `web.json`
   (seznam `citlive_schvaleno`): `zapis.py` ho neumí, ruční přepis rozbije odsazení nebo konce řádků (CRLF).
3. **Aktualizace projektu přepisovala `tools/` bez zálohy** (#79) – vlastní úpravy nástrojů se ztratily. *Opraveno
   v této větvi, viz níže.*
4. **Nejednotné souřadnice.** `vyrez.py` a `overit.py` berou zlomky celé stránky, `ramecek.py` zlomky výřezu.
   Plete to Clauda i člověka (#37). *Zlepšeno v této větvi.*
5. **Mnoho archivů už jen přes prohlížeč** (SOA Praha, Třeboň, MZA, Opava) – archivy od listopadu 2026 nástroje
   odmítají. Práce je pomalejší a závisí na doplňku Playwright.
6. **Testy jen pro brzdu a hlídač.** Ostatní nástroje (export webu, kontrola, import GEDCOM) automatické testy
   nemají; chyby se najdou až u uživatelů.
7. **Kód nástrojů je hustý** (dlouhé řádky, některé nástroje „na jeden řádek“ jako `overit.py`), opakuje se
   (funkce `magick()` je zkopírovaná v 11 souborech). Laik ho upravit nedokáže, správce ho musí měnit na více místech.
8. **Cloud (claude.ai / Claude Code na webu)** – v cloudovém prostředí skill není nainstalovaný a weby archivů
   nebývají v povolených doménách; skill s tím počítá jen okrajově (náhled webu).

## 5. Rizika

### Bezpečnost a soukromí
- **Data jsou citlivá** (osobní údaje rodiny). Zůstávají na počítači; při záloze na GitHub jen soukromý repozitář
  (README to říká).
- **Přihlášení na webu je lehké**: cookie s otiskem (SHA-256) odpovědi na rodinnou otázku, kontrolovaná na serveru
  (Netlify / nginx). Kdo zná odpověď nebo má cookie, vidí vše; cookie platí rok a nejde odvolat jinak než změnou
  odpovědi. README to poctivě přiznává – nedávat na web nic, co by vadilo, kdyby se to dostalo ven.
- **Žijící lidé** – ochrana je jen pokyn pro Clauda a kontrola citlivých slov, kód ji nevynucuje.
- **Hlídač sítě je textová heuristika**, ne neprůstřelná ochrana (sám to říká). Při vlastní chybě příkaz pustí.
- Nástroje nic neposílají ven kromě dotazů na archivy a OpenStreetMap (souřadnice obcí); poznámky pro správce
  posílá jen uživatel ručně. Dobré.

### Ohleduplnost k archivům
- Hlavní riziko je **zablokování IP adresy** (MZA blokovala celou síť na hodiny). Brzda ho výrazně snižuje, ale
  **v prohlížeči neplatí** – tam se Claude musí hlídat sám (5–10 s mezi stránkami).
- SOA Praha a SOA Třeboň od 2. 11. 2026 nástroj výslovně zakazují; skill to respektuje (nástroje vypnuté, brzda
  zastaví). Do budoucna je třeba hlídat podmínky dalších archivů (`robots.txt`).
- Víc projektů / pomocníků na jednom počítači sdílí jednu IP – brzda je proto společná pro celý počítač.

### Údržba
- Archivy mění weby a pravidla (eBadatelna, Třeboň během jednoho dne) – nástroje stárnou rychle.
- Číslo verze je na 4 místech (plugin.json, VERZE, 2× README) a pravidla na více místech v textu.
- Projekty uživatelů mají vlastní kopie nástrojů a šablony webu → každá aktualizace musí počítat se starším
  formátem (CLAUDE.md to připomíná).
- Jediný správce; skill se rychle vyvíjí (0.5 → 0.7 za pár dní).

### Windows
- Nejvíc pastí: `python3` je falešný alias z Microsoft Store, výstup v cp1250 bez `-X utf8`, `convert.exe` je jiný
  program, Git Bash vs. PowerShell u hooků, CRLF konce řádků u `.sh` i u dat. Skill to řeší pečlivě, ale je to křehké.
- `test_hlidac.py` na Windows pro 0.6.1+ zatím neověřený (tests/brzda/README.md).
- `pdftotext`/`pdftoppm` (potřebné pro soupis 1651) na Windows standardně nejsou.

## 6. Otevřené issues původního repozitáře

Všech 34 otevřených issues i s komentáři (stav 4. 11. 2026) dodal Jiří jako export z `gh`; z cloudu jsem k nim
přístup neměl. Odhad náročnosti: **malá** = hodina–dvě, jeden soubor; **střední** = víc souborů nebo web;
**velká** = nová funkce napříč daty, nástroji a webem.

### Co z issues vyplývá nejvíc
1. **Aktualizace projektu je nejčastější bolest.** Kromě #79 si na přepsané úpravy stěžují #36, #61 (komentář: zmizely
   úpravy `export_web.py`) a #69 (úprava webu zůstane jen v záloze). Návrh v #79 jde dál než moje oprava: projekt si
   má pamatovat původní šablonu a při aktualizaci **sloučit** změny po řádcích (jako `git merge-file`) – u nástrojů
   i webu. Autor #79 píše, že má rozpracovaný PR. Moje záloha nástrojů je bezpečný první krok, který se s takovým
   PR nevylučuje, ale je dobré se domluvit, ať nevzniknou dvě řešení.
2. **Hodně lidí má hotový kód a nabízí PR** (#14, #15, #32, #33, #36, #37, #40, #79, #80, #81, PR #42 k #43). Úzké
   místo je čas autora na kontrolu, ne nápady.
3. **Několik tichých chyb v datech** (web ukáže nesmysl a nic se nehlásí): #68 (strýc jako bratr vlastního otce),
   #74 (překlad pod klíčem `preklad` místo `cs` na webu chybí), #81 (bod na mapě 200 km jinde), #18 (odkaz do archivu
   na první stránku knihy). Jsou malé a mají velký užitek.

### Opravy nástrojů a dat (nejlepší poměr užitek / práce)
| Issue | Co (podle textu issue) | Náročnost | Stav |
|---|---|---|---|
| #79 | `tools/` se přepíše bez zálohy; web se slučuje jen ručně (13 souborů pokaždé, i když se šablona nezměnila); návrh tříverzového slučování, autor má rozpracovaný PR | malá (záloha) / střední–velká (slučování) | **záloha nástrojů hotová v této větvi**; slučování ne |
| #37 | `overit.py` nafukuje dlouhé výřezy (`1900x` → `1900x1900>`); `ebadatelna.py` zkracuje Retry-After; `kontrola.py` plané poplachy a chybí varování na prázdnou mapu; `ramecek.py` nápověda; `aron_img.py crop` zarovnaný na dlaždice; přepínač `--vylepsit` pro vybledlé snímky (hotový příkaz ImageMagicku v issue). Opravy overit/ebadatelna/kontrola má mhaluska jako PR | malá, po kouscích | **`ramecek.py` hotový**; zbytek ne (planý poplach „Novákovi“ je v 0.7.0 už opravený) |
| #18 | `aron_img.py link` dává do odkazu soubor typu PUBLISHED, prohlížeč ARONu ale stránku najde jen podle TILE → odkaz otevře první snímek knihy. Oprava je jeden řádek, ohlašovatel ji ověřil | malá | **v 0.7.0 pořád neopraveno** (`aron_img.py`, ř. 182) |
| #68 | komentář u `k` v `SIDE` svádí: `k` znamená „předek, jehož je sourozencem“, ne „ke kterému patří“ | malá (text + případně kontrola) | – |
| #74 | `kontrola.py` nehlásí přepis bez pole `cs`; `zapis.py prepisy` by ho měl odmítnout | malá | – |
| #81 | `mista.py` bere první výsledek OpenStreetMap (herna v Liberci místo vsi); návrh: jen sídla, vypsat okres, varovat při bodu > 50 km od ostatních; ohlašovatel pošle PR | malá–střední | – |
| #80 | `kontrola.py`: partner na sousedním čísle, sňatek po úmrtí, čísla domů proti přepisům; ohlašovatel pošle PR | střední | – |
| #54 | `zapis.py` neumí položku smazat; `policie_prihlasky.py karta` nad 20 vrací cizí kartu | malá–střední | – |
| #61 | otevřený web v Dockeru: nginx padá na „duplicate default map parameter“; přihlášení přes http v LAN nefunguje (`crypto.subtle`) | malá–střední | – |
| #50 | `export_web.py` padal na aliasu `SAME` bez vlastní položky | – | v 0.7.0 zřejmě opraveno |
| #25 | anglický audit 0.5.0 (staré obrázky na webu, kolize identifikátorů, import/export) | střední – nejdřív ověřit, co ještě platí | – |

### Web
| Issue | Co | Náročnost |
|---|---|---|
| #69 | stránka předka neukazuje jeho ostatní děti – v issue je hotový kód (2 řádky v `osoba/[slug].astro`) | malá |
| #17 | skrytá osoba jen s iniciálami a bez předků; issue vyjmenovává, kudy všude by mohla prosáknout (vějíř, výřezy, vyhledávání…) | střední–velká |
| #15 | víc příběhů rodů – chtějí to už dva uživatelé | střední |
| #36 | vlastní heslo pro každého, log návštěv, heslo mimo git, Synology – nabízen PR | střední–velká (bezpečnost) |
| #14 | „Putování rodu“ – vějíř podle krajů + mapa cest; uživatel to má hotové | velká |
| #16 | kronika v PDF, sépiová perokresba z fotek | velká (nejdřív jen návod) |
| #75 | veřejný `rodokmen.json` a index pro propojení badatelů; v komentářích upozornění na hranici 100 let a žijící děti | velká, citlivé na soukromí |

### Rodokmen jako celek, import/export, metodika
| Issue | Co | Náročnost |
|---|---|---|
| #33 | export do GEDCOM 5.5.1 se skrytím žijících a testem tam a zpět – hotový PR | střední (kontrola PR) |
| #32 | víc výchozích osob (sourozenci, děti dvou rodičů) – hotový PR, mění model dat (`OSOBY` vedle `P`) | velká |
| #34 | čtení a ověřování: povinný kontrolní zápis pro pomocníka, dávky do 20–25 snímků, nezávislé druhé čtení | malá–střední (návod), velmi užitečné |
| #27 | metodika GPS (Genealogical Proof Standard, 5 kroků dokazování) | střední (návod) |
| #43 | podpora Codexu a OMP (PR #42); v komentářích zkušenost, že Codex čte matriky hůř | střední (údržba navíc) |

### Archivy a prameny (hlavně návody)
| Issue | Co | Náročnost |
|---|---|---|
| #84 | soupis 1651 jako PDF, filiální vsi v knihách zemřelých, cloud | malá; **soupis a filiální vsi hotové**, cloud ne |
| #83 | FamilySearch jako náhrada za zablokované archivy (Třeboň, Praha), Matricula, OneDrive | střední (a posoudit podmínky FamilySearch) |
| #78 | lokální archiv celých knih z ARONu (84 GB ZIPů), past OneDrive „jen online“ | střední |
| #82 | koncepty žádostí archivům a úřadům jako odkaz do e-mailu + přehled žádostí | střední |
| #40 | vojenské prameny (Verlustlisten, VÚA–VHA, legie, pomníky) – nabízen PR | malá–střední |
| #35 | sčítání 1921, civilní matriky 1939–45 (Litoměřice), GenTeam, žádost datovou schránkou | malá |
| #70 | ZA Opava: ověření „jsem člověk“ jen v kartě Clauda, strop ~200–300 dotazů denně | malá |
| #21 | Kramerius (celý OCR text), MZA Acta Publica | malá – ověřit, co ještě platí |
| #30, #50, #54, #61, #63, #67, #74 | souhrnná „Poznámky z praxe“ – desítky drobností (Windows, MZA, Opava, Cloudflare, kurent, dějiny domu, mapa v čase…) | po bodech, většinou malé |

### Co z toho se týká Jiřího a co dál
#79 a #84 řeší tato větev (u #79 jen zálohu nástrojů). Nejlepší další kandidáti, všechny malé:
**#18** (odkaz do ARONu, jeden řádek), **#68** (komentář v `osoby.py`), **#74** (kontrola pole `cs`), **#69** (další děti
na stránce předka, kód je v issue) a zbytek **#37** (`--vylepsit` pro vybledlé snímky). Mimo issues: nástroj na
`web.json` → `citlive_schvaleno` a na úpravu jedné osoby v `osoby.py`.

## 7. Co jsem změnil

Vybral jsem tři věci s nejlepším poměrem užitek / náročnost: #79, soupis 1651 (#84) a dvě drobnosti (#37
a Jiřího hlášení k `ebadatelna.py`). Změny jsou na větvi `claude/cool-knuth-78o8mw` v Jiřího forku
(`george190321/rodokmen-skill`); do původního repozitáře nic nešlo, žádný pull request ani issue.

### a) Záloha upravených nástrojů při aktualizaci (#79)
- **Soubor:** `skills/rodokmen/tools/novy_projekt.py`
- **Proč:** aktualizace projektu přepsala `tools/*.py` vždy a bez zálohy – vlastní úpravy se ztratily
  (u webu se zálohovalo, u nástrojů ne). Navíc `pracovni/` není v gitu projektu, takže ani git by je nezachránil,
  pokud nebyly uložené.
- **Jak:** při každém kopírování si projekt zapíše „otisky“ nástrojů (`tools/.otisky.json` – kontrolní součet
  SHA-256 obsahu, jak ho skill nakopíroval). Při aktualizaci:
  - nástroj beze změny → nic,
  - nástroj se liší, ale otisk sedí (je to jen starší verze ze skillu) → přepíše se bez zálohy,
  - nástroj se liší od otisku (někdo ho upravil) → **nejdřív se uloží do `pracovni/zaloha_tools_<datum>/`**,
    přepíše se a výpis to ohlásí s „POZOR“ a radou, jak úpravy převzít,
  - projekt ze starší verze bez otisků → pro jistotu se zazálohuje každý lišící se nástroj (s vysvětlením),
  - vlastní nástroje, které ve skillu nejsou, zůstanou beze změny (tak to bylo i dřív).
- **Dokumentace:** `SKILL.md` (aktualizace na začátku konverzace) a `reference/web.md` (Aktualizace staršího projektu).
- **Test:** nový `tests/aktualizace/test_aktualizace.py` (11 z 11 OK): založení, aktualizace beze změn, upravený
  nástroj, vlastní nástroj, starší verze se sedícím otiskem, projekt bez otisků. Ručně: projekt založený verzí 0.7.0
  (`git archive` výchozího stavu) s upraveným `kontrola.py` → nová verze zazálohovala 4 lišící se nástroje,
  `kontrola.py` i `export_web.py` pak na ukázkových datech prošly. Stávající `tests/brzda/test_hlidac.py`
  (importuje `novy_projekt.py`) 71 z 71 OK.

### b) Soupis poddaných 1651 a filiální vsi (#84)
- **Soubory:** `skills/rodokmen/reference/portaly.md` (Starší prameny), `skills/rodokmen/reference/matriky.md`
- **Proč:** návod měl o soupisu dvě věty; v praxi se ztrácel čas hledáním ve svazcích, kde panství chybí,
  a hledáním v textu z `pdftotext` s rozbitou diakritikou.
- **Co je nově v návodu:** svazky jsou volně zdarma jako PDF; **nejdřív seznam zachovaných panství v úvodu**;
  `pdftotext` rozbíjí diakritiku → hledat část jména bez háčků a čárek a varianty pravopisu; stránku číst
  jako obrázek (`pdftoppm`, nebo přímo z PDF); jak soupis zapsat do dat a proč je ztotožnění s předkem obvykle
  jen `prob`; co dělat, když poppler chybí (Windows). V `matriky.md` přibyla věta, že kniha zemřelých mateřské
  fary nemusí zapisovat filiální vsi.
- **Upřesněno podle textu #84:** jak přesně `pdftotext` diakritiku rozbije (ě → ì, ř → ø, š a ž zmizí), kde edice
  na webu NA jsou, rejstřík míst na konci svazku, německé tvary jmen, řazení podle panství, 3–4 vzorky knihy zemřelých.
- **Test:** jen textová změna; porovnáno s `playbook.md` a s textem #84. Weby archivů ani NA jsem neotvíral.

### c) Drobné opravy nástrojů (#37 a hlášení k `ebadatelna.py`)
- **`ramecek.py` + `vyrez.py`:** nová volba `ramecek.py <klíč> --stranka x0,y0,x1,y1` – souřadnice na **celé
  stránce**, stejně jako u `vyrez.py` a `overit.py`. `vyrez.py` si oblast výřezu zapamatuje
  (`pracovni/vyrezy_oblasti.json`) a `ramecek.py` souřadnice sám přepočítá; u starších výřezů jde oblast zadat
  `--vyrez`. Nápověda teď velkými písmeny říká, že bez `--stranka` jde o zlomky VÝŘEZU, a po zápisu to připomene.
  Původní volání funguje beze změny (zpětně kompatibilní, formát `zvyrazneni.json` se nemění).
- **`ebadatelna.py snimek / a-snimek`** (není v #37, je to Jiřího zkušenost – #37 řeší u eBadatelny jiné věci):
  výstup musí mít příponu `.jpg`/`.jpeg`/`.png`; `snimek 123 5 nahled`
  skončí srozumitelnou chybou místo souboru jménem „nahled“.
- **Test (`python3 -I`, s ImageMagickem 6):** výřez 0.2,0.5,0.6,0.7 a rámeček na stránce 0.3,0.55,0.5,0.6 →
  ve výřezu 0.25,0.25,0.75,0.5 (správně); rámeček mimo výřez, chybějící oblast, ruční `--vyrez`, pixely místo
  zlomků, `--vyrez` bez `--stranka` – vše dá srozumitelnou hlášku. `ebadatelna.py snimek 123 5 nahled` i
  `a-snimek 123 5 0,0,0.5,0.5` skončí chybou, správné volání dojde až ke kontrole mezipaměti (bez sítě).
- **Dokumentace:** `SKILL.md` (krok 5.4 a tabulka nástrojů).

### Co zbývá
- **Vydání verze** nedělám – o čísle verze, CHANGELOGu a vydání rozhoduje správce (postup v `CLAUDE.md`). Návrh
  textu do CHANGELOGu:
  > **Nové** – Aktualizace projektu zazálohuje ručně upravené nástroje do `pracovni/zaloha_tools_<datum>/` (#79).
  > `ramecek.py --stranka` bere souřadnice celé stránky (#37). **Opravy** – `ebadatelna.py snimek` bez výstupního
  > souboru už nevytvoří soubor „nahled“. **Návody** – soupis poddaných 1651: nejdřív seznam zachovaných
  > panství, rozbitá diakritika z pdftotext (#84); kniha zemřelých a filiální vsi.
- `npm install / data / build` při zkoušce aktualizace jsem nespouštěl – šablona webu (`template/web/`) se nemění,
  `export_web.py` na ukázce prošel.
- Na Windows a macOS neotestováno (zkoušeno na Linuxu, Python 3.13).
- `pracovni/vyrezy_oblasti.json` není v gitu projektu (`pracovni/` je v `.gitignore`); když se smaže, stačí `--vyrez`.
- #79 navrhuje plné slučování (tři verze souboru) a jeho autor má rozpracovaný PR – moje záloha je jen první krok.
- Další kandidáti: viz konec sekce 6 (#18, #68, #74, #69, zbytek #37) a návod pro cloud (#84).

### Jak si změny prohlédnout
```bash
git diff e386dfa -- skills tests
```
