# Dzienniczek Głodów Alkoholowych

Jest to aplikacja desktopowa z interfejsem graficznym (GUI) stworzona w Pythonie, służąca jako osobisty dziennik do monitorowania i analizowania głodów alkoholowych. Aplikacja została zaprojektowana wokół **wizualnego kalendarza**, który pozwala na szybką identyfikację wzorców i częstotliwości występowania poszczególnych objawów głodu.

## Główne Funkcje

- **Kalendarz Głodów**: Główny ekran aplikacji to interaktywny kalendarz miesięczny.
  - **Wiersze** reprezentują predefiniowane objawy głodu (np. "Potrzeba napicia się", "Sny alkoholowe").
  - **Kolumny** reprezentują dni miesiąca.
  - Komórki w siatce są **automatycznie podświetlane**, jeśli dany objaw został zarejestrowany danego dnia, co daje natychmiastowy wgląd w Twoje wzorce.
- **Dodawanie Wpisów**: Prosty formularz w nowym oknie pozwala na szybkie dodawanie wpisów, w tym:
  - Intensywność głodu (1-10).
  - Wybór jednego lub więcej objawów z listy.
  - Opis zastosowanego sposobu radzenia sobie.
  - Zaznaczenie, czy doszło do spożycia alkoholu.
- **Zaawansowana Analiza (Streamlit)**: Dedykowana zakładka "Analiza" uruchamia zewnętrzny, interaktywny panel analityczny.
  - Panel jest zbudowany przy użyciu **Streamlit** i otwiera się w przeglądarce internetowej.
  - Oferuje szczegółowe wykresy, statystyki i tabele, pozwalając na głębszą analizę danych z dzienniczka.
- **Ustawienia i Powiadomienia E-mail**:
  - Możliwość skonfigurowania własnych danych serwera SMTP do wysyłki e-maili.
  - Opcja włączenia codziennych przypomnień e-mail o stałej porze.

## Struktura Projektu

- `main.py`: Główny plik aplikacji. Odpowiada za stworzenie interfejsu graficznego (GUI) z **kalendarzem głodów**, zarządzanie zakładkami, obsługę dodawania wpisów oraz uruchamianie panelu Streamlit.
- `viewer.py`: Skrypt aplikacji **Streamlit**. Odpowiada za wczytanie danych z `cravings.csv` i wygenerowanie interaktywnego panelu analitycznego w przeglądarce.
- `data_manager.py`: Zarządza operacjami na danych (zapis i odczyt z pliku `cravings.csv`).
- `symptoms.py`: Przechowuje predefiniowaną listę objawów głodu alkoholowego.
- `settings_manager.py`: Obsługuje ustawienia aplikacji (zapis i odczyt z pliku `settings.json`).
- `email_notifier.py`: Odpowiada za wysyłanie wiadomości e-mail.
- `reminder_scheduler.py`: Implementuje harmonogram powiadomień e-mail w osobnym wątku.
- `requirements.txt`: Plik zawierający listę wszystkich bibliotek Pythona potrzebnych do uruchomienia aplikacji (`tkinter`, `pandas`, `streamlit` itp.).
- `cravings.csv`: Plik, w którym przechowywane są wszystkie wpisy z dziennika.
- `settings.json`: Plik konfiguracyjny (tworzony automatycznie).
- `.gitignore`: Plik instruujący system kontroli wersji, aby ignorował pliki lokalne, takie jak `cravings.csv`, `settings.json` i `__pycache__`.

## Instalacja i Uruchomienie

**1. Wymagania wstępne:**
   - Upewnij się, że masz zainstalowanego Pythona w wersji 3.6 lub nowszej.

**2. Klonowanie repozytorium (opcjonalnie):**
   ```bash
   git clone <adres-repozytorium>
   cd <nazwa-folderu-repozytorium>
   ```

**3. Instalacja zależności:**
   Otwórz terminal lub wiersz poleceń w głównym folderze projektu i zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```

**4. Uruchomienie aplikacji:**
   Uruchom główną aplikację z interfejsem kalendarza:
   ```bash
   python3 main.py
   ```

**5. Uruchomienie panelu analitycznego:**
   W głównej aplikacji przejdź do zakładki **"Analiza"** i kliknij przycisk **"Uruchom Panel Analizy (Streamlit)"**. Spowoduje to otwarcie nowej karty w Twojej domyślnej przeglądarce z interaktywnym panelem.

   Alternatywnie, możesz uruchomić panel analityczny bezpośrednio z terminala:
   ```bash
   streamlit run viewer.py
   ```