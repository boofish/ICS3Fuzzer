#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         fdl

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

#include <Constants.au3>

Func launch()
   Local $iPID = Run("C:\Program Files (x86)\MELSOFT\GPPW2\GD2.EXE C:\Users\xxx\Desktop\Mitsubishi\test.gxw")
   ;Sleep(1500)
   WinWaitActive("MELSOFT Series GX Works2 C:\Users\xxx\Desktop\Mitsubishi\test.gxw - [[PRG]Write MAIN 1 Step]","",1)
EndFunc

launch()