Func read_from_plc()
   WinActivate("MELSOFT Series GX Works2 C:\Users\xxx\Desktop\Mitsubishi\test.gxw - [[PRG]Write MAIN 1 Step]")
   Local $windw = WinWaitActive("MELSOFT Series GX Works2 C:\Users\xxx\Desktop\Mitsubishi\test.gxw - [[PRG]Write MAIN 1 Step]","",4)
   Local $aPos = WinGetPos($windw)
   ;If $aPos Then
   Local $x = $aPos[0] + 330
   Local $y = $aPos[1] + 14 + 28
   MouseClick("left",$x,$y,1,3)
   send("{ENTER}")
   Send("{DOWN}")
   send("{ENTER}")
   ;EndIf

EndFunc



Func arrange_plc()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 616
	  Local $y = $aPos[1] + 523 + 30
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

Func write_title()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 335
	  Local $y = $aPos[1] + 523 + 45
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

Func set_clock()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 148
	  Local $y = $aPos[1] + 523 + 45
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

Func delete()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 17 + 444
	  Local $y = $aPos[1] + 57 + 33
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

Func format_plc_memory()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 429
	  Local $y = $aPos[1] + 523 + 45
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

Func clear_plc_memory()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 535
	  Local $y = $aPos[1] + 523 + 45
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc




read_from_plc()
clear_plc_memory()


;arrange_plc()