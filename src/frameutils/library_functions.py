#Injecting this as lua code is a hack, it ideally would be handled on the frame itself internal to the built-in print() function
library_print_long = """
local mtu = frame.bluetooth.max_length()
function prntLng(stringToPrint)
	local len = string.len(stringToPrint)
	if len <= mtu - 3 then
		print(stringToPrint)
		return
	end
	local i = 1
	local chunkIndex = 0
	while i <= len do
		local j = i + mtu - 4
		if j > len then
			j = len
		end
		local chunk = string.sub(stringToPrint, i, j)
		print("\\10"..chunk)
		chunkIndex = chunkIndex + 1
		i = j + 1
	end
	print("\\11"..chunkIndex)
end
"""