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

read_from_plc()
