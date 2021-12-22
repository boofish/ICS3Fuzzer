Func format_plc_memory()
   WinActivate("Online Data Operation")
   Local $subwd = WinWaitActive("Online Data Operation","",3)
   If $subwd Then
	   ControlClick($subwd, "Close", "Button21")
   EndIf

EndFunc

format_plc_memory()