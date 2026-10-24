DraveDice v0.2
==============

Een dobbelsteen-roller voor D&D en andere tafelspellen. Lokaal, offline,
gratis (met donatie). Grote, goed leesbare cijfers.

Starten
-------
- Dubbelklik op run.bat. De eerste keer installeert hij zichzelf; daarna
  start de app meteen.
- Werkt de eerste keer niet? Draai start-debug.bat (toont de fout) of
  herstel.bat (installeert opnieuw).

Gebruik
-------
- Klik op een dobbelsteen (d4 t/m d100) om er meteen een te gooien.
- De modifier (- / +) wordt bij die worp opgeteld.
- Modus Voordeel/Nadeel geldt voor de d20 (gooit twee keer, neemt de
  hoogste resp. laagste).
- Eigen worp: typ bijv. 2d6+3, 1d20-1 of 1d8+1d4+2 en klik Gooi (of Enter).
- Het grote getal is het totaal; daaronder elke worp apart. Natuurlijke 20
  op een losse d20 = KRITIEK, natuurlijke 1 = misser.
- Onder Geschiedenis staan je laatste worpen.

Een .exe maken (optioneel)
--------------------------
- Draai eerst run.bat (zodat de .venv bestaat), daarna bouw-exe.bat.
- Resultaat: dist\DraveDice.exe (een enkel bestand).

NIEUW in v0.2
-------------
- De modifier heeft nu duidelijke - / + knoppen (de oude spinbox-pijltjes
  reageerden niet door de stijl).

Contact / donatie
-----------------
service@dravenlock.nl - paypal.me/roger076
