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

format_plc_memory()