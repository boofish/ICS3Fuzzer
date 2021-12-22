Func remote_operate()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 52
	  Local $y = $aPos[1] + 523 + 36
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

remote_operate()