"""Regresní test aktualizace projektu (novy_projekt.py na existující složku) – záloha ručně upravených nástrojů (#79).

Nic nestahuje, pracuje v dočasné složce. Z kořene repozitáře:
  python3 -I tests/aktualizace/test_aktualizace.py skills/rodokmen
(na Windows `python -I -X utf8 …`)
"""
import glob, json, os, shutil, subprocess, sys, tempfile

SKILL = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "skills/rodokmen")
NP = os.path.join(SKILL, "tools", "novy_projekt.py")
ok = chyb = 0


def over(podminka, popis):
    global ok, chyb
    print(("OK   " if podminka else "CHYBA"), popis)
    ok, chyb = ok + bool(podminka), chyb + (not podminka)


def spust(projekt):
    r = subprocess.run([sys.executable, "-I", "-X", "utf8", NP, projekt], capture_output=True, text=True,
                       encoding="utf-8")
    if r.returncode:
        print(r.stdout, r.stderr)
    return r.stdout


def zalohy(projekt):
    return sorted(glob.glob(os.path.join(projekt, "pracovni", "zaloha_tools_*")))


tmp = tempfile.mkdtemp(prefix="test_aktualizace_")
try:
    p = os.path.join(tmp, "projekt")
    spust(p)
    otisky = json.load(open(os.path.join(p, "tools", ".otisky.json"), encoding="utf-8"))
    over("zapis.py" in otisky and "novy_projekt.py" not in otisky, "založení zapíše otisky nástrojů")
    over(not zalohy(p), "založení nic nezálohuje")

    vystup = spust(p)
    over(not zalohy(p) and "POZOR" not in vystup, "aktualizace beze změn nic nezálohuje")

    upraveny = os.path.join(p, "tools", "ramecek.py")
    with open(upraveny, "a", encoding="utf-8") as f:
        f.write("# vlastní úprava\n")
    vlastni = os.path.join(p, "tools", "muj_nastroj.py")
    with open(vlastni, "w", encoding="utf-8") as f:
        f.write("print('můj')\n")
    vystup = spust(p)
    z = zalohy(p)
    over(len(z) == 1 and os.listdir(z[0]) == ["ramecek.py"], "ručně upravený nástroj je v zaloha_tools_*")
    over(z and "# vlastní úprava" in open(os.path.join(z[0], "ramecek.py"), encoding="utf-8").read(),
         "záloha obsahuje úpravu")
    over(open(upraveny, "rb").read() == open(os.path.join(SKILL, "tools", "ramecek.py"), "rb").read(),
         "nástroj má po aktualizaci verzi ze skillu")
    over("POZOR" in vystup and "tools/ramecek.py" in vystup, "výpis upozorní na upravený nástroj")
    over(open(vlastni, encoding="utf-8").read() == "print('můj')\n", "vlastní nástroj zůstal beze změny")

    # nástroj, který jen změnil skill (stará verze z minula, otisk sedí) – přepíše se bez zálohy
    for d in z:
        shutil.rmtree(d)
    o = json.load(open(os.path.join(p, "tools", ".otisky.json"), encoding="utf-8"))
    stara = b"# stara verze ze skillu\n"
    with open(os.path.join(p, "tools", "mista.py"), "wb") as f:
        f.write(stara)
    import hashlib
    o["mista.py"] = hashlib.sha256(stara).hexdigest()
    with open(os.path.join(p, "tools", ".otisky.json"), "w", encoding="utf-8") as f:
        json.dump(o, f)
    vystup = spust(p)
    over(not zalohy(p) and "POZOR" not in vystup, "starou verzi ze skillu (otisk sedí) přepíše bez zálohy")

    # projekt ze starší verze bez otisků: liší-li se nástroj, zazálohuje se pro jistotu
    os.remove(os.path.join(p, "tools", ".otisky.json"))
    with open(os.path.join(p, "tools", "vyrez.py"), "a", encoding="utf-8") as f:
        f.write("# starší verze\n")
    vystup = spust(p)
    z = zalohy(p)
    over(len(z) == 1 and os.listdir(z[0]) == ["vyrez.py"] and "otisky" in vystup,
         "bez otisků zálohuje lišící se nástroj a vysvětlí proč")
    over(os.path.exists(os.path.join(p, "tools", ".otisky.json")), "po aktualizaci otisky zase jsou")
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print(f"\n{ok} z {ok + chyb}")
sys.exit(1 if chyb else 0)
