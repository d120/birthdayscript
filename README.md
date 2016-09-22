# Birthdayscript 

Um das Skript zu starten muss die config.default in config umbenannt werden.

Der Aufruf ist dann python3 birthday.py [OPTIONS]

In der Datei mail_template.txt wird der Text für das Anschreiben konfiguriert. 
Hierbei werden die Wörter RECiPIENT durch den Adressaten der E-Mail und
BIRTHDAYKID durch den Geburtstagshabenden ersetzt.

```
supported commands:
  -n    dry-run (list mails to be sent)
  -s    really send the mails listed by dry-run
  -l    list all birthdays in upcoming order
        options:
          -S json|ascii|html
```


