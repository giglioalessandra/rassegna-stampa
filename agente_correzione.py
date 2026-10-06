import os
import platform
import subprocess
from pathlib import Path

# Librerie AI e Documenti
from google import genai
from google.genai import types
import fitz # PyMuPDF, per leggere i PDF
from docx import Document # Per leggere i file .docx

# Notifiche
from notifypy import Notify # Per i pop-up di notifica


# --- CONFIGURAZIONE E INIZIALIZZAZIONE ---

# 1. Configurazione del Percorso
# BUG FIX: il percorso era relativo alla cartella da cui si lancia lo script
# ("./file_da_correggere"): lanciandolo da un'altra posizione creava una
# cartella vuota altrove e non trovava i file. Ora è ancorato alla posizione
# dello script stesso.
CARTELLA_DI_LAVORO = Path(__file__).resolve().parent / "file_da_correggere"

# NOVITÀ: cartella (dentro CARTELLA_DI_LAVORO) che conterrà un file di
# trascrizione per ogni file audio/video, e nome dell'alias sul Desktop.
NOME_CARTELLA_TRASCRIZIONI = "trascrizioni"
NOME_ALIAS_TRASCRIZIONI = "Trascrizioni"
ESTENSIONI_AUDIO = ['.mp3', '.wav', '.m4a', '.mp4', '.ogg', '.flac']

# 2. Configurazione AI
LIVELLO_L2 = "Italiano L2, livello A2 consolidato"

# Inizializzazione Client AI
client_gemini = None
GEMINI_MODEL = 'gemini-2.5-flash'

# Controllo esplicito della chiave API: genai.Client() NON verifica la chiave
# alla creazione, quindi senza questo controllo l'errore emergeva solo
# durante le chiamate, mascherato come generico "ERRORE DI ELABORAZIONE".
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    print("=" * 60)
    print("ERRORE: la variabile d'ambiente GEMINI_API_KEY non è impostata.")
    print("Impostala nel terminale prima di lanciare lo script, ad esempio:")
    print('  export GEMINI_API_KEY="LA_TUA_CHIAVE"')
    print("(il comando export vale solo per la sessione corrente del terminale)")
    print("=" * 60)
else:
    try:
        client_gemini = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"ATTENZIONE: Client Gemini non inizializzato: {e}")


# --- FUNZIONI UTILITY PER L'INPUT ---

def get_desktop_path() -> Path | None:
    """Restituisce il percorso della cartella Desktop."""
    system = platform.system()
    try:
        if system == 'Windows':
            return Path(os.path.join(os.environ['USERPROFILE'], 'Desktop'))
        elif system == 'Darwin': # macOS
            return Path.home() / 'Desktop'
        else:
            return Path.home() / 'Desktop'
    except Exception:
        return None

def leggi_file_word(file_path: Path) -> str:
    document = Document(file_path)
    testo_completo = ""
    for paragraph in document.paragraphs:
        testo_completo += paragraph.text + "\n"
    return testo_completo.strip()

def leggi_file_pdf(file_path: Path) -> str:
    testo_completo = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            testo_completo += page.get_text() + "\n"
    return testo_completo.strip()

def chiama_api_trascrizione(file_path: Path) -> str:
    """Trascrive file audio/video."""
    if not client_gemini: return "ERRORE: Client non inizializzato."

    print(f"-> Trascrizione audio/video: {file_path.name}")
    audio_file_uploaded = None
    try:
        audio_file_uploaded = client_gemini.files.upload(file=file_path)
        prompt = """Trascrivi integralmente l'audio in italiano. Non fare correzioni, non cambiare le parole, non aggiungere commenti. Restituisci SOLO il testo trascritto."""
        response = client_gemini.models.generate_content(model=GEMINI_MODEL, contents=[prompt, audio_file_uploaded])
        # Il testo può essere None se la risposta è bloccata/vuota
        return (response.text or "").strip()
    except Exception as e:
        return f"ERRORE DI TRASCRIZIONE: {e}"
    finally:
        if audio_file_uploaded:
            client_gemini.files.delete(name=audio_file_uploaded.name)

