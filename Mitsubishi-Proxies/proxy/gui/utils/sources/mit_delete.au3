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

delete()