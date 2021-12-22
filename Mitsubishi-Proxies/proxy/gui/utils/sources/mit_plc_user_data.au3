Func plc_user_data()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	  Local $aPos = WinGetPos($subwd)
	  Local $x = $aPos[0] + 7 + 241
	  Local $y = $aPos[1] + 523 + 31
	  MouseClick("left",$x,$y,2,2)
   EndIf

EndFunc

plc_user_data()