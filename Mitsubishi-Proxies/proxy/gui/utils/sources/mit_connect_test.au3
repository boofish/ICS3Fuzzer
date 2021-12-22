#cs ----------------------------------------------------------------------------

 AutoIt Version: 3.3.14.5
 Author:         myName

 Script Function:
	Template AutoIt script.

#ce ----------------------------------------------------------------------------

#include <Constants.au3>

Func connect_test()

   WinActivate("MELSOFT Series GX Works2 C:\Users\xxx\Desktop\Mitsubishi\test.gxw - [[PRG]Write MAIN 1 Step]")
   Local $windw = WinWaitActive("[CLASS:GXW2FrameWnd;INSTANCE:1]","",2)
   If $windw Then
	  Local $aPos = WinGetPos($windw)
	  ;MsgBox(($MB_SYSTEMMODAL,"box" , "posi:x=" & $aPos[0] & ",y=" & $aPos[1]))
	  Local $x = $aPos[0] + 55
	  Local $y = $aPos[1] + 430 + 156

	 ; WinWaitActive("[CLASS:XTPShortcutBar;INSTANCE:1]","",1)
	  ;MsgBox($MB_SYSTEMMODAL,"box" , "posi:x=" & $aPos[0] & ",y=" & $aPos[1])

	  MouseClick("left",$x,$y,2,0)

	  $x = $aPos[0] + 1 + 77
	  $y = $aPos[1] + 253 + 35
	 ; WinWaitActive("[CLASS:SysTreeView32;INSTANCE:5]","",1)
	  MouseClick("left",$x,$y,2,0)


	  WinWaitActive("Transfer Setup Connection1","",2)
	  send("!T")
   ;Sleep(500)


   ;WinWaitActive("MELSOFT Application")
   ;send("{ENTER}")
   ;Sleep(500)

   ;WinWaitActive("Transfer Setup Connection1")
   ;send("{ENTER}")
   EndIf

EndFunc

connect_test()