def chiama_api_visione(file_path: Path) -> str:
    """Estrae testo da immagini e lo corregge (OCR + Correzione)."""
    if not client_gemini: return "ERRORE: Client non inizializzato."

    print(f"-> Analisi immagine (OCR): {file_path.name}")
    image_uploaded = None
    try:
        image_uploaded = client_gemini.files.upload(file=file_path)

        # Usiamo lo stesso formato di output di chiama_api_correzione per coerenza
        prompt = f"""
        Analizza l'immagine allegata, estrai il testo scritto (OCR) e correggilo come esperto in Italiano L2 (livello {LIVELLO_L2}).

        Formato di output richiesto:

        --- INIZIO OUTPUT CORREZIONE ---
        **Tipo File:** Immagine (OCR)

        **Testo Originale/Trascrizione:**
        [Inserisci qui il testo estratto dall'immagine esattamente come appare]

        **Testo Corretto ({LIVELLO_L2}):**
        Bene! Attenzione però: [Inserisci qui il testo corretto aderente al livello B1]

        **Errori Segnalati (Rilevanti per A2/B1):**
        [Lista puntata di 3-5 errori con spiegazione concisa]
        --- FINE OUTPUT CORREZIONE ---
        """

        response = client_gemini.models.generate_content(model=GEMINI_MODEL, contents=[prompt, image_uploaded])
        return response.text.replace('```markdown', '').replace('```', '').strip()
    except Exception as e:
        return f"ERRORE ANALISI IMMAGINE: {e}"
    finally:
        if image_uploaded:
            client_gemini.files.delete(name=image_uploaded.name)


# --- FUNZIONI DI ELABORAZIONE ---

def chiama_api_correzione(testo: str, is_audio: bool) -> str:
    """Correzione per testi puri o trascrizioni."""
    if not client_gemini: return "ERRORE: Client non inizializzato."

    prompt = f"""
    Sei un correttore linguistico esperto in Italiano L2. Livello: {LIVELLO_L2}.
    Correggi il testo senza superare il livello B1.

    Formato di output richiesto:
    --- INIZIO OUTPUT CORREZIONE ---
    **Tipo File:** {'Audio Trascritto' if is_audio else 'Testo Originale'}

    **Testo Originale/Trascrizione:**
    {testo}

    **Testo Corretto ({LIVELLO_L2}):**
    Bene! Attenzione però: [Testo corretto]

    **Errori Segnalati (Rilevanti per A2/B1):**
    [Lista puntata di 3-5 errori]
    --- FINE OUTPUT CORREZIONE ---
    """
    try:
        response = client_gemini.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=types.GenerateContentConfig(temperature=0.0))
        return response.text.replace('```markdown', '').replace('```', '').strip()
    except Exception as e:
        return f"ERRORE API CORREZIONE: {e}"


# --- FUNZIONI PER LE TRASCRIZIONI (NOVITÀ) ---

def salva_trascrizione(file_audio: Path, trascrizione: str, cartella: Path, nomi_usati: set) -> Path | None:
    """Salva la trascrizione di un file audio in un file TXT dedicato.

    Restituisce il percorso del file creato, oppure None se la trascrizione
    non è valida (errore API o testo vuoto): in quel caso non si crea nessun
    file, per non spacciare un messaggio d'errore per una trascrizione.
    """
    if not trascrizione or trascrizione.startswith("ERRORE"):
        print(f"   [!] Trascrizione non salvata per {file_audio.name}")
        return None

    nome = f"{file_audio.stem}_trascrizione.txt"
    # Due file con lo stesso nome ma estensione diversa (es. a.mp3 e a.wav)
    # non devono sovrascriversi a vicenda.
    if nome in nomi_usati:
        nome = f"{file_audio.stem}_{file_audio.suffix.lstrip('.').lower()}_trascrizione.txt"
    nomi_usati.add(nome)

    cartella.mkdir(exist_ok=True)
    destinazione = cartella / nome
    with open(destinazione, 'w', encoding='utf-8') as f:
        f.write(trascrizione + "\n")
    print(f"   Trascrizione salvata: {destinazione.name}")
    return destinazione

