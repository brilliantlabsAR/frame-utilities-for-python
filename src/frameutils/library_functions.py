#Injecting this as lua code is a hack, it ideally would be handled on the frame itself internal to the built-in print() function
library_print_long = """
function prntLng(stringToPrint)
	local mtu = frame.bluetooth.max_length()
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
		print("\\010"..chunk)
		chunkIndex = chunkIndex + 1
		i = j + 1
	end
	print("\\011"..chunkIndex)
end
function sendPartial(dataToSend, max_size)
	local len = string.len(dataToSend)
	local i = 1
	local chunkIndex = 0
	while i <= len do
		local j = i + max_size - 4
		if j > len then
			j = len
		end
		local chunk = string.sub(dataToSend, i, j)
		frame.bluetooth.send("\\001"..chunk)
		chunkIndex = chunkIndex + 1
		i = j + 1
		if len > 1000 then
			frame.sleep(0.05)
		end
	end
	return chunkIndex
end
function printCompleteFile(filename)
	local mtu = frame.bluetooth.max_length()
	local f = frame.file.open(filename, "read")
	local chunkIndex = 0
	local chunk = ""
	while true do
		local new_chunk = f:read()
		if new_chunk == nil then
			if string.len(chunk) > 0 then
				chunkIndex = chunkIndex + sendPartial(chunk, mtu)
				break
			end
			break
		end
		if string.len(new_chunk) == 512 then
			chunk = chunk .. new_chunk
		else
			chunk = chunk .. new_chunk .. "\\n"
		end
		
		while string.len(chunk) > mtu - 4 do
			local chunk_to_send = string.sub(chunk, 1, mtu - 4)
			chunkIndex = chunkIndex + 1
			chunk = string.sub(chunk, mtu - 3)
			frame.bluetooth.send("\\001"..chunk_to_send)
			frame.sleep(0.05)
		end
	end
	frame.bluetooth.send("\\002"..chunkIndex)
	f:close()
end
"""