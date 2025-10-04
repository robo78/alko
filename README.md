# Dzienniczek Głodów Alkoholowych

Jest to aplikacja desktopowa z interfejsem graficznym (GUI) stworzona w Pythonie, służąca jako osobisty dziennik do monitorowania i analizowania głodów alkoholowych. Aplikacja pomaga użytkownikom w śledzeniu ich postępów w walce z nałogiem poprzez zapisywanie i analizowanie danych dotyczących głodów.

## Funkcje

- **Dziennik Wpisów**: Umożliwia użytkownikom dodawanie nowych wpisów o głodach, w tym:
  - Data i godzina wystąpienia głodu (zapisywane automatycznie).
  - Intensywność głodu na skali 1-10.
  - Wybór objawów/wyzwalaczy z predefiniowanej listy.
  - Opis sposobu radzenia sobie z głodem.
  - Zaznaczenie, czy doszło do spożycia alkoholu.
- **Historia Wpisów**: Wszystkie wpisy są wyświetlane w przejrzystej tabeli, co pozwala na łatwe przeglądanie historii.
- **Analiza i Podsumowanie**: Dedykowana zakładka "Analiza" automatycznie generuje:
  - **Statystyki**: Całkowita liczba wpisów, średnia intensywność głodów, najczęstszy objaw/wyzwalacz oraz najczęściej stosowany sposób radzenia sobie.
  - **Wykres**: Graficzna wizualizacja intensywności głodów w czasie, co ułatwia identyfikację trendów.
- **Ustawienia i Powiadomienia E-mail**:
  - **Konfiguracja SMTP**: Użytkownicy mogą skonfigurować własne dane serwera SMTP, aby otrzymywać powiadomienia e-mail.
  - **Powiadomienia Codzienne**: Możliwość włączenia codziennych przypomnień e-mail o określonej godzinie, aby nie zapomnieć o uzupełnieniu dziennika.
  - **Test E-mail**: Funkcja wysyłania testowego e-maila w celu weryfikacji poprawności ustawień.

## Struktura Projektu

Projekt jest podzielony na kilka modułów, co zapewnia czytelność i łatwość w zarządzaniu kodem:

- `main.py`: Główny plik aplikacji. Odpowiada za stworzenie interfejsu graficznego (GUI) przy użyciu `tkinter`, zarządzanie zakładkami oraz integrację wszystkich pozostałych modułów.
- `data_manager.py`: Zarządza operacjami na danych. Odpowiada za zapisywanie nowych wpisów do pliku `cravings.csv` oraz ich odczytywanie.
- `analysis.py`: Zawiera logikę analityczną. Oblicza statystyki podsumowujące i generuje wykres intensywności głodów przy użyciu biblioteki `matplotlib`.
- `symptoms.py`: Przechowuje predefiniowaną listę objawów i wyzwalaczy głodu alkoholowego, która jest wykorzystywana w formularzu wpisu.
- `settings_manager.py`: Obsługuje ustawienia aplikacji. Zapisuje i odczytuje konfigurację (np. dane SMTP) z pliku `settings.json`.
- `email_notifier.py`: Odpowiada za wysyłanie wiadomości e-mail przy użyciu `smtplib` na podstawie konfiguracji z menedżera ustawień.
- `reminder_scheduler.py`: Implementuje harmonogram powiadomień. Używa bibliotek `schedule` i `threading` do uruchamiania wysyłki e-maili w tle, bez blokowania interfejsu użytkownika.
- `requirements.txt`: Plik zawierający listę wszystkich zewnętrznych bibliotek Pythona potrzebnych do uruchomienia aplikacji.
- `cravings.csv`: Plik, w którym przechowywane są wszystkie wpisy z dziennika.
- `settings.json`: Plik konfiguracyjny dla ustawień aplikacji (tworzony automatycznie).

## Instalacja i Uruchomienie

Aby uruchomić aplikację, postępuj zgodnie z poniższymi krokami:

**1. Wymagania wstępne:**
   - Upewnij się, że masz zainstalowanego Pythona w wersji 3.6 lub nowszej.

**2. Klonowanie repozytorium (opcjonalnie):**
   ```bash
   git clone <adres-repozytorium>
   cd <nazwa-folderu-repozytorium>
   ```

**3. Instalacja zależności:**
   Otwórz terminal lub wiersz poleceń w głównym folderze projektu i zainstaluj wymagane biblioteki za pomocą poniższej komendy:
   ```bash
   pip install -r requirements.txt
   ```

**4. Uruchomienie aplikacji:**
   Po pomyślnej instalacji zależności, uruchom aplikację, wykonując poniższą komendę:
   ```bash
   python3 main.py
   ```

Po wykonaniu tej komendy, główne okno aplikacji powinno pojawić się na ekranie.