def crea_alias_cartella(cartella: Path, desktop: Path | None, nome_alias: str) -> bool:
    """Crea sul Desktop un alias/collegamento alla cartella indicata.

    macOS: alias del Finder; Windows: collegamento .lnk; Linux: link simbolico.
    Se l'alias esiste già viene sostituito. Restituisce True se creato.
    """
    if not desktop or not desktop.exists():
        print("   [!] Desktop non trovato: alias non creato.")
        return False

    cartella = cartella.resolve()
    system = platform.system()

    try:
        if system == 'Darwin':
            alias_path = desktop / nome_alias
            # Rimuove un eventuale alias/link precedente (ma mai una vera cartella)
            if alias_path.is_symlink() or alias_path.is_file():
                alias_path.unlink()
            script = [
                'on run argv',
                'tell application "Finder"',
                'make new alias file to (POSIX file (item 1 of argv) as alias) '
                'at (POSIX file (item 2 of argv) as alias) '
                'with properties {name:(item 3 of argv)}',
                'end tell',
                'end run',
            ]
            cmd = ['osascript']
            for riga in script:
                cmd += ['-e', riga]
            cmd += [str(cartella), str(desktop), nome_alias]
            risultato = subprocess.run(cmd, capture_output=True, text=True)
            if risultato.returncode != 0:
                print(f"   [!] Alias non creato: {risultato.stderr.strip()}")
                return False

        elif system == 'Windows':
            alias_path = desktop / f"{nome_alias}.lnk"
            if alias_path.exists():
                alias_path.unlink()
            # I percorsi passano tramite variabili d'ambiente per evitare
            # problemi di apici/spazi nella riga di comando di PowerShell.
            ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:ALIAS_LNK);"
                  "$s.TargetPath=$env:ALIAS_TGT;$s.Save()")
            env = dict(os.environ, ALIAS_LNK=str(alias_path), ALIAS_TGT=str(cartella))
            risultato = subprocess.run(['powershell', '-NoProfile', '-Command', ps],
                                       env=env, capture_output=True, text=True)
            if risultato.returncode != 0:
                print(f"   [!] Collegamento non creato: {risultato.stderr.strip()}")
                return False

        else:
            alias_path = desktop / nome_alias
            if alias_path.is_symlink() or alias_path.is_file():
                alias_path.unlink()
            alias_path.symlink_to(cartella, target_is_directory=True)

        print(f"   Alias creato sul Desktop: {alias_path.name}")
        return True
    except Exception as e:
        print(f"   [!] Alias non creato: {e}")
        return False


# --- FUNZIONI DI REPORTING ---

def analizza_e_formatta_report(nome_studente: str, output_gemini: str) -> str:
    """Formatta il report individuale applicando la nuova intestazione richiesta."""
    # BUG FIX 1: il controllo era `"ERRORE" in output_gemini`, quindi scattava
    # anche se la parola ERRORE compariva nel testo della correzione.
    # Ora controlliamo solo l'inizio della stringa (i messaggi d'errore interni
    # iniziano tutti con "ERRORE").
    # BUG FIX 2: il messaggio d'errore reale veniva buttato via — ora lo
    # mostriamo nel report e in console, così si capisce la causa.
    if output_gemini.startswith("ERRORE"):
        print(f"   [!] {nome_studente}: {output_gemini}")
        return (
            f"================================================\n"
            f"STUDENTE: {nome_studente}\n"
            f"ERRORE DI ELABORAZIONE — dettaglio:\n"
            f"{output_gemini}\n\n"
        )

    try:
        # Estraiamo la sezione degli errori
        sezione_errori = output_gemini.split('**Errori Segnalati (Rilevanti per A2/B1):**')[1].split('---')[0].strip()

        report = (
            f"================================================\n"
            f"STUDENTE: {nome_studente}\n"
            f"================================================\n"
            f"Bene! Attenzione, però:\n"
            f"{sezione_errori}\n\n"
        )
        return report
    except Exception:
        return f"================================================\nSTUDENTE: {nome_studente}\n(Errore formattazione report)\n\n"

def salva_report_finale(report_errori, destinazioni):
    """Salva il file TXT di riepilogo errori."""
    testo_errori = f"# RIEPILOGO ERRORI ({LIVELLO_L2})\n\n" + "".join(report_errori)

    for cartella in destinazioni:
        if not cartella: continue
        with open(cartella / "RIEPILOGO_ERRORI_FINALE.txt", 'w', encoding='utf-8') as f: f.write(testo_errori)

    if platform.system() == 'Darwin' and destinazioni:
        os.system(f'open "{destinazioni[0] / "RIEPILOGO_ERRORI_FINALE.txt"}"')


# --- FLUSSO PRINCIPALE ---

def esegui_agente():
    # Senza client AI è inutile proseguire: prima usciva con tutti i file
    # marcati "ERRORE DI ELABORAZIONE" senza spiegazione.
    if not client_gemini:
        print("Impossibile procedere: client Gemini non inizializzato (vedi messaggio sopra).")
        return

    if not CARTELLA_DI_LAVORO.exists():
        CARTELLA_DI_LAVORO.mkdir()
        print(f"Creata la cartella {CARTELLA_DI_LAVORO}. Mettici dentro i file e rilancia lo script.")
        return

    destinazioni = [CARTELLA_DI_LAVORO]
    desktop = get_desktop_path()
    if desktop: destinazioni.append(desktop)

    cartella_trascrizioni = CARTELLA_DI_LAVORO / NOME_CARTELLA_TRASCRIZIONI
    trascrizioni_salvate = []
    nomi_trascrizioni_usati = set()

    report_finale_errori = []
    elaborati = []

    print(f"--- Scansione in corso: {CARTELLA_DI_LAVORO} ---")

    # Snapshot ordinato: la cartella delle trascrizioni viene creata durante
    # il ciclo e non deve essere scansionata. Le sottocartelle sono ignorate.
    for file_path in sorted(p for p in CARTELLA_DI_LAVORO.iterdir() if p.is_file()):
        if file_path.name.startswith('RIEPILOGO') or file_path.name.startswith('.'): continue

        ext = file_path.suffix.lower()
        risultato_ai = None
        tipo = ""

        # 1. Testo / Documenti
        if ext == '.docx':
            risultato_ai = chiama_api_correzione(leggi_file_word(file_path), False)
            tipo = "Word"
        elif ext == '.pdf':
            risultato_ai = chiama_api_correzione(leggi_file_pdf(file_path), False)
            tipo = "PDF"
        elif ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                risultato_ai = chiama_api_correzione(f.read(), False)
            tipo = "Testo"

        # 2. Audio / Video
        elif ext in ESTENSIONI_AUDIO:
            trascrizione = chiama_api_trascrizione(file_path)
            # NOVITÀ: un file di trascrizione per ciascun file audio
            salvata = salva_trascrizione(file_path, trascrizione, cartella_trascrizioni, nomi_trascrizioni_usati)
            if salvata:
                trascrizioni_salvate.append(salvata)
            risultato_ai = chiama_api_correzione(trascrizione, True)
            tipo = "Audio/Video"

        # 3. Immagini (NOVITÀ)
        elif ext in ['.png', '.jpg', '.jpeg', '.webp']:
            risultato_ai = chiama_api_visione(file_path)
            tipo = "Immagine"

        if risultato_ai:
            report_finale_errori.append(analizza_e_formatta_report(file_path.stem, risultato_ai))
            elaborati.append(f"{file_path.name} ({tipo})")

    if elaborati:
        salva_report_finale(report_finale_errori, destinazioni)

        # NOVITÀ: alias sul Desktop alla cartella con le trascrizioni
        alias_creato = False
        if trascrizioni_salvate:
            alias_creato = crea_alias_cartella(cartella_trascrizioni, desktop, NOME_ALIAS_TRASCRIZIONI)

        print("\nProcesso completato.")
        notifica = Notify()
        notifica.title = "Agente AI L2"
        messaggio = f"Processati {len(elaborati)} file. Report pronti."
        if trascrizioni_salvate:
            messaggio += f" {len(trascrizioni_salvate)} trascrizioni salvate"
            messaggio += " (alias sul Desktop)." if alias_creato else "."
        notifica.message = messaggio
        notifica.send()
    else:
        print("Nessun file supportato trovato.")

if __name__ == "__main__":
    esegui_agente